import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
  type DocumentSummary,
} from "@/lib/api";

export function HomePage() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DocumentSummary | null>(
    null,
  );

  const refresh = useCallback(() => {
    setErr(null);
    return listDocuments()
      .then(setDocs)
      .catch((e: Error) => {
        setErr(e.message);
      });
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    setErr(null);
    try {
      for (const f of Array.from(files)) {
        await uploadDocument(f);
      }
      await refresh();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const executeDelete = async () => {
    const d = pendingDelete;
    if (!d) return;
    setDeletingId(d.id);
    setErr(null);
    try {
      await deleteDocument(d.id);
      setPendingDelete(null);
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Delete failed");
      setPendingDelete(null);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-8">
      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this document?"
        description={
          pendingDelete ? (
            <>
              <span className="font-medium text-zinc-900">
                &ldquo;{pendingDelete.filename}&rdquo;
              </span>{" "}
              will be removed permanently, including stored drafts and the
              search index. This cannot be undone.
            </>
          ) : null
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        destructive
        pending={deletingId !== null}
        onClose={() => {
          if (deletingId !== null) return;
          setPendingDelete(null);
        }}
        onConfirm={() => void executeDelete()}
      />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Documents
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600">
          Upload PDFs or office files. Text is extracted and indexed for grounded
          drafting with citations on each document page.
        </p>
      </div>

      <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-white px-6 py-12 text-center shadow-sm transition hover:border-zinc-400">
        <input
          type="file"
          className="hidden"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.webp,.docx"
          disabled={busy}
          onChange={(e) => void onFiles(e.target.files)}
        />
        <div className="text-sm font-medium text-zinc-800">
          {busy ? "Uploading…" : "Drop files or click to upload"}
        </div>
        <div className="mt-1 text-xs text-zinc-500">PDF, images, DOCX</div>
      </label>

      {err ? (
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800"
          role="alert"
        >
          {err}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 text-xs font-semibold uppercase tracking-wide text-zinc-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {docs.map((d) => (
              <tr key={d.id} className="hover:bg-zinc-50/80">
                <td className="px-4 py-3 font-medium text-zinc-900">{d.filename}</td>
                <td className="px-4 py-3">
                  <span
                    className={
                      d.status === "ready"
                        ? "text-emerald-700"
                        : d.status === "failed"
                          ? "text-red-600"
                          : "text-amber-700"
                    }
                  >
                    {d.status}
                  </span>
                  {d.error_message ? (
                    <div
                      className="mt-1 max-w-md truncate text-xs text-zinc-500"
                      title={d.error_message}
                    >
                      {d.error_message}
                    </div>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex flex-wrap items-center justify-end gap-3">
                    <Link
                      className="font-medium text-zinc-900 underline-offset-2 hover:underline"
                      to={`/documents/${d.id}`}
                    >
                      Open
                    </Link>
                    <button
                      type="button"
                      disabled={deletingId !== null || busy}
                      onClick={() => setPendingDelete(d)}
                      className="font-medium text-red-700 underline-offset-2 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {deletingId === d.id ? "Deleting…" : "Delete"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!docs.length ? (
              <tr>
                <td className="px-4 py-6 text-zinc-500" colSpan={3}>
                  No documents yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
