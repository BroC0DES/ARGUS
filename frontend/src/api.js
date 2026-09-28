// The only place the frontend talks to the backend. Components import from here;
// nothing else calls fetch().
import React from "react";

const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, timeoutMs = 10000 } = {}) {
  if (!BASE) throw new ApiError("VITE_API_URL is not set (see frontend/.env.example).");
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(BASE + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try { detail = (await res.json()).detail || detail; } catch { /* non-JSON error body */ }
      throw new ApiError(detail, res.status);
    }
    return await res.json();
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e.name === "AbortError") throw new ApiError("The request timed out.");
    throw new ApiError("Cannot reach the ARGUS backend. Is it running?");
  } finally {
    clearTimeout(timer);
  }
}

export const getGraph = () => request("/graph");
export const getHealth = () => request("/health");
export const getLogs = (n = 60) => request(`/logs?n=${n}`).then((r) => r.lines);
// /query runs retrieval + an LLM call on a local model, so it gets a much longer
// timeout than polls -- kept just above the backend's own OLLAMA_TIMEOUT (180s,
// see backend/query_pipeline.py) so the frontend never gives up before the
// backend would have. A cold/unloaded Ollama model can take 100s+ just to load
// into memory on its first call; main.py fires a warmup ping at backend startup
// to avoid that happening mid-demo, but this margin covers it either way.
export const postQuery = (question) => request("/query", { method: "POST", body: { question }, timeoutMs: 200000 });
// Scenario replay itself is instant (it just rewrites the log file) -- generous
// timeout only in case the backend is briefly busy with something else.
export const setScenario = (name) => request("/scenario", { method: "POST", body: { name }, timeoutMs: 15000 });
// Toggles mock-codebase2's traffic simulator process on/off -- see
// backend/traffic_control.py. Instant either way (just starting/killing a
// process), so a short timeout is fine.
export const setTraffic = (action) => request("/traffic", { method: "POST", body: { action }, timeoutMs: 10000 });

/**
 * Poll `fn` every `ms`. A failed poll keeps the last-known-good data (never
 * flashes the UI empty) and only flips `error`; the next tick retries, so a
 * restarted backend or simulator just resumes.
 */
export function usePoll(fn, ms) {
  const [state, setState] = React.useState({ data: null, error: null });
  const fnRef = React.useRef(fn);
  fnRef.current = fn;
  React.useEffect(() => {
    let alive = true;
    let timer;
    const tick = async () => {
      try {
        const data = await fnRef.current();
        if (alive) setState({ data, error: null });
      } catch (e) {
        if (alive) setState((s) => ({ data: s.data, error: e }));
      }
      if (alive) timer = setTimeout(tick, ms);
    };
    tick();
    return () => { alive = false; clearTimeout(timer); };
  }, [ms]);
  return state;
}

/** Map a /query response onto the incident shape the report components render. */
export function toIncident(r) {
  const ext = r.relevant_code ? r.relevant_code.filename.split(".").pop() : "";
  const d = r.diagnosis || {};
  return {
    service: r.root_cause_service,
    summary: r.summary,
    timeline: r.timeline,
    confidentCauseFound: r.confident_cause_found,
    confidence: r.confidence,
    ruledOut: r.ruled_out,
    rootCause: r.root_cause,
    rootCauseFn: r.root_cause_function || undefined,
    rootCauseFailureType: r.failure_type || undefined,
    stats: r.stats,
    evidence: r.evidence_logs.map((l) => ({ id: l.id, label: `log:${l.time}` })),
    evidenceLogs: r.evidence_logs,
    affected: r.affected_nodes,
    code: r.relevant_code && { filename: r.relevant_code.filename, startLine: r.relevant_code.start_line, lines: r.relevant_code.lines, language: ext },
    fix: r.recommended_fix,
    // Activity + confidence-explanation fields, straight from the primary incident's
    // diagnosis block -- no recomputation, just renamed to camelCase for the components.
    activity: d.activity ?? null,
    lastErrorAgeS: d.last_error_age_s ?? null,
    confidenceReason: d.confidence_reason ?? null,
    competingCandidates: d.competing_candidates || [],
    // Every other incident the backend found this turn (see /query's `incidents`),
    // for the "Also detected" list -- the primary is filtered out in the component
    // by comparing `service`, since IncidentReport already renders it above.
    incidents: (r.incidents || []).map((inc) => ({
      service: inc.root,
      confidence: inc.confidence_label,
      score: inc.score,
      isMinor: inc.is_minor,
      activity: inc.activity,
      lastErrorAgeS: inc.last_error_age_s,
    })),
  };
}
