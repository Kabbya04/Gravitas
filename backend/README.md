# Backend

## Setup (Conda)

Use the **`gravitas`** Conda environment (Python **3.11**). From the **repository root**:

```bash
conda env create -f environment.yml
conda activate gravitas
```

Then install / refresh Python deps from this directory:

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env — at minimum set GROQ_API_KEY
```

Optional: install **Tesseract** and **Poppler** for OCR / PDF rasterization (see root README).

## Run

```bash
conda activate gravitas
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Tests

```bash
conda activate gravitas
cd backend
pytest
```

## HTTP surface (summary)

| Method | Path | Role |
|--------|------|------|
| `POST` | `/api/documents` | Multipart upload |
| `GET` | `/api/documents`, `/api/documents/{id}`, `/api/documents/{id}/chunks` | List / detail / chunks |
| `DELETE` | `/api/documents/{id}` | Purge DB row, files, Chroma vectors |
| `POST` | `/api/documents/{id}/draft` | Create draft (Groq + persist) |
| `GET` | `/api/documents/{id}/drafts` | List draft metadata |
| `GET` | `/api/drafts/{draft_id}` | Load one draft |
| `POST` | `/api/drafts/{draft_id}/operator` | Save operator text + mine edits |

Routers live under `app/api/routers/`. See the root [README.md](../README.md) for the full product picture.

## Layout

- `app/main.py` — FastAPI app and CORS
- `app/api/routers/` — HTTP routes
- `app/core/` — env settings, YAML config, prompt loading
- `app/db/` — SQLAlchemy models + SQLite session
- `app/ingestion/` — extract, chunk, ingest service, document purge on delete
- `app/rag/` — embedder, Chroma, BM25, hybrid retrieval
- `app/llm/` — Groq client, citation helpers
- `app/learning/` — operator edit capture + memory block
- `config.yaml` — non-secret tunables
- `prompts/` — prompt templates (YAML + Jinja2)
