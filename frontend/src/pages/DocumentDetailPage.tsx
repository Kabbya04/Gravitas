import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DraftMarkdown } from "@/components/DraftMarkdown";
import {
  DraftViewToggle,
  type DraftViewMode,
} from "@/components/DraftViewToggle";
import {
  citationsUsedFromResponse,
  createDraft,
  deleteDocument,
  draftTextFromResponse,
  getDocument,
  getDocumentChunks,
  getDraft,
  listDocumentDrafts,
  saveOperatorDraft,
  type DocumentChunk,
  type DocumentSummary,
  type DraftResponse,
  type DraftSummary,
} from "@/lib/api";

function chunkKey(c: DocumentChunk, index: number): string {
  if (c.id) return c.id;
  const cid = c.chunk_id;
  if (cid !== undefined && cid !== null) return String(cid);
  return `row-${index}`;
}

function chunkPage(c: DocumentChunk): string {
  if (c.page_start !== undefined && c.page_end !== undefined) {
    if (c.page_start === c.page_end) return String(c.page_start);
    return `${c.page_start}–${c.page_end}`;
  }
  const p = c.page;
  if (p === null || p === undefined) return "—";
  return String(p);
}

function chunkSource(c: DocumentChunk): string {
  return String(c.source ?? "—");
}

function chunkConfidence(c: DocumentChunk): string {
  const v = c.ocr_confidence ?? c.confidence;
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toFixed(2);
  return String(v);
}

function chunkSnippet(c: DocumentChunk): string {
  const t = c.text_preview ?? c.snippet ?? c.text;
  if (!t) return "—";
  const s = String(t);
  return s.length > 160 ? `${s.slice(0, 157)}…` : s;
}

function formatDraftSavedAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function queryPreview(q: string, max = 72): string {
  const t = q.trim();
  if (t.length <= max) return t || "—";
  return `${t.slice(0, max - 1)}…`;
}

export function DocumentDetailPage() {
  const { id: rawId } = useParams();
  const navigate = useNavigate();
  const id = rawId ?? "";

  const [doc, setDoc] = useState<DocumentSummary | null>(null);
  const [docErr, setDocErr] = useState<string | null>(null);

  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [chunksErr, setChunksErr] = useState<string | null>(null);
  const [chunksLoading, setChunksLoading] = useState(true);

  const [query, setQuery] = useState(
    "Summarize key facts, timeline, and open issues.",
  );
  const [useMemory, setUseMemory] = useState(false);
  const [draftBusy, setDraftBusy] = useState(false);
  const [draftErr, setDraftErr] = useState<string | null>(null);
  const [draftRes, setDraftRes] = useState<DraftResponse | null>(null);

  const [saveBusy, setSaveBusy] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const [draftList, setDraftList] = useState<DraftSummary[]>([]);
  const [draftListLoading, setDraftListLoading] = useState(false);
  const [draftListErr, setDraftListErr] = useState<string | null>(null);
  const [openDraftBusyId, setOpenDraftBusyId] = useState<string | null>(null);

  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [draftBody, setDraftBody] = useState("");
  const [draftViewMode, setDraftViewMode] = useState<DraftViewMode>("preview");

  const citationLines = useMemo(
    () => (draftRes ? citationsUsedFromResponse(draftRes) : []),
    [draftRes],
  );

  useEffect(() => {
    if (!draftRes) {
      setDraftBody("");
      return;
    }
    setDraftBody(draftTextFromResponse(draftRes));
    setDraftViewMode("preview");
  }, [
    draftRes?.draft_id,
    draftRes?.content,
    draftRes?.draft,
    draftRes?.draft_text,
  ]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setDoc(null);
    setChunks([]);
    setChunksErr(null);

    const poll = async () => {
      try {
        const d = await getDocument(id);
        if (cancelled) return;
        setDoc(d);
        setDocErr(null);
        if (d.status !== "ready") {
          setChunks([]);
          setChunksLoading(false);
          setChunksErr(null);
        }
      } catch (e) {
        if (!cancelled) {
          setDocErr(e instanceof Error ? e.message : "Failed to load document");
        }
      }
    };

    void poll();
    const t = window.setInterval(() => {
      void poll();
    }, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, [id]);

  useEffect(() => {
    if (!id || doc?.status !== "ready") return;
    let cancelled = false;
    setChunksErr(null);
    setChunksLoading(true);
    (async () => {
      try {
        const ch = await getDocumentChunks(id);
        if (!cancelled) setChunks(Array.isArray(ch) ? ch : []);
      } catch (e) {
        if (!cancelled) {
          setChunksErr(
            e instanceof Error ? e.message : "Failed to load chunks",
          );
          setChunks([]);
        }
      } finally {
        if (!cancelled) setChunksLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, doc?.status]);

  const refreshDraftList = useCallback(async () => {
    if (!id || doc?.status !== "ready") {
      setDraftList([]);
      return;
    }
    setDraftListLoading(true);
    setDraftListErr(null);
    try {
      const rows = await listDocumentDrafts(id);
      setDraftList(Array.isArray(rows) ? rows : []);
    } catch (e) {
      setDraftListErr(
        e instanceof Error ? e.message : "Failed to load draft list",
      );
      setDraftList([]);
    } finally {
      setDraftListLoading(false);
    }
  }, [id, doc?.status]);

  useEffect(() => {
    void refreshDraftList();
  }, [refreshDraftList]);

  const onGenerate = async () => {
    if (!id || !query.trim()) return;
    setDraftBusy(true);
    setDraftErr(null);
    setSaveMsg(null);
    try {
      const res = await createDraft(id, {
        query: query.trim(),
        use_memory: useMemory,
      });
      setDraftRes(res);
      void refreshDraftList();
    } catch (e) {
      setDraftErr(e instanceof Error ? e.message : "Draft request failed");
    } finally {
      setDraftBusy(false);
    }
  };

  const onOpenSavedDraft = async (draftId: string) => {
    setDraftListErr(null);
    setOpenDraftBusyId(draftId);
    try {
      const res = await getDraft(draftId);
      setDraftRes(res);
      setDraftErr(null);
    } catch (e) {
      setDraftListErr(
        e instanceof Error ? e.message : "Could not open that draft",
      );
    } finally {
      setOpenDraftBusyId(null);
    }
  };

  const onSaveOperator = async () => {
    if (!draftRes?.draft_id || !draftBody.trim()) return;
    setSaveBusy(true);
    setSaveMsg(null);
    try {
      await saveOperatorDraft(draftRes.draft_id, { text: draftBody });
      setSaveMsg("Operator version saved.");
      const updated = await getDraft(draftRes.draft_id);
      setDraftRes(updated);
      void refreshDraftList();
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaveBusy(false);
    }
  };

  const runDeleteDocument = async () => {
    if (!id) return;
    setDeleteBusy(true);
    setDocErr(null);
    try {
      await deleteDocument(id);
      setDeleteDialogOpen(false);
      navigate("/", { replace: true });
    } catch (e) {
      setDocErr(e instanceof Error ? e.message : "Delete failed");
      setDeleteDialogOpen(false);
    } finally {
      setDeleteBusy(false);
    }
  };

  if (!id) {
    return (
      <p className="text-sm text-zinc-600">
        Missing document id.{" "}
        <Link to="/" className="font-medium text-zinc-900 underline">
          Back
        </Link>
      </p>
    );
  }

  const docTitle = doc?.filename ?? doc?.name ?? id;
  const docReady = doc?.status === "ready";

  return (
    <div className="space-y-8">
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete this document?"
        description={
          <>
            <span className="font-medium text-zinc-900">
              &ldquo;{docTitle}&rdquo;
            </span>{" "}
            will be removed permanently, including stored drafts, uploaded files,
            and the search index. This cannot be undone.
          </>
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        destructive
        pending={deleteBusy}
        onClose={() => {
          if (!deleteBusy) setDeleteDialogOpen(false);
        }}
        onConfirm={() => void runDeleteDocument()}
      />
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <Link
            to="/"
            className="text-xs font-medium text-zinc-500 hover:text-zinc-800"
          >
            ← Documents
          </Link>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
            {docTitle}
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            Status:{" "}
            <span className="font-medium text-zinc-800">{doc?.status ?? "…"}</span>
            {!docReady && doc?.status !== "failed" ? (
              <span className="ml-2 text-xs text-zinc-500">
                Refreshing every 2s until ready…
              </span>
            ) : null}
          </p>
          {docErr && (
            <p className="mt-1 text-sm text-red-600" role="alert">
              {docErr}
            </p>
          )}
        </div>
        <button
          type="button"
          disabled={deleteBusy}
          onClick={() => setDeleteDialogOpen(true)}
          className="shrink-0 rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-800 shadow-sm transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {deleteBusy ? "Deleting…" : "Delete document"}
        </button>
      </div>

      <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-100 px-4 py-3 sm:px-5">
          <h2 className="text-sm font-semibold text-zinc-900">Chunks</h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            Indexed segments used for retrieval and citations.
          </p>
        </div>
        <div className="overflow-x-auto">
          {!docReady ? (
            <p className="px-4 py-6 text-center text-sm text-zinc-500 sm:px-5">
              {doc?.status === "failed"
                ? "Document processing failed; chunks are unavailable."
                : "Processing document… chunks appear when status is ready."}
            </p>
          ) : chunksLoading ? (
            <p className="px-4 py-6 text-center text-sm text-zinc-500 sm:px-5">
              Loading chunks…
            </p>
          ) : chunksErr ? (
            <p className="px-4 py-6 text-center text-sm text-red-600 sm:px-5">
              {chunksErr}
            </p>
          ) : chunks.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-zinc-500 sm:px-5">
              No chunks returned for this document.
            </p>
          ) : (
            <table className="min-w-full text-left text-sm">
              <thead className="bg-zinc-50 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="px-4 py-3 sm:px-5">Page</th>
                  <th className="px-4 py-3 sm:px-5">Source</th>
                  <th className="px-4 py-3 sm:px-5">OCR confidence</th>
                  <th className="px-4 py-3 sm:px-5">Snippet</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {chunks.map((c, idx) => (
                  <tr key={chunkKey(c, idx)} className="hover:bg-zinc-50/80">
                    <td className="whitespace-nowrap px-4 py-3 text-zinc-800 sm:px-5">
                      {chunkPage(c)}
                    </td>
                    <td className="max-w-[10rem] truncate px-4 py-3 text-zinc-700 sm:px-5">
                      {chunkSource(c)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-zinc-700 sm:px-5">
                      {chunkConfidence(c)}
                    </td>
                    <td className="px-4 py-3 text-zinc-600 sm:px-5">
                      {chunkSnippet(c)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-100 px-4 py-3 sm:px-5">
          <h2 className="text-sm font-semibold text-zinc-900">Saved drafts</h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            Each run of Generate stores a draft on the server. Open one to view
            its text, citations, and evidence. If you used{" "}
            <span className="font-medium text-zinc-700">Save operator version</span>
            , the stored text is the edited version.
          </p>
        </div>
        <div className="overflow-x-auto">
          {!docReady ? (
            <p className="px-4 py-6 text-center text-sm text-zinc-500 sm:px-5">
              Drafts are available after the document is ready.
            </p>
          ) : draftListLoading ? (
            <p className="px-4 py-6 text-center text-sm text-zinc-500 sm:px-5">
              Loading drafts…
            </p>
          ) : draftListErr ? (
            <p className="px-4 py-6 text-center text-sm text-red-600 sm:px-5">
              {draftListErr}
            </p>
          ) : draftList.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-zinc-500 sm:px-5">
              No drafts yet. Use{" "}
              <span className="font-medium text-zinc-800">Generate</span> below
              to create the first one.
            </p>
          ) : (
            <table className="min-w-full text-left text-sm">
              <thead className="bg-zinc-50 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="px-4 py-3 sm:px-5">Saved</th>
                  <th className="px-4 py-3 sm:px-5">Query</th>
                  <th className="px-4 py-3 sm:px-5">Status</th>
                  <th className="px-4 py-3 sm:px-5" />
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {draftList.map((row) => {
                  const isOpen = draftRes?.draft_id === row.draft_id;
                  const opening = openDraftBusyId === row.draft_id;
                  return (
                    <tr
                      key={row.draft_id}
                      className={
                        isOpen ? "bg-amber-50/60 hover:bg-amber-50/80" : "hover:bg-zinc-50/80"
                      }
                    >
                      <td className="whitespace-nowrap px-4 py-3 text-zinc-800 sm:px-5">
                        {formatDraftSavedAt(row.created_at)}
                      </td>
                      <td className="max-w-md px-4 py-3 text-zinc-700 sm:px-5">
                        <span title={row.query}>{queryPreview(row.query)}</span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 sm:px-5">
                        {row.has_operator_version ? (
                          <span className="text-emerald-700">Operator saved</span>
                        ) : (
                          <span className="text-zinc-500">Model only</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right sm:px-5">
                        <button
                          type="button"
                          disabled={opening}
                          onClick={() => void onOpenSavedDraft(row.draft_id)}
                          className="font-medium text-zinc-900 underline-offset-2 hover:underline disabled:cursor-wait disabled:opacity-60"
                        >
                          {opening ? "Opening…" : isOpen ? "Reload" : "Open"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section className="space-y-4 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-5">
          <h2 className="text-sm font-semibold text-zinc-900">Drafting</h2>
          <label className="block text-xs font-medium text-zinc-600">
            Query
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              placeholder="e.g. Draft a short factual background citing the contract termination clause…"
              className="mt-1 w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-900 shadow-inner outline-none ring-zinc-900/10 transition focus:border-zinc-400 focus:bg-white focus:ring-2"
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-700">
            <input
              type="checkbox"
              checked={useMemory}
              onChange={(e) => setUseMemory(e.target.checked)}
              className="rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900"
            />
            Use memory
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              disabled={draftBusy || !query.trim() || !docReady}
              onClick={() => void onGenerate()}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {draftBusy ? "Generating…" : "Generate"}
            </button>
            <button
              type="button"
              disabled={
                saveBusy || !draftRes?.draft_id || !draftBody.trim()
              }
              onClick={() => void onSaveOperator()}
              className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 shadow-sm transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saveBusy ? "Saving…" : "Save operator version"}
            </button>
          </div>
          {draftErr && (
            <p className="text-sm text-red-600" role="alert">
              {draftErr}
            </p>
          )}
          {saveMsg && (
            <p className="text-sm text-zinc-600" role="status">
              {saveMsg}
            </p>
          )}

          <div>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Draft
                </h3>
                <p className="mt-1 text-xs text-zinc-500">
                  {draftViewMode === "preview" ? (
                    <>
                      Rendered view for reading. Switch to{" "}
                      <span className="font-medium text-zinc-700">
                        Edit markdown
                      </span>{" "}
                      to change text.
                    </>
                  ) : (
                    <>
                      Edit freely. Keep markers like{" "}
                      <span className="font-mono text-zinc-700">[E1]</span> so the
                      evidence panel stays aligned with your text.
                    </>
                  )}
                </p>
              </div>
              <DraftViewToggle
                mode={draftViewMode}
                disabled={!draftRes}
                onChange={setDraftViewMode}
              />
            </div>
            {draftViewMode === "preview" ? (
              <div
                className="mt-2 min-h-[12rem] w-full overflow-y-auto rounded-lg border border-zinc-200 bg-zinc-50/80 p-4 read-only:opacity-70"
                aria-label="Draft preview"
              >
                {draftRes ? (
                  <DraftMarkdown markdown={draftBody} />
                ) : (
                  <p className="text-sm text-zinc-500">
                    Generate a draft or open a saved one from the list above.
                  </p>
                )}
              </div>
            ) : (
              <textarea
                value={draftBody}
                onChange={(e) => setDraftBody(e.target.value)}
                readOnly={!draftRes}
                spellCheck
                rows={16}
                placeholder={
                  draftRes
                    ? ""
                    : "Generate a draft or open a saved one from the list above."
                }
                className="mt-2 min-h-[12rem] w-full resize-y rounded-lg border border-zinc-200 bg-zinc-50/80 p-4 font-mono text-sm leading-relaxed text-zinc-800 outline-none ring-zinc-900/10 transition read-only:cursor-not-allowed read-only:opacity-70 focus:border-zinc-400 focus:bg-white focus:ring-2"
              />
            )}
          </div>

          {draftRes && citationLines.length > 0 && (
            <p className="text-xs text-zinc-500">
              Citations / checks:{" "}
              <span className="font-mono text-zinc-700">
                {citationLines.join("; ")}
              </span>
            </p>
          )}
        </section>

        <aside className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-5">
          <h2 className="text-sm font-semibold text-zinc-900">Evidence</h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            Spans retrieved for this draft. Match labels{" "}
            <span className="font-mono">[E#]</span> in your draft text.
          </p>
          <div className="mt-4 max-h-[70vh] space-y-3 overflow-y-auto pr-1">
            {!draftRes?.evidence?.length ? (
              <p className="text-sm text-zinc-500">
                Generate a new draft or open a saved one to see evidence spans.
              </p>
            ) : (
              draftRes.evidence.map((ev, evIdx) => {
                return (
                  <div
                    key={`${ev.e_label}-${evIdx}`}
                    className="rounded-lg border border-zinc-100 bg-zinc-50/80 p-3 text-sm transition"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-zinc-800">
                        {ev.e_label}
                      </span>
                      <span className="text-xs text-zinc-500">
                        p. {ev.page ?? "—"} · chunk {ev.chunk_id}
                      </span>
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-zinc-700">
                      {ev.text}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
