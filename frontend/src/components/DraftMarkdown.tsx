import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const CITATION_RE = /(\[E\d+\])/g;

function renderCitationSpans(text: string): ReactNode[] {
  const parts = text.split(CITATION_RE);
  return parts.map((part, i) =>
    /^\[E\d+\]$/.test(part) ? (
      <span
        key={`${part}-${i}`}
        className="mx-0.5 inline rounded bg-amber-100 px-1 py-0.5 font-mono text-[0.7rem] font-semibold text-amber-900"
      >
        {part}
      </span>
    ) : (
      part
    ),
  );
}

function withCitations(children: ReactNode): ReactNode {
  if (typeof children === "string") {
    return <>{renderCitationSpans(children)}</>;
  }
  if (Array.isArray(children)) {
    return children.map((child, i) => (
      <span key={i}>{withCitations(child)}</span>
    ));
  }
  return children;
}

type BlockProps = { children?: ReactNode };

const markdownComponents = {
  h1: ({ children }: BlockProps) => (
    <h1 className="text-lg font-semibold tracking-tight text-zinc-900">
      {withCitations(children)}
    </h1>
  ),
  h2: ({ children }: BlockProps) => (
    <h2 className="mt-4 text-base font-semibold text-zinc-900">
      {withCitations(children)}
    </h2>
  ),
  p: ({ children }: BlockProps) => (
    <p className="text-sm leading-relaxed text-zinc-800">
      {withCitations(children)}
    </p>
  ),
  ul: ({ children }: BlockProps) => (
    <ul className="list-disc space-y-2 pl-5 text-sm text-zinc-800">{children}</ul>
  ),
  ol: ({ children }: BlockProps) => (
    <ol className="list-decimal space-y-2 pl-5 text-sm text-zinc-800">{children}</ol>
  ),
  li: ({ children }: BlockProps) => (
    <li className="leading-relaxed">{withCitations(children)}</li>
  ),
  strong: ({ children }: BlockProps) => (
    <strong className="font-semibold text-zinc-900">{withCitations(children)}</strong>
  ),
  em: ({ children }: BlockProps) => (
    <em className="italic text-zinc-800">{withCitations(children)}</em>
  ),
};

type DraftMarkdownProps = {
  markdown: string;
  className?: string;
};

export function DraftMarkdown({ markdown, className = "" }: DraftMarkdownProps) {
  if (!markdown.trim()) {
    return (
      <p className="text-sm text-zinc-500">No draft content to preview.</p>
    );
  }

  const rootClass = ["space-y-3", className].filter(Boolean).join(" ");

  return (
    <article className={rootClass}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {markdown}
      </ReactMarkdown>
    </article>
  );
}
