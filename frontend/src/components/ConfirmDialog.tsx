import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

export type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Disables actions and shows loading on the confirm control */
  pending?: boolean;
  /** Use destructive styling for the confirm action */
  destructive?: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  pending = false,
  destructive = false,
  onClose,
  onConfirm,
}: ConfirmDialogProps) {
  const titleId = useId();
  const descId = useId();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !pending) {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, pending]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const t = window.setTimeout(() => {
      panelRef.current?.querySelector<HTMLButtonElement>("button[data-autofocus]")?.focus();
    }, 0);
    return () => window.clearTimeout(t);
  }, [open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-[200] flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        aria-label="Dismiss"
        disabled={pending}
        onClick={onClose}
        className="absolute inset-0 bg-zinc-950/40 backdrop-blur-[1px] transition enabled:hover:bg-zinc-950/50 disabled:cursor-not-allowed"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative z-[1] w-full max-w-md rounded-xl border border-zinc-200 bg-white p-5 shadow-xl sm:p-6"
      >
        <h2
          id={titleId}
          className="text-lg font-semibold tracking-tight text-zinc-900"
        >
          {title}
        </h2>
        <div id={descId} className="mt-3 text-sm leading-relaxed text-zinc-600">
          {description}
        </div>
        <div className="mt-6 flex flex-wrap justify-end gap-2 sm:gap-3">
          <button
            type="button"
            data-autofocus
            disabled={pending}
            onClick={onClose}
            className="rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-800 shadow-sm transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            disabled={pending}
            onClick={onConfirm}
            className={
              destructive
                ? "rounded-lg bg-red-700 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-red-800 disabled:cursor-not-allowed disabled:opacity-60"
                : "rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
            }
          >
            {pending ? "Please wait…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
