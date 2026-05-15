# Directory structure

Brief purpose of each top-level area (and important subfolders).

## Layout tree

Source-oriented view (omits generated dirs: `frontend/node_modules/`, `frontend/dist/`, `backend/data/`, `backend/chroma_data/`, `__pycache__/`, `.pytest_cache/`). Optional IDE metadata lives under `.cursor/` (see table below).

```text
gravitas/
├── README.md
├── plan.md
├── DIRECTORY_STRUCTURE.md
├── environment.yml
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ASSUMPTIONS.md
│   ├── EVALUATION.md
│   └── diagrams/
│       ├── architecture.mmd
│       ├── architecture.svg
│       ├── rag-pipeline.mmd
│       └── rag-pipeline.svg
├── samples/
│   ├── README.md
│   └── .gitkeep
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── config.yaml
│   ├── .env.example
│   ├── prompts/
│   │   └── drafting.yaml
│   ├── tests/
│   │   ├── test_citations.py
│   │   └── test_retrieval.py
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   └── routers/
│       │       ├── health.py
│       │       ├── documents.py
│       │       └── drafts.py
│       ├── core/
│       │   ├── paths.py
│       │   ├── settings.py
│       │   ├── yaml_config.py
│       │   └── prompts.py
│       ├── db/
│       │   ├── database.py
│       │   └── models.py
│       ├── ingestion/
│       │   ├── extract.py
│       │   ├── chunking.py
│       │   └── service.py
│       ├── rag/
│       │   ├── fusion.py
│       │   ├── embedder.py
│       │   ├── chroma_store.py
│       │   ├── bm25_index.py
│       │   └── retrieval.py
│       ├── llm/
│       │   ├── citations.py
│       │   └── groq_service.py
│       └── learning/
│           └── edits.py
└── frontend/
    ├── README.md
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    ├── .env.example
    ├── public/
    │   └── vite.svg
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── vite-env.d.ts
        ├── lib/
        │   └── api.ts
        ├── components/
        │   ├── Layout.tsx
        │   └── ConfirmDialog.tsx
        └── pages/
            ├── HomePage.tsx
            └── DocumentDetailPage.tsx
```

| Path | Purpose |
|------|---------|
| [`backend/`](backend/) | FastAPI service: document ingest, RAG, Groq drafting, operator-edit loop. |
| [`backend/app/`](backend/app/) | Application package (`main`, routers, services). |
| [`backend/app/api/`](backend/app/api/) | HTTP layer: route modules and shared API wiring. |
| [`backend/app/core/`](backend/app/core/) | Settings (`.env`), YAML config, prompt template loading. |
| [`backend/app/db/`](backend/app/db/) | SQLAlchemy models and SQLite session factory. |
| [`backend/app/ingestion/`](backend/app/ingestion/) | Extract text (PDF/OCR/MarkItDown), chunk, persist to DB + vectors; **`purge_document`** removes files + Chroma + DB row for deletes. |
| [`backend/app/rag/`](backend/app/rag/) | Embeddings, Chroma, BM25, RRF fusion helper, hybrid retrieval + evidence packing. |
| [`backend/app/llm/`](backend/app/llm/) | Groq client, JSON draft parsing, citation validation helpers. |
| [`backend/app/learning/`](backend/app/learning/) | Operator diff mining and memory block for future prompts. |
| [`backend/prompts/`](backend/prompts/) | Externalized LLM prompt YAML (Jinja2); not hardcoded in Python. |
| [`backend/tests/`](backend/tests/) | `pytest` unit tests for stable helpers (no API keys required). |
| [`frontend/`](frontend/) | React + Vite + TypeScript + Tailwind UI: upload, delete (with modal confirm), chunk view, **saved drafts**, drafting, evidence, operator save. |
| [`frontend/src/`](frontend/src/) | App entry, pages (`HomePage`, `DocumentDetailPage`), shared layout, **reusable confirm dialog**, typed API client. |
| [`docs/`](docs/) | Architecture, assumptions, evaluation notes for reviewers. |
| [`docs/diagrams/`](docs/diagrams/) | Mermaid sources (`.mmd`) and rendered **SVG** diagrams for `ARCHITECTURE.md` previews. |
| [`samples/`](samples/) | Placeholder / future sample inputs and expected outputs for the assessment. |
| [`.cursor/`](.cursor/) | Cursor IDE metadata (plans, etc.); not required at runtime. **Gitignored** in this repo — do not commit. |
| [`plan.md`](plan.md) | High-level product / assessment plan (living reference). |
| [`environment.yml`](environment.yml) | Conda env `gravitas` (Python 3.11) + pip install from `backend/requirements.txt`. |

Runtime-generated paths (gitignored): `backend/data/` (uploads + SQLite), `backend/chroma_data/` (vector store), `frontend/node_modules/`, `frontend/dist/`.
