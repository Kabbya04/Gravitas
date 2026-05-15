# Gravitas frontend

React 18 + Vite + TypeScript + Tailwind. Calls the FastAPI API using `VITE_API_URL` (see `.env.example`). With an **empty** `VITE_API_URL`, same-origin requests use Vite’s dev proxy for `/api` and `/health` to `http://127.0.0.1:8000`.

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
| `VITE_API_URL` | API origin, e.g. `http://127.0.0.1:8000` (no trailing slash). Leave **empty** in dev to use the Vite proxy. |

Never put Groq or other secrets in the frontend; only the backend should hold API keys.

## Routes and UI

- **`/`** — Upload zone, document table with **Open** / **Delete**. Delete opens a **`ConfirmDialog`** (in-app modal; not `window.confirm`).
- **`/documents/:id`** — Status polling until **ready**, chunk table, **Saved drafts** (list + **Open** / **Reload**), drafting (**Generate**, optional **Use memory**), **editable** draft textarea (keep `[E#]` markers aligned with evidence), evidence panel, **Save operator version**, and **Delete document** (same modal pattern).

Shared UI: [`src/components/Layout.tsx`](src/components/Layout.tsx), [`src/components/ConfirmDialog.tsx`](src/components/ConfirmDialog.tsx). API types and helpers: [`src/lib/api.ts`](src/lib/api.ts).

If backend routes change, update `src/lib/api.ts` and match `backend/app/api/routers/`.
