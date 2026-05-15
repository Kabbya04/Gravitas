# Gravitas platform: assessment scope and build plan

## Source of truth: assessment brief

The take-home (`AI Engineer - Assessment.pdf`) defines four core capabilities and explicit deliverables.

**Core capabilities (must ship end-to-end):**

1. **Document processing** — Ingest noisy legal-style inputs (scanned PDFs, low resolution, handwriting-adjacent noise, inconsistent formats). Deliver **extracted text plus structured fields** that need no manual cleanup before retrieval/drafting.
2. **Grounded retrieval** — For a drafting task, **surface relevant passages**, pass them into generation, and make it **possible to inspect which evidence supported which part of the output**. Control unsupported generation.
3. **Draft generation** — Pick one first-pass output type; it must be **relevant, well structured, and grounded** in retrieved evidence (legal correctness is out of scope).
4. **Improvement from operator edits** — **Capture edits**, **extract reusable signal**, and **use it to measurably improve future drafts** — a real loop, not only a side-by-side diff.

**Required submission artifacts (plan the repo layout around these):**

- Source code
- **README** — setup and run
- **Short architecture overview** (e.g. `docs/ARCHITECTURE.md`)
- **Assumptions and tradeoffs** (e.g. `docs/ASSUMPTIONS.md`)
- **Sample inputs and outputs** (e.g. `samples/`)
- **Evaluation approach and results** (e.g. `docs/EVALUATION.md`)

**In scope:** API + simple UI + tests. **Docker** deferred (local setup only).

**Logistics:** deadline **Friday May 15, 2026** EOD local; push to GitHub; invite reviewers; email submission — document in README.

---

## Folder layout

| Area | Path |
|------|------|
| Frontend | `frontend/` |
| Backend | `backend/` |
| Root | `README.md`, `plan.md`, `DIRECTORY_STRUCTURE.md`, `environment.yml` (Conda env **gravitas**, Python 3.11) |

---

## Draft output type

**Case fact summary** (timeline + issues + key entities) with **citation tags** tied to evidence `E#` and chunk IDs.

---

## Storage

- **SQLite** — Documents, chunks, drafts, operator corrections, provenance.
- **Chroma** — Vector embeddings for chunks; metadata links to SQLite `chunk_id`.

---

## Standard RAG pipeline (13 stages)

1. Load → 2. Parse/extract → 3. Chunk → 4. Persist SQLite → 5. Embed (local) → 6. Chroma upsert → 7. BM25 index → 8. Query embed → 9. Hybrid retrieve → 10. RRF fusion → 11. Context pack `E1…En` → 12. Groq generate → 13. Citation validation (optional repair).

Operator-edit **memory** injects into step 11 as an extra prompt block (retrieved past corrections).

---

## Implementation order

1. Backend skeleton (FastAPI, SQLite, Chroma path, config, prompts from files).
2. Ingestion (PDF native, OCR, MarkItDown when needed).
3. Indexing + hybrid retrieval.
4. Groq drafting + persistence.
5. Frontend (Vite React Tailwind) wired via env `VITE_API_URL`.
6. Edit loop + docs/samples + `pytest` in Conda env `gravitas` (Python 3.11).

See `.cursor/plans/` for the full detailed plan including mermaid diagram and rubric checklist.
