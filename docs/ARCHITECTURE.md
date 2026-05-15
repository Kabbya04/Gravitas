# Architecture

This document describes how **Gravitas** is put together: major components, how data moves through the system, and how **retrieval-augmented generation (RAG)** is implemented end-to-end. For a quick folder map, see [DIRECTORY_STRUCTURE.md](../DIRECTORY_STRUCTURE.md).

## Goals

The service ingests **noisy legal-style** files (PDFs, scans, office formats), turns them into **searchable chunks** with provenance, retrieves **only relevant passages** for a drafting task, and asks **Groq** to produce a **grounded** first-pass summary whose claims can be traced to numbered evidence. A separate **operator edit** path captures corrections and feeds a lightweight **memory** block into later prompts so drafts can improve without fine-tuning the base model.

## High-level system architecture

![High-level system architecture for Gravitas](diagrams/architecture.svg)

Source (edit and regenerate SVG as needed): [diagrams/architecture.mmd](diagrams/architecture.mmd). From `docs/diagrams/`, e.g. `npx --yes @mermaid-js/mermaid-cli@11.4.0 -i architecture.mmd -o architecture.svg -w 2200 -H 950 -s 1 -b white -q`.

**Groq:** OpenAI-compatible client with `base_url=https://api.groq.com/openai/v1` and `GROQ_API_KEY` ([Groq overview](https://console.groq.com/docs/overview)); the browser never sees API keys. Model id defaults in `config.yaml` and can be overridden with `GROQ_MODEL` in `.env`.

**Reading the diagram:** **POST upload** flows through ingestion into **SQLite** (canonical text and files), **Chroma** (dense vectors), and **BM25** corpus texts. **DELETE document** tears down the same stores for that id (plus cascaded SQL rows) without going through the ingest path. At draft time, **Hybrid** / **Pack** / **Groq** / **Parse** and the **Mine** → **Mem** loop feeding back into **Pack** behave as before.

## Major components

| Layer | Role | Primary code |
|--------|------|----------------|
| **API** | HTTP routes: multipart upload, document CRUD (including **delete**), chunk listing, draft create/list/get, operator-save. | [`backend/app/main.py`](../backend/app/main.py), [`backend/app/api/routers/`](../backend/app/api/routers/) |
| **Core config** | `.env` secrets, `config.yaml` tunables, Jinja-rendered prompts from YAML files. | [`backend/app/core/`](../backend/app/core/), [`backend/config.yaml`](../backend/config.yaml), [`backend/prompts/drafting.yaml`](../backend/prompts/drafting.yaml) |
| **Persistence** | SQLAlchemy models and SQLite session; files under `backend/data/`. | [`backend/app/db/`](../backend/app/db/) |
| **Ingestion** | Format routing, PDF native vs OCR, optional MarkItDown, chunking with overlap; **`purge_document`** for full teardown on delete. | [`backend/app/ingestion/`](../backend/app/ingestion/) |
| **RAG** | Embeddings, Chroma client, BM25 over in-memory tokenized corpus, RRF fusion, evidence packing. | [`backend/app/rag/`](../backend/app/rag/) |
| **LLM** | Groq via OpenAI-compatible client, JSON draft shape, citation validation and optional repair. | [`backend/app/llm/`](../backend/app/llm/) |
| **Learning** | Diff-based correction snippets, embeddings for memory retrieval, prompt injection. | [`backend/app/learning/edits.py`](../backend/app/learning/edits.py) |
| **Frontend** | React + Vite + TypeScript + Tailwind; upload, **delete** (modal confirm), chunk view, **saved drafts** list + reload, editable draft, evidence panel, operator save. | [`frontend/src/`](../frontend/src/) |

## End-to-end data flow (narrative)

1. A document is **uploaded** and stored on disk; a row is created in SQLite with `pending` status.
2. A **background task** runs ingestion: extract text (native PDF, **Tesseract** on low-text pages, or **MarkItDown** for office types), **chunk** with configurable size and overlap, then write **Chunk** rows.
3. Each chunk is **embedded** locally (**sentence-transformers** / PyTorch) and **upserted** into **Chroma** with metadata linking back to SQLite `chunk_id` and `document_id`.
4. When the user requests a **draft**, the backend **embeds the query**, runs **dense retrieval** (Chroma) and **lexical retrieval** (BM25 rebuilt from chunks for that document), **fuses** rankings with **reciprocal rank fusion** (`backend/app/rag/fusion.py`), trims to a token budget, and labels passages **E1…En**.
5. Optionally, **operator memory** (short text from past corrections similar to the current query) is prepended to the user prompt.
6. **Groq** returns JSON matching the case-fact schema; the service **validates citations** against the evidence set and may run a **single repair** completion if tags are invalid.
7. The draft and evidence list are **persisted**; the UI can **list** and **re-open** past drafts per document. Operator saves run **diff mining** and store correction rows for future **memory** retrieval.
8. **`DELETE /api/documents/{id}`** removes the **Document** row (SQLAlchemy cascades chunks and drafts), deletes the upload directory on disk, and drops matching vectors in **Chroma** so nothing is orphaned.

## RAG pipeline

**RAG** here means: *retrieve evidence that is actually in the corpus, show it to the model under strict labels, and verify the model only cites those labels.* Indexing and query paths are separated below.

### Stages (indexing and query)

| Phase | Step | What happens |
|--------|------|----------------|
| **Indexing** | Parse and chunk | Router picks native PDF text, OCR, or MarkItDown; output is overlapping chunks with page and `source` metadata. |
| **Indexing** | Persist | Full chunk text written to **SQLite** (source of truth for UI and audits). |
| **Indexing** | Embed | Local embedding model encodes each chunk vector (no Groq spend on indexing). |
| **Indexing** | Vector store | Vectors upserted to **Chroma** with `chunk_id` / `document_id` metadata. |
| **Indexing** | Lexical | Same chunk texts tokenized for **BM25** at query time (rebuilt per request for demo scale). |
| **Query** | Query encoding | User `query` string embedded with the **same** model as chunks. |
| **Query** | Hybrid retrieve | **Top‑k** dense neighbors from Chroma and **top‑k** BM25 hits in parallel, scoped to the active document. |
| **Query** | Fusion | **RRF** merges two ranked lists and deduplicates by `chunk_id`. |
| **Query** | Context build | Truncate to `max_context_chunks` / char budget; assign **E1…En**; serialize only those passages into the prompt. |
| **Query** | Memory (optional) | Top similar **operator_corrections** snippets appended as a “preferences” block (does not replace evidence). |
| **Query** | Generate | Groq receives system + user messages; JSON output with bullets citing `[E#]`. |
| **Query** | Grounding check | Parser validates `[E#]` labels; optional **repair** pass; issues surfaced to the client as `citation_issues`. |

**Out of scope for v1:** cross-encoder reranking, continual learning of the retriever weights, and multi-tenant isolation (single SQLite + local Chroma path per deployment config).

### RAG pipeline diagram

The plan’s **13** RAG stages are drawn below as a **top-to-bottom** `flowchart TB` (easier to read at large type than a single wide row). Source: [diagrams/rag-pipeline.mmd](diagrams/rag-pipeline.mmd). From `docs/diagrams/`, regenerate the SVG with e.g. `npx --yes @mermaid-js/mermaid-cli@11.4.0 -i rag-pipeline.mmd -o rag-pipeline.svg -w 960 -H 1800 -s 1.45 -b white -q` (adjust viewport flags if labels clip).

![RAG pipeline: stages 1 through 13](diagrams/rag-pipeline.svg)

**Stages 1–7 (indexing):** load → parse/extract → chunk → persist SQLite → embed → Chroma upsert → BM25 token corpus from chunk texts. **Stages 8–13 (each draft request):** **8** query embedding; **9** hybrid dense + lexical retrieval scoped to the document; **10** RRF fusion; **11** context packing with **E** labels plus optional **operator memory**; **12** Groq generation; **13** citation validation and optional **repair**.

## Design choices (short)

- **SQLite + Chroma**: relational data and vectors are split so SQL stays simple and similarity search stays in a purpose-built store.
- **Local embeddings**: keeps indexing cost and latency predictable; Groq is reserved for the generative step.
- **Hybrid + RRF**: legal-style queries often mix exact phrases (parties, statute refs) with paraphrases; BM25 + dense covers both.
- **External prompts**: `drafting.yaml` keeps iteration on wording and schema out of Python diffs.

For evaluation ideas tied to this architecture, see [EVALUATION.md](EVALUATION.md).
