# ARGUS

Live incident console. See `REALTIME-INTEGRATION.md` (wiring) and the design system project (visuals).

```
backend/          FastAPI :8000  — /graph /logs /query /scenario, code indexer, log analyzer, traffic_sim.py
frontend/         Vite + React   — one API layer (src/api.js), design-system bundle in public/
sample_repo/      default REPO_PATH: a small multi-service Python codebase to index
mock-codebase2/   alternate REPO_PATH: a TypeScript codebase with two planted, commented
                  bugs and 3 scenario log fixtures — see "Demo scenarios" below
```

## Setup
```
cd backend  && pip install -r requirements.txt && cp .env.example .env
cd frontend && npm install && cp .env.example .env.local                 # sets VITE_API_URL (env files are git-ignored)
```

## LLM: local Ollama (no API key)
ARGUS runs its diagnosis on a **local Ollama model** — no Anthropic/Claude API key and no cloud calls.
```
ollama pull mistral          # any model with reasonable JSON/structured-output support works
ollama serve                 # http://localhost:11434 (skip if already running)
```
Configure in `backend/.env`: `OLLAMA_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `mistral`).

## Run (three terminals)
```
cd backend  && uvicorn main:app --port 8000
cd frontend && npm run dev                # :5173 (falls back to `npx vite --port 5174` if taken; CORS allows both)
cd backend  && python traffic_sim.py      # type payment | db | ambiguous | none + Enter to trigger a scenario
```

Point `REPO_PATH` in `backend/.env` at any Python **or TypeScript** repo laid out as
`services/<name>/*.{py,ts,tsx}` (or top-level service dirs); services and edges are
derived from its imports (Python `import`/`from` statements, or TS relative-path
`import` sources — either way, a real edge means one service's code actually imports
another's).

## Demo scenarios (mock-codebase2)
`mock-codebase2/packages` is a 6-service TypeScript codebase with two planted,
commented bugs (`payment-service/src/gateway.ts` BUG #1: timeout too short;
`db-pool/src/pool.ts` BUG #2: connection limit too low, cascading into
payment-service/ledger-worker/orders-service but not notify-worker). Point
`REPO_PATH` at `mock-codebase2/packages` to index it instead of `sample_repo`.

Three static log fixtures in `mock-codebase2/logs/` (`scenario-payment-timeout.log`,
`scenario-db-exhaustion.log`, `scenario-cascading-failure.log`) drive it — since
they ship with fixed, long-past timestamps, `POST /scenario {"name": "<slug>"}`
replays the chosen file into `LOG_PATH` with every timestamp shifted so the last
line lands at "now" (relative spacing between events is preserved). `GET /health`
reports `active_scenario` and `available_scenarios`; the frontend's "Demo scenario"
buttons (top of the workspace graph panel) call this and show the current one live.
`{"name": "none"}` clears the active scenario without touching the log file.
