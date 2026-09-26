# ARGUS

Live incident console. See `REALTIME-INTEGRATION.md` (wiring) and the design system project (visuals).

```
backend/    FastAPI :8000  — /graph /logs /query, code indexer, log analyzer, traffic_sim.py
frontend/   Vite + React   — one API layer (src/api.js), design-system bundle in public/
sample_repo/  default REPO_PATH: a small multi-service Python codebase to index
```

## Setup
```
cd backend  && pip install -r requirements.txt && cp .env.example .env   # then set ANTHROPIC_API_KEY
cd frontend && npm install && cp .env.example .env.local                 # sets VITE_API_URL (env files are git-ignored)
```

## Run (three terminals)
```
cd backend  && uvicorn main:app --port 8000
cd frontend && npm run dev                # :5173 (falls back to `npx vite --port 5174` if taken; CORS allows both)
cd backend  && python traffic_sim.py      # type payment | db | ambiguous | none + Enter to trigger a scenario
```

Point `REPO_PATH` in `backend/.env` at any Python repo laid out as `services/<name>/*.py`
(or top-level service dirs); services and edges are derived from its imports.
