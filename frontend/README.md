# Gravitas frontend

React 18 + Vite + TypeScript + Tailwind. Calls the FastAPI API using `VITE_API_URL` (see `.env.example`). Optional Vite dev proxies for `/api` and `/health` are configured when you use an empty base URL (advanced).

## Setup

```bash
cd frontend
cp .env.example .env
npm install
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Vite dev server at http://localhost:5173 |
| `npm run build` | Typecheck + production bundle |
| `npm run preview` | Preview the production build |

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | API origin, e.g. `http://127.0.0.1:8000` (no trailing slash required) |

Never put Groq or other secrets in the frontend; only the backend should hold API keys.

## Routes

- `/` — Upload zone and document list  
- `/documents/:id` — Chunks table, drafting query, evidence panel, draft with clickable `[E#]` citations  

If the backend routes differ, update `src/lib/api.ts` after checking `backend/app/main.py` and `backend/app/api/routers/`.
