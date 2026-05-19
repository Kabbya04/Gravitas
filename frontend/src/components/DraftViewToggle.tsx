export type DraftViewMode = "preview" | "edit";

type DraftViewToggleProps = {
  mode: DraftViewMode;
  disabled?: boolean;
  onChange: (mode: DraftViewMode) => void;
};

export function DraftViewToggle({
  mode,
  disabled = false,
  onChange,
}: DraftViewToggleProps) {
  const base =
    "rounded-md px-3 py-1.5 text-xs font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-zinc-900";
  const active = "bg-white text-zinc-900 shadow-sm";
  const inactive = "text-zinc-600 hover:text-zinc-900";

  return (
    <div
      className="inline-flex rounded-lg border border-zinc-200 bg-zinc-50 p-0.5"
      role="group"
      aria-label="Draft view mode"
    >
      <button
        type="button"
        disabled={disabled}
        aria-pressed={mode === "preview"}
        onClick={() => onChange("preview")}
        className={`${base} ${mode === "preview" ? active : inactive} disabled:cursor-not-allowed disabled:opacity-50`}
      >
        Preview
      </button>
      <button
        type="button"
        disabled={disabled}
        aria-pressed={mode === "edit"}
        onClick={() => onChange("edit")}
        className={`${base} ${mode === "edit" ? active : inactive} disabled:cursor-not-allowed disabled:opacity-50`}
      >
        Edit markdown
      </button>
    </div>
  );
}
