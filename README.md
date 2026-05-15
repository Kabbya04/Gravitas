# Gravitas

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Conda](https://img.shields.io/badge/Conda-44A833?style=flat-square&logo=anaconda&logoColor=white)](https://docs.conda.io/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6433?style=flat-square)](https://www.trychroma.com/)  
[![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)  
[![Groq](https://img.shields.io/badge/Groq-F55036?style=flat-square&logo=groq&logoColor=white)](https://groq.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Sentence Transformers](https://img.shields.io/badge/sentence--transformers-yellow?style=flat-square&logo=huggingface&logoColor=black)](https://www.sbert.net/)
[![Tesseract](https://img.shields.io/badge/Tesseract-OCR-000000?style=flat-square&logo=tesseract&logoColor=white)](https://github.com/tesseract-ocr/tesseract)

Internal workflow for **messy legal-style documents**: extract text (with OCR when needed), **hybrid RAG** (Chroma + BM25), **Groq**-powered grounded drafting with inspectable evidence tags, and an **operator edit** memory loop.

See [plan.md](plan.md) for the assessment-aligned architecture and [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) for a folder map.

## Quick start

### Python environment (Conda)

Use a Conda env named **`gravitas`** with **Python 3.11** (declared in [environment.yml](environment.yml)).

```bash
# From repo root — creates env gravitas and pip-installs backend/requirements.txt
conda env create -f environment.yml
# If the env already exists and you changed dependencies:
# conda env update -f environment.yml --prune

conda activate gravitas
cd backend
cp .env.example .env
# Set GROQ_API_KEY in .env. Tune non-secret knobs in config.yaml.

pip install -r requirements.txt   # safe to re-run; matches environment.yml pip section

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Tests** (same env, from `backend/`):

```bash
pytest
```

System dependencies for OCR / PDF rasterization:

- macOS: `brew install tesseract poppler`
- Ubuntu: `sudo apt-get install -y tesseract-ocr poppler-utils`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://127.0.0.1:8000` during development. Optional: set `VITE_API_URL` in `frontend/.env` (see `frontend/.env.example`).

### Web app (what you get in the UI)

- **Documents** — Upload files, see processing status, **open** a document, or **delete** it. Delete uses an in-app confirmation modal (not the browser `confirm` dialog).
- **Document workspace** — After **ready**: chunk table, **saved drafts** list (every **Generate** creates a server-side draft; **Open** reloads text + evidence), drafting query with optional **Use memory**, editable draft textarea, evidence column, **Save operator version**.
- **Delete document** — Available from the list and from the document header; removes SQLite rows (cascading chunks and drafts), Chroma vectors for that id, and files under `backend/data/files/<id>/`.

## Configuration

| Location | Purpose |
|----------|---------|
| `backend/.env` | **Secrets** (e.g. `GROQ_API_KEY`). Optional `GROQ_MODEL`, `DATA_DIR`. |
| `backend/config.yaml` | Tunables: Groq model default, embedding model, chunk sizes, retrieval `k`, CORS origins, prompt file path. |
| `backend/prompts/drafting.yaml` | LLM prompt templates (Jinja2). |
| `environment.yml` | Conda env **`gravitas`** (Python 3.11) + pip requirements. |
| `DIRECTORY_STRUCTURE.md` | One-line purpose map for repo folders. |

## API (high level)

- `POST /api/documents` — multipart upload; processing runs in background.
- `GET /api/documents`, `GET /api/documents/{id}`, `GET /api/documents/{id}/chunks`
- `DELETE /api/documents/{id}` — remove document, chunks, drafts, on-disk upload folder, and Chroma vectors for that id (`204` on success).
- `POST /api/documents/{id}/draft` — JSON `{ "query": "...", "use_memory": true }`; persists a **Draft** row and returns `draft_id`, content, evidence, `citation_issues`.
- `GET /api/documents/{id}/drafts` — list saved drafts for a document (metadata: query, `created_at`, `has_operator_version`).
- `GET /api/drafts/{draft_id}` — load a saved draft (content prefers operator text when present; evidence replayed from storage).
- `POST /api/drafts/{draft_id}/operator` — JSON `{ "text": "..." }` saves operator text and mines edit pairs for future prompts.

## Submission docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)
- [docs/EVALUATION.md](docs/EVALUATION.md)
