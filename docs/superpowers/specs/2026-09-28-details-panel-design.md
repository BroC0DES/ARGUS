# Details panel (incident report deep-dive) — design

**Goal:** A "Details" button at the bottom-right of the Report screen opens a
full-screen modal that explains an incident the way a person would explain it
out loud — plain-English paragraphs first, backing data (logs/code/diff)
underneath — covering root cause, blast radius, evidence, trust/verification,
fix, and next actions. No LLM call, no invented facts, no backend changes:
every sentence is a template filled from fields `/query` already returns.

**Why:** The existing Report card (`IncidentReport` in
`frontend/public/ds_bundle.js`) is intentionally terse — a headline, not a
walkthrough. Users (not just developers) need to understand *what happened*
without parsing raw log/code snippets unassisted.

## Non-goals
- No new backend endpoint, no new LLM call, no change to `query_pipeline.py`'s
  CONFIG/routing/confidence logic.
- No change to `frontend/public/ds_bundle.js` (generated design-system bundle
  — this feature is additive, composed alongside it).
- Model name stays "mistral" everywhere (explicit user decision) — the
  investigation-flow diagram reads it live from `/health`'s `ollama_model`
  field rather than hardcoding a string, so it's always truthful regardless.
- No literal "MEDIUM" confidence tier (ARGUS's formula is binary high/low —
  inventing a middle tier would misrepresent the real system).
- No raw "FRONTEND SUMMARY JSON" dump in the UI (contradicts "plain English
  and simple"); a collapsed "Raw response" block is a nice-to-have, not
  required.

## Data source
100% derived from the existing `POST /query` response (`backend/main.py`
`run_query()`'s return dict — see `backend/query_pipeline.py:744-769`) plus
`GET /health`'s `ollama_model` field, both already polled/fetched in
`ConsoleApp.jsx`. No new fields, no new requests.

## Component
New file: `frontend/src/DetailsModal.jsx` — plain React, styled inline with
the same CSS custom properties (`var(--surface-3)`, `var(--hairline)`,
`var(--space-*)`, `argus-body-sm` etc.) `ConsoleApp.jsx` already uses, so it
matches visually without touching the generated bundle. It reuses these
already-exported design-system primitives from `window.ARGUSDesignSystem_7fa82c`:
`Icon`, `Badge`, `Button`, `CodeBlock`, `CitationChip`, `ConfidenceTag`,
`ActivityBadge`, `IncidentTimeline`, `StatGrid`.

Props: `response` (the raw `/query` result, i.e. `result.response` already
held in `ConsoleApp` state), `ollamaModel` (string, from `healthPoll.data`),
`onClose`, `onCitationClick`, `onServiceClick` (same callback shapes
`IncidentReport` already uses, so clicking a cited log or an affected service
inside Details does the same thing it does in the main report: jump to that
log line / open that node's panel).

## Wiring into ConsoleApp.jsx
- New state: `const [detailsOpen, setDetailsOpen] = React.useState(false)`.
- In the `screen === "report"` block, after `<IncidentReport>`, a
  right-aligned row with a `Details` button (visible whenever `result`
  exists, i.e. a query has run — including the "no confident cause" case,
  which still has useful sections: summary, what-was-checked, evidence).
  Hidden only when there's truly nothing (`!result`).
- `{detailsOpen && <DetailsModal response={response} ollamaModel={healthPoll.data?.ollama_model} onClose={...} onCitationClick={(e) => { setDetailsOpen(false); setScreen("workspace"); flash(e.id); }} onServiceClick={(id) => { setDetailsOpen(false); setScreen("workspace"); setSelected(id); }} />}`
  rendered as a fixed-overlay modal, same pattern as the existing
  `exportText` postmortem-copy dialog (`ConsoleApp.jsx:553-574`) — click
  outside or an X button closes it.

## Section-by-section content

Every section below is **prose first** (a template string built from real
fields, in the style `confidence_reason`/`_fallback_narrative` already use in
`backend/explain.py` / `backend/query_pipeline.py`), **then** the supporting
raw detail (table/snippet/diff). Fallback text everywhere a needed field is
empty: `"Not available in the current investigation data."` Nothing here is
computed server-side — all prose-building functions live in `DetailsModal.jsx`
itself, pure functions of `response`.

1. **Incident Summary** — 2–3 sentences: severity (derived: `"Critical"` if
   `answer_type==="incident" && confidence==="high"`, `"Uncertain"` if
   `confidence==="low"`, `"No incident"` otherwise), the exact issue
   (`root_cause_service` + `failure_type`), and whether it's cascading
   (`affected_nodes.length > 0`).
2. **Exact Root Cause** — `root_cause_service` → `root_cause_function` →
   `failure_type` → `confidence`, then one sentence on *why*: single
   candidate + error volume (from `diagnosis.label`/`root_errors`), or the
   fixed sentence *"Root cause could not be conclusively established from the
   available evidence."* when `answer_type !== "incident"` or the incident is
   ambiguous.
3. **Failure Path & Blast Radius** — prose describing the path
   (`trace_path`, arrow-joined) and impact count, then the path diagram and
   one line per `affected_nodes` entry (already has `name`/`health`/`note`).
4. **Incident Timeline** — prose lead sentence, then `timeline` rendered via
   the existing `IncidentTimeline` component.
5. **Evidence** — prose intro (count + common signature), then each
   `evidence_logs` entry (id/time/service/severity/text) as a `CitationChip`
   row, clickable.
6. **Code Responsible** — prose tying the code to the failure, then
   `relevant_code` (file/function/lines) via `CodeBlock`, plus a relevance
   sentence bucketed from `diagnosis.raw_relevance` (`>=0.6` "closely
   matches", `0.3–0.6` "loosely matches", `<0.3` "only weakly matches").
7. **Why Should I Trust This?** — four checks, each a real sentence, each
   derived from field *presence* (never asserted blind):
   - LOG VERIFIED: `evidence_logs.length > 0`
   - GRAPH VERIFIED: `trace_path.length > 0`
   - CODE VERIFIED: `relevant_code != null`
   - FIX VERIFIED: `recommended_fix != null` (shown as "Not applicable" with
     its own sentence, not a failure, when no fix was proposed)
   Then `Confidence: HIGH` / `LOW` (never MEDIUM) with one sentence from
   `diagnosis.confidence_reason` when present, else a generic high-confidence
   sentence.
8. **Recommended Fix** — prose one-liner, then the diff via `CodeBlock`
   (`diff` mode) when `recommended_fix` exists; otherwise the fallback
   sentence plus "a developer should review `root_cause_service`'s code
   directly."
9. **Fix Safety Check** — templated bullets from real signals only: low
   confidence → suggests more investigation; `affected_nodes.length > 0` →
   names them, notes they should recover once the root is fixed; no fix →
   notes manual review is needed. Never invents config-change risk (no real
   ARGUS signal supports that claim).
10. **Next Actions** — 3–5 checklist lines (`□ ...`), each conditioned on
    which fields are actually populated (matches the spec's own checklist
    format for this one section).

**Investigation flow** — static diagram (LOGS → ANOMALY DETECTION → TF-IDF
CODE RETRIEVAL → DEPENDENCY GRAPH → `{ollamaModel}` → CLAIM VALIDATION →
VERIFIED RCA), one line above it: *"This is the same pipeline that produced
this report — the code decided the root cause and confidence; the model only
wrote the explanation."* Terms are ARGUS's real ones (no "NetworkX", no
"AST indexing", no "LangChain", no ChromaDB mention — none of those are part
of this system).

## Testing
Manual verification (no existing frontend test harness in this repo): run
`npm run dev`, trigger a scenario via the existing scenario switcher, ask a
question, open Report → Details, confirm every section renders real data (or
the correct fallback sentence) for: a high-confidence single-root case, a
low-confidence/ambiguous case, and a "no confident cause" case.
