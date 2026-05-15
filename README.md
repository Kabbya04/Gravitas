<h1 align="center">Gravitas</h1>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://docs.conda.io/"><img src="https://img.shields.io/badge/Conda-44A833?style=flat-square&logo=anaconda&logoColor=white" alt="Conda"></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite"></a>
  <a href="https://www.trychroma.com/"><img src="https://img.shields.io/badge/ChromaDB-FF6433?style=flat-square" alt="ChromaDB"></a>
  <a href="https://groq.com/"><img src="https://img.shields.io/badge/Groq-F55036?style=flat-square&logo=groq&logoColor=white" alt="Groq"></a>
  <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" alt="PyTorch"></a>
  <a href="https://www.sbert.net/"><img src="https://img.shields.io/badge/sentence--transformers-yellow?style=flat-square&logo=huggingface&logoColor=black" alt="sentence-transformers"></a>
  <a href="https://github.com/tesseract-ocr/tesseract"><img src="https://img.shields.io/badge/Tesseract-OCR-000000?style=flat-square&logo=tesseract&logoColor=white" alt="Tesseract OCR"></a>
  <br>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React"></a>
  <a href="https://vitejs.dev/"><img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite"></a>
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/Tailwind-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"></a>
</p>

Internal workflow for **messy legal-style documents**: extract text (native PDF, **Tesseract** OCR, or MarkItDown), optional **Groq OCR refine** before chunking, **hybrid RAG** (Chroma + BM25), grounded drafting with inspectable `[E#]` evidence tags, and an **operator edit** memory loop.

| Resource | Description |
|----------|-------------|
| [plan.md](plan.md) | Assessment-aligned scope and build plan |
| [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) | Folder map |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, data flow, and RAG pipeline |

---

## Quick start

### Prerequisites

- [Conda](https://docs.conda.io/) (Miniconda or Miniforge)
- [Node.js](https://nodejs.org/) 18+
- [Groq API key](https://console.groq.com/)
- **Tesseract** and **Poppler** for OCR and PDF rasterization (see [system dependencies](#system-dependencies-ocr--pdf-rasterization))

Run the **backend** and **frontend** in separate terminals. When both are up, open **http://localhost:5173**.

### 1. Backend (Conda)

Use environment **`gravitas`** with **Python 3.11** ([environment.yml](environment.yml)).

**macOS / Linux** — from the repository root:

```bash
conda env create -f environment.yml
# Existing env with dependency changes:
# conda env update -f environment.yml --prune

conda activate gravitas
cd backend
cp .env.example .env
# Set GROQ_API_KEY in .env; tune non-secrets in config.yaml

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Windows** — from the repository root (Anaconda Prompt, PowerShell, or cmd):

```bat
conda env create -f environment.yml
REM Existing env: conda env update -f environment.yml --prune

conda activate gravitas
cd backend
copy .env.example .env
REM Set GROQ_API_KEY in .env; tune non-secrets in config.yaml

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

PowerShell alternative for `.env`: `Copy-Item .env.example .env`

**Tests** (from `backend/`, any platform):

```bash
pytest
```

#### System dependencies (OCR / PDF rasterization)

| Platform | Command / notes |
|----------|-----------------|
| **macOS** | `brew install tesseract poppler` |
| **Linux (Debian/Ubuntu)** | `sudo apt-get install -y tesseract-ocr poppler-utils` |
| **Windows** | Install **Tesseract** and **Poppler**; add both to `PATH`. Examples (elevated terminal if required):<br>• Chocolatey: `choco install tesseract poppler -y`<br>• Scoop: `scoop install tesseract poppler`<br>• winget: `winget install UB-Mannheim.TesseractOCR`<br>Poppler: [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases) — add the `bin` folder to `PATH`. Restart the terminal after installing. |

### 2. Frontend

From the repository root:

```bash
cd frontend
cp .env.example .env   # optional; see frontend/.env.example
npm install
npm run dev
```

In development, Vite proxies `/api` and `/health` to `http://127.0.0.1:8000`. Set `VITE_API_URL` in `frontend/.env` only when not using the proxy.

---

## Web app

### Features

| Area | Capabilities |
|------|----------------|
| **Documents** | Upload, processing status, open, delete (in-app confirmation modal) |
| **Workspace** | Chunk table, saved drafts, hybrid retrieval, drafting with optional **Use memory**, editable draft, evidence panel, **Save operator version** |
| **Delete** | Removes SQLite rows (chunks and drafts cascade), Chroma vectors, and `backend/data/files/<id>/` |

### Screenshots

**Documents** — upload zone and document list.

![Documents home — upload zone and document list](docs/diagrams/home-documents.png)

**Document workspace** — chunks, drafting controls, and evidence panel.

![Document workspace — chunks, drafting controls, and evidence panel](docs/diagrams/document-workspace.png)

**Saved drafts** — list with Open and Reload.

![Saved drafts — list with Open and Reload](docs/diagrams/saved-drafts.png)

**Drafting** — generated output with `[E#]` tags and retrieved sources.

![Drafting output with evidence tags and retrieved sources](docs/diagrams/drafting-evidence.png)

---

## Configuration

| File | Purpose |
|------|---------|
| `backend/.env` | Secrets: `GROQ_API_KEY`; optional `GROQ_MODEL`, `DATA_DIR` |
| `backend/config.yaml` | Tunables: models, chunking, `ocr_refine`, retrieval `k`, CORS, prompt paths |
| `backend/prompts/drafting.yaml` | Drafting prompts (Jinja2) |
| `backend/prompts/ocr_refine.yaml` | Post-OCR cleanup prompts (Jinja2) |
| `environment.yml` | Conda env **`gravitas`** (Python 3.11) and pip requirements |

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/documents` | Multipart upload; background processing |
| `GET` | `/api/documents` | List documents |
| `GET` | `/api/documents/{id}` | Document metadata |
| `GET` | `/api/documents/{id}/chunks` | Chunk list |
| `DELETE` | `/api/documents/{id}` | Purge document, files, and Chroma vectors (`204`) |
| `POST` | `/api/documents/{id}/draft` | Body: `{ "query": "...", "use_memory": true }` — create draft |
| `GET` | `/api/documents/{id}/drafts` | List drafts (query, `created_at`, `has_operator_version`) |
| `GET` | `/api/drafts/{draft_id}` | Load draft (operator text preferred when present) |
| `POST` | `/api/drafts/{draft_id}/operator` | Body: `{ "text": "..." }` — save operator version and mine edits |

Interactive docs: **http://127.0.0.1:8000/docs** (with the backend running).

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and RAG pipeline |
| [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) | Scope, tradeoffs, and limitations |
| [docs/EVALUATION.md](docs/EVALUATION.md) | Evaluation approach |
