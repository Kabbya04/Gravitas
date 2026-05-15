/**
 * Typed HTTP helpers for the Gravitas FastAPI backend.
 * Configure `VITE_API_URL` in `.env` (see `.env.example`). Never put API keys in the frontend.
 *
 * If `VITE_API_URL` is empty, requests use same-origin paths (e.g. Vite dev proxy to `/api`).
 */

function getBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL;
  if (raw === undefined || raw === null) {
    throw new Error("VITE_API_URL is not defined. Add it to `.env` (see `.env.example`).");
  }
  const t = String(raw).trim();
  if (t === "") return "";
  return t.replace(/\/$/, "");
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      const body = JSON.parse(text) as { detail?: unknown };
      if (body?.detail !== undefined) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* keep raw */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  return parseJson<T>(res);
}

export async function apiPostJson<T, B extends object>(
  path: string,
  body: B,
): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return parseJson<T>(res);
}

export async function apiPostMultipart<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "POST",
    body: formData,
  });
  return parseJson<T>(res);
}

// --- Document / chunk types (supports current backend + flexible fields) ---

export type DocumentSummary = {
  id: string;
  filename: string;
  name?: string | null;
  status: string;
  error_message?: string | null;
};

export type DocumentChunk = {
  id?: string;
  chunk_id?: string | number;
  chunk_index?: number;
  page?: number | null;
  page_start?: number;
  page_end?: number;
  source?: string | null;
  ocr_confidence?: number | null;
  confidence?: number | null;
  snippet?: string | null;
  text?: string | null;
  text_preview?: string | null;
};

export type EvidenceItem = {
  e_label: string;
  chunk_id: string | number;
  text: string;
  page: number | null;
};

export type DraftResponse = {
  draft_id: string;
  /** Primary plain-text draft from some backends */
  content?: string;
  draft?: string;
  draft_text?: string;
  evidence: EvidenceItem[];
  citations_used?: string[];
  citation_issues?: string[];
  draft_json?: Record<string, unknown>;
};

/** Row from `GET /api/documents/:id/drafts` */
export type DraftSummary = {
  draft_id: string;
  query: string;
  created_at: string;
  has_operator_version: boolean;
};

export type CreateDraftBody = {
  query: string;
  use_memory?: boolean;
};

export type SaveOperatorBody = {
  text: string;
};

export type HealthResponse = {
  status?: string;
  [key: string]: unknown;
};

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

/** @deprecated use getHealth */
export const health = getHealth;

export function listDocuments(): Promise<DocumentSummary[]> {
  return apiGet<DocumentSummary[]>("/api/documents");
}

export function uploadDocument(file: File): Promise<DocumentSummary> {
  const fd = new FormData();
  fd.append("file", file);
  return apiPostMultipart<DocumentSummary>("/api/documents", fd);
}

export function getDocument(id: string): Promise<DocumentSummary> {
  return apiGet<DocumentSummary>(`/api/documents/${encodeURIComponent(id)}`);
}

export function getDocumentChunks(id: string): Promise<DocumentChunk[]> {
  return apiGet<DocumentChunk[]>(
    `/api/documents/${encodeURIComponent(id)}/chunks`,
  );
}

/** @deprecated use getDocumentChunks */
export const listChunks = getDocumentChunks;

export function createDraft(
  documentId: string,
  body: CreateDraftBody,
): Promise<DraftResponse> {
  return apiPostJson<DraftResponse, CreateDraftBody>(
    `/api/documents/${encodeURIComponent(documentId)}/draft`,
    body,
  );
}

export function listDocumentDrafts(
  documentId: string,
): Promise<DraftSummary[]> {
  return apiGet<DraftSummary[]>(
    `/api/documents/${encodeURIComponent(documentId)}/drafts`,
  );
}

export function getDraft(draftId: string): Promise<DraftResponse> {
  return apiGet<DraftResponse>(
    `/api/drafts/${encodeURIComponent(draftId)}`,
  );
}

export function saveOperatorDraft(
  draftId: string,
  body: SaveOperatorBody,
): Promise<{ status?: string; [key: string]: unknown }> {
  return apiPostJson(`/api/drafts/${encodeURIComponent(draftId)}/operator`, body);
}

export function draftTextFromResponse(res: DraftResponse): string {
  const c = res.content;
  if (typeof c === "string" && c.length > 0) return c;
  if (typeof res.draft === "string" && res.draft.length > 0) return res.draft;
  if (typeof res.draft_text === "string" && res.draft_text.length > 0) {
    return res.draft_text;
  }
  return "";
}

export function citationsUsedFromResponse(res: DraftResponse): string[] {
  if (Array.isArray(res.citations_used) && res.citations_used.length) {
    return res.citations_used;
  }
  if (Array.isArray(res.citation_issues) && res.citation_issues.length) {
    return res.citation_issues;
  }
  return [];
}

// Legacy names used by earlier UI code
export type ChunkOut = DocumentChunk;
export type EvidenceOut = EvidenceItem;
