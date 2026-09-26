# REALTIME-INTEGRATION.md — ARGUS

## 1. What this file is
DESIGN.md defines what everything looks like. This file defines what
everything connects to. Read both together — DESIGN.md is the visual
spec, this is the wiring spec. Claude Code should treat this as the
checklist for turning the Claude-Design-built frontend from a mock-data
demo into a real, live system.

## 2. Architecture
Three local processes, no deployment needed for the hackathon:
- **Backend** — Python + FastAPI, port 8000
- **Frontend** — React + Vite, port 5173 (already built, per DESIGN.md)
- **Traffic simulator** — standalone script, feeds realistic log data
  continuously so the system has something real to detect

## 3. Backend — what must exist and be genuinely real
- **POST /query** — full pipeline: Log Analyzer (current anomalies) →
  Code Indexer (vector store + dependency graph retrieval) → bundle
  context → real Anthropic API call (Claude Haiku 4.5) → parse into
  `{root_cause, evidence_logs, relevant_code, recommended_fix,
  confidence, trace_path, node_ids, affected_nodes, timeline}`. Every
  field must trace back to something computed that request — nothing
  fixed.
- **GET /graph** — live dependency graph; each node's status (error
  count) computed from current log data, not static.
- **GET /logs** — most recent N lines, freshly read from disk each call.
- **CORS** enabled for `http://localhost:5173`.
- **.env**: `ANTHROPIC_API_KEY`, `REPO_PATH` (absolute path to the real
  codebase being indexed).

## 4. Frontend — what Claude Code needs to change in the Claude-Design build
- Find wherever mock/hardcoded data currently lives (graph, logs, chat
  responses, report) and replace with real `fetch()` calls to the
  endpoints above. Centralize this in one API layer/file — don't scatter
  fetch calls across components.
- `VITE_API_URL` env var — never hardcode `localhost:8000` inline.
- Graph and log panels poll every 3–5s.
- Chat: pulsing "thinking" state (DESIGN.md §9.10/§9.13) while `/query`
  is in flight; clear error state if the call fails — never a silent hang.
- Failed poll → keep last-known-good state, don't flash the UI empty.
- **Node Detail Panel** (§9.6): relevance bridge text and matching
  code-line highlight must be generated from the real response, not
  placeholder text.
- **Postmortem export** (§9.7a): verify chronological log sorting and
  the honest-failure edge case both work against *real* incident data,
  not just the one example we hand-tested earlier in this build.

## 5. Traffic simulator
Separate script, separate terminal. Appends log lines on an interval
(mostly healthy, occasional real anomaly bursts) to the file the Log
Analyzer reads — this is what makes the status strip pulse and counts
change *during* the actual demo instead of sitting static.

## 6. Codebase indexing
`REPO_PATH` env var points to a real repo on disk. Code Indexer reads it
directly via tree-sitter — no upload UI, no folder-browser needed for
the hackathon. (Optional "Connect Repository" path-input screen only if
time remains — not required.)

## 7. Running order
```
Terminal 1: cd backend && uvicorn main:app --reload --port 8000
Terminal 2: cd frontend && npm run dev
Terminal 3: cd backend && python traffic_sim.py
```

## 8. Verification checklist — how to confirm it's actually real
- [ ] Ask two different chat questions → two genuinely different, evidence-specific answers (not similar boilerplate)
- [ ] Log panel receives new lines without a manual refresh
- [ ] Trigger a deliberately unclear/low-signal scenario → dashed node + "Needs review" + the postmortem's honest-failure state all activate correctly together
- [ ] Postmortem's chronological sorting and relevance bridge render correctly against a *real* incident, not just the hand-tested example
- [ ] Killing the traffic simulator and restarting it doesn't break the frontend (poll should just resume showing fresh data)

## 9. Explicitly not needed
No deployment/hosting for the demo. No rewriting the frontend in Python
or the backend in JS — React + FastAPI over REST is correct and final,
don't change it.
