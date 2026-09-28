"""POST /query pipeline:

  Log Analyzer (current anomalies)
    -> question router (plain string matching -- which service, if any, was named)
    -> incident partitioning (plain code, dependency graph -- one incident per
       connected component of the currently-failing services)
    -> confidence, computed per incident from measurable signals
    -> Code Indexer (retrieval, scoped to the chosen incident's own root)
    -> local Ollama model (schema-constrained JSON = explanation text only, for
       the one incident actually being answered)
    -> validate the model's text against what the code already decided
    -> response

The model never chooses the diagnosis, for any incident. WHICH service is the
root cause of each incident is decided entirely by _partition_incidents()
below, from real error counts and the real dependency graph -- the model
cannot override it, and its own self-rated confidence is never consulted.
Confidence is computed by _compute_confidence() from measurable signals only.
The model's only job, for the one incident being answered, is to write the
explanation, and even that is checked afterward: if its text doesn't name the
code-chosen root (or claims a symptom is the cause), the text is discarded and
a deterministic fallback sentence is used instead.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime

from code_indexer import CodeIndexer, display_name
from log_analyzer import LogAnalyzer, WINDOW_S, _signature

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "180"))
MAX_LOG_LINES = 90
MAX_CHUNKS = 6

# All confidence-formula constants live here, and nowhere else in this module --
# no other line hardcodes a weight, threshold, divisor, or cutoff. Weights,
# threshold, and the grounding gate are unchanged since Prompt 1.
CONFIG = {
    "EVIDENCE_DIVISOR": 20,        # weighted_errors / this, capped at 1.0
    "WARNING_WEIGHT": 0.25,        # weighted_errors = errors + this * warnings
    "WEIGHT_EVIDENCE": 0.4,
    "WEIGHT_RELEVANCE": 0.25,
    "WEIGHT_DOMINANCE": 0.35,
    "HIGH_THRESHOLD": 0.65,        # score >= this -> "high"
    "ONGOING_CUTOFF_S": 60,        # last error <= this many seconds ago -> "ongoing"
    "MIN_COMPETITOR_ERRORS": 5,    # a candidate below this absolute weighted_errors is never a competitor
    "MIN_COMPETITOR_SHARE": 0.10,  # ...or below this fraction of the strongest candidate's weighted_errors
}


class QueryError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


REPORT_TOOL = {
    "name": "report_incident",
    "description": (
        "Write up the investigation. WHICH service is the root cause has already been "
        "decided by the system (given in the context as ROOT SERVICE / CANDIDATE "
        "SERVICES) -- you cannot change it. Your job is to verify it against the actual "
        "logs and code and explain it. Cite only ids that appear in the provided context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # root_service and evidence_summary are listed first on purpose: the model
            # commits to naming the (already-decided) service before it starts writing
            # prose, instead of reasoning its way toward a different one across a bunch
            # of other fields first.
            "root_service": {"type": "string", "description": "Copy the ROOT SERVICE (or, if the context lists CANDIDATE SERVICES instead, whichever one of those you investigated) exactly as given. Do not name any other service here, even if you suspect it."},
            "evidence_summary": {"type": "string", "description": "1-3 sentences, stated as fact, no hedging words. Must explicitly name root_service. Must NOT claim a SYMPTOM service (also given in the context) is the cause -- symptoms are affected BY the root cause, they are not it."},
            "root_cause_function": {"type": "string", "description": "Function name in root_service's own code, e.g. charge_card(). Omit if its code doesn't clearly show the failure."},
            "failure_type": {"type": "string", "description": "One or two words, e.g. 'timeout', 'pool exhaustion'."},
            "evidence_log_ids": {"type": "array", "items": {"type": "string"}, "description": "Ids of the log lines that show root_service's own failure."},
            "code_chunk_id": {"type": "string", "description": "Id of the code chunk (from CODE CHUNKS) that belongs to root_service and shows the failure. Omit if none of the retrieved chunks are root_service's own code."},
            "fix": {
                "type": "array",
                "description": "Diff against the chunk: each line has kind remove|add|context. 'remove' and 'context' lines must be copied verbatim from the chunk. Omit entirely if you didn't cite a code_chunk_id.",
                "items": {"type": "object", "properties": {"kind": {"type": "string", "enum": ["remove", "add", "context"]}, "text": {"type": "string"}}, "required": ["kind", "text"]},
            },
            "node_details": {
                "type": "array",
                "description": "For each service on the trace path that has a relevant chunk: why its code and logs belong together.",
                "items": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "bridge": {"type": "string", "description": "One sentence linking this service's code to the cited logs."},
                        "code_chunk_id": {"type": "string"},
                        "matches": {"type": "array", "items": {"type": "object", "properties": {"log_id": {"type": "string"}, "line_offset": {"type": "integer", "description": "0-based line index within the chunk that produced that log line"}}, "required": ["log_id", "line_offset"]}},
                    },
                    "required": ["service", "bridge", "code_chunk_id", "matches"],
                },
            },
        },
        "required": ["root_service", "evidence_summary", "evidence_log_ids"],
    },
}

SYSTEM = """You are ARGUS, an incident investigation agent. You are given live log lines, the service dependency graph, and code retrieved from the indexed repository. Diagnose using ONLY that context.

Rules:
- WHICH service is the root cause has already been decided by the system (ROOT SERVICE, or CANDIDATE SERVICES if there's more than one) -- your job is to verify and explain it, not to pick a different one, however loud its error count is. If none of the retrieved code chunks belong to that service, say so plainly in evidence_summary rather than switching to a service that happens to have a matching chunk.
- Cite only log ids and code chunk ids that appear in the context. Never invent ids, functions, or numbers.
- The context may also list SYMPTOM services -- these fail only because they depend on the root cause. Never name a symptom as the cause.
- For fixes, copy 'remove' and 'context' lines verbatim from the chunk; keep the diff minimal.
- State findings as facts, no hedging words like 'possibly'."""


def _service_ids(indexer: CodeIndexer) -> dict[str, str]:
    return {display_name(s): s for s in indexer.graph()[0]}


# =============================================================================
# 1) QUESTION ROUTER -- plain string matching, no LLM. Service names always come
#    from the dependency graph at runtime (the `services` argument); nothing
#    here is hardcoded.
# =============================================================================
def _normalize_name(s: str) -> str:
    """Hyphens, spaces, underscores, and CamelCase boundaries all collapse to
    the same form: lowercase with separators stripped. "Payment-Service",
    "payment service", "payment_service", and "PaymentService" all become
    "paymentservice", so any of those spellings match the same known service."""
    return re.sub(r"[-_\s]+", "", s).lower()


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_SERVICE_SUFFIXES = ("service", "worker", "gateway", "pool")


def _route_question(question: str, services: dict[str, str]) -> dict:
    """Returns {"mode": "specific"|"general"|"unknown_service", "target": ...}.

    - Exactly one known service's normalized name appears in the normalized
      question -> "specific", target = that service's display name.
    - More than one known service is named -> ambiguous which one is "the"
      target; falls back to "general" (which lists every incident anyway).
    - No known service named, but some word in the question looks like a
      service name (ends in service/worker/gateway/pool) and isn't one of the
      known services -> "unknown_service", so the caller can say so plainly
      instead of guessing.
    - Otherwise -> "general", target None.
    """
    norm_q = _normalize_name(question)
    matches = [disp for disp in services if _normalize_name(disp) in norm_q]
    if len(matches) == 1:
        return {"mode": "specific", "target": matches[0]}
    if len(matches) > 1:
        return {"mode": "general", "target": None}
    known_norms = {_normalize_name(d) for d in services}
    for w in _WORD_RE.findall(question):
        nw = _normalize_name(w)
        if nw.endswith(_SERVICE_SUFFIXES) and nw not in known_norms:
            return {"mode": "unknown_service", "target": w}
    return {"mode": "general", "target": None}


def _bundle(logs: LogAnalyzer, indexer: CodeIndexer, now: datetime):
    anomalies = logs.anomalies(now=now)
    recent = logs.recent(60)
    # Context lines: every warn/error line in the lookback, plus the freshest lines overall.
    picked: dict[str, object] = {}
    for a in anomalies:
        for l in a["lines"][-25:]:
            picked[l.id] = l
    for l in recent[-25:]:
        picked[l.id] = l
    lines = sorted(picked.values(), key=lambda l: l.id)[-MAX_LOG_LINES:]
    return anomalies, lines


# =============================================================================
# 2) SCOPING -- one incident per connected component of the currently-failing
#    services (edges from the real dependency graph, restricted to
#    failing<->failing pairs). This is what makes two unrelated single-cause
#    failures score as two separate incidents instead of one falsely-ambiguous
#    one: a failing service is only a candidate for OTHER failing services it's
#    actually reachable from.
# =============================================================================
def _weighted(a: dict) -> float:
    return a["errors"] + CONFIG["WARNING_WEIGHT"] * a["warns"]


def _last_error_ts(anomaly: dict):
    errors = [l for l in anomaly["lines"] if l.severity == "error"]
    return max((l.ts for l in errors), default=anomaly.get("last_seen"))


def _activity_of(anomaly: dict | None, now: datetime) -> tuple[str | None, float | None]:
    if anomaly is None:
        return None, None
    ts = _last_error_ts(anomaly)
    if ts is None:
        return None, None
    age_s = (now - ts).total_seconds()
    return ("ongoing" if age_s <= CONFIG["ONGOING_CUTOFF_S"] else "stopped"), age_s


def _partition_incidents(failing: dict[str, dict], indexer: CodeIndexer, services: dict[str, str], now: datetime) -> list[dict]:
    """One incident per connected component of the failing-services subgraph, as
    before (real dependency edges, failing<->failing pairs only -- unrelated
    faults are never merged). Within a component, candidates are now split into
    COMPETITORS (could plausibly be the cause) and MINOR ones (too weak to
    seriously compete), per CONFIG's floor: a candidate must clear both
    MIN_COMPETITOR_ERRORS (absolute) and MIN_COMPETITOR_SHARE of the strongest
    candidate's weighted_errors (relative) to count as a competitor. The
    strongest candidate is always root and always counts as a competitor, even
    if it's individually weak (that's what `is_minor` on the primary records
    instead). Everything that fails the floor is split out into its own
    single-node "minor incident" -- reported separately, never folded into the
    primary's symptoms, and never affecting its dominance or label."""
    failing_ids = {services[n] for n in failing if n in services}
    id_to_name = {services[n]: n for n in failing if n in services}
    adj: dict[str, set[str]] = {sid: set() for sid in failing_ids}
    for sid in failing_ids:
        for callee in indexer.callees(sid) & failing_ids:
            adj[sid].add(callee)
            adj[callee].add(sid)

    seen: set[str] = set()
    incidents = []
    for start in failing_ids:
        if start in seen:
            continue
        comp: set[str] = set()
        stack = [start]
        while stack:
            n = stack.pop()
            if n in comp:
                continue
            comp.add(n)
            seen.add(n)
            stack.extend(adj[n] - comp)
        comp_names = {id_to_name[c] for c in comp}
        raw_candidates = sorted(
            (n for n in comp_names if not (indexer.callees(services[n]) & comp)),
            key=lambda n: (-_weighted(failing[n]), n),  # strongest first, ties broken by name
        )
        if not raw_candidates:
            activity, age_s = None, None
            incidents.append({
                "component_ids": comp, "failing_services": sorted(comp_names), "candidates": [],
                "root": None, "symptoms": sorted(comp_names), "label": "none",
                "root_errors": 0, "root_warns": 0, "is_minor": False,
                "activity": activity, "last_error_age_s": age_s,
            })
            continue

        root = raw_candidates[0]  # always the single strongest candidate, competitor or not
        strongest_w = _weighted(failing[root])
        competitors = [root]
        minor: list[str] = []
        for n in raw_candidates[1:]:
            w = _weighted(failing[n])
            if w >= CONFIG["MIN_COMPETITOR_ERRORS"] and w >= CONFIG["MIN_COMPETITOR_SHARE"] * strongest_w:
                competitors.append(n)
            else:
                minor.append(n)

        true_symptoms = sorted(n for n in comp_names if n not in raw_candidates)
        activity, age_s = _activity_of(failing[root], now)
        incidents.append({
            "component_ids": comp, "failing_services": sorted({root, *true_symptoms}),
            "candidates": competitors, "root": root, "symptoms": true_symptoms,
            "label": "single" if len(competitors) <= 1 else "ambiguous",
            "root_errors": failing[root]["errors"], "root_warns": failing[root]["warns"],
            "is_minor": strongest_w < CONFIG["MIN_COMPETITOR_ERRORS"],
            "activity": activity, "last_error_age_s": age_s,
        })
        for n in minor:
            n_activity, n_age = _activity_of(failing[n], now)
            incidents.append({
                "component_ids": {services[n]}, "failing_services": [n], "candidates": [n],
                "root": n, "symptoms": [], "label": "single",
                "root_errors": failing[n]["errors"], "root_warns": failing[n]["warns"], "is_minor": True,
                "activity": n_activity, "last_error_age_s": n_age,
            })
    # Primary incident = highest severity-weighted errors (errors + WARNING_WEIGHT*warnings,
    # summed over every service in the incident, not just the root), ties broken by root name.
    incidents.sort(key=lambda inc: (-sum(_weighted(failing[n]) for n in inc["failing_services"]), inc["root"] or ""))
    return incidents


def _incident_for(name: str, incidents: list[dict]) -> dict | None:
    for inc in incidents:
        if name in inc["failing_services"]:
            return inc
    return None


def _chain_to_root(start: str, root: str, incident: dict, indexer: CodeIndexer, services: dict[str, str]) -> list[str]:
    """SPECIFIC mode: the causal chain from the asked-about service down to the
    incident's root, following only real (currently-failing) dependency edges."""
    if start == root:
        return [start]
    comp_ids, start_id, root_id = incident["component_ids"], services[start], services[root]
    prev: dict[str, str | None] = {start_id: None}
    q = deque([start_id])
    while q:
        n = q.popleft()
        if n == root_id:
            break
        for nb in indexer.callees(n) & comp_ids:
            if nb not in prev:
                prev[nb] = n
                q.append(nb)
    if root_id not in prev:
        return []  # not reachable within this component (shouldn't happen; defensive)
    path_ids, cur = [], root_id
    while cur is not None:
        path_ids.append(cur)
        cur = prev[cur]
    path_ids.reverse()
    return [display_name(i) for i in path_ids]


def _incident_chain(incident: dict, indexer: CodeIndexer) -> list[str]:
    """GENERAL mode (no specific starting service): the chain is the incident's
    root's own path from a graph entry point, same concept as the old
    system-wide trace_path, just scoped to this one incident's root."""
    if not incident["root"]:
        return []
    return [display_name(s) for s in indexer.path_to(_root_id_of(incident, indexer))]


def _root_id_of(incident: dict, indexer: CodeIndexer) -> str:
    # incident["component_ids"] are internal ids; find the one matching root's display name
    for sid in incident["component_ids"]:
        if display_name(sid) == incident["root"]:
            return sid
    raise KeyError(incident["root"])


# =============================================================================
# 3) CONFIDENCE -- one function, used for every incident scored, in both modes.
#    Weights (0.4/0.25/0.35), the 0.65 threshold, and the grounding gate are
#    unchanged from Prompt 1. Two changes only: evidence now folds in warnings
#    (weighted_errors = errors + 0.25*warnings on the root), and dominance is
#    scoped to the candidates of the ONE incident being scored, not a global
#    count across the whole system. No logprob-based signal exists anywhere in
#    this pipeline, so there is nothing to remove there.
# =============================================================================
def _compute_confidence(root_errors: int, root_warns: int, num_candidates: int, top_relevance: float) -> dict:
    """num_candidates is the incident's (already floor-filtered) COMPETITOR count
    -- see _partition_incidents. Weights, threshold, and the grounding gate are
    unchanged. One addition: >1 competitor forces label "low" regardless of the
    numeric score (kept, not zeroed) -- several plausible causes competing is
    itself a reason to distrust "high", separate from what the weighted formula
    happens to compute."""
    relevance = round(max(0.0, min(top_relevance, 1.0)), 3)
    if num_candidates <= 0 or root_errors <= 0:
        return {"label": "low", "score": 0.0, "signals": {"evidence": 0.0, "dominance": 0.0, "relevance": relevance}}
    weighted_errors = root_errors + CONFIG["WARNING_WEIGHT"] * root_warns
    evidence = round(min(weighted_errors / CONFIG["EVIDENCE_DIVISOR"], 1.0), 3)
    dominance = round(1.0 / num_candidates, 3)
    score = round(CONFIG["WEIGHT_EVIDENCE"] * evidence + CONFIG["WEIGHT_RELEVANCE"] * relevance + CONFIG["WEIGHT_DOMINANCE"] * dominance, 3)
    label = "high" if score >= CONFIG["HIGH_THRESHOLD"] else "low"
    if num_candidates > 1:
        label = "low"
    return {"label": label, "score": score, "signals": {"evidence": evidence, "dominance": dominance, "relevance": relevance}}


def _fallback_narrative(incident: dict) -> str:
    root, candidates, symptoms, label = incident["root"], incident["candidates"], incident["symptoms"], incident["label"]
    if label == "single":
        tail = f" {', '.join(symptoms)} {'is' if len(symptoms) == 1 else 'are'} affected because {'it depends' if len(symptoms) == 1 else 'they depend'} on it." if symptoms else ""
        return f"{root} is the root cause.{tail}"
    if label == "ambiguous":
        tail = f" {', '.join(symptoms)} {'is' if len(symptoms) == 1 else 'are'} affected because {'it depends' if len(symptoms) == 1 else 'they depend'} on one or more of them." if symptoms else ""
        return f"{', '.join(candidates)} are failing independently, with no single common cause between them.{tail}"
    return "No service currently has real errors in the lookback window; there is nothing to diagnose."


def _narrative_ok(model_root_field: str, evidence_summary: str, incident: dict) -> bool:
    if incident["label"] == "none" or model_root_field not in incident["candidates"]:
        return False
    return model_root_field.lower() in (evidence_summary or "").lower()


# =============================================================================
# 4) RETRIEVAL QUERY -- built from the chosen root's own error evidence (error
#    codes, message templates, service name). Never from the question text.
#    Same function for general and specific modes.
# =============================================================================
def _build_retrieval_query(root_display: str, root_anomaly: dict | None) -> str:
    if not root_anomaly:
        return root_display or ""
    error_lines = [l for l in root_anomaly["lines"] if l.severity == "error"]
    sigs: dict[str, None] = {}
    for l in error_lines:
        sigs.setdefault(_signature(l.message), None)
    return (root_display + " " + " ".join(list(sigs)[:8])).strip()


def _boost_for(root_id: str | None, indexer: CodeIndexer) -> dict[str, float]:
    if root_id is None:
        return {}
    boost = {root_id: 1.6}
    for n in indexer.callees(root_id):
        boost[n] = max(boost.get(n, 1.0), 1.2)
    return boost


def _render_context(question, services, edges, anomalies, lines, chunks, stats, incident) -> str:
    out = [f"QUESTION: {question}", "", "SERVICES: " + ", ".join(sorted(services))]
    out.append("DEPENDENCIES (A -> B means A calls B): " + "; ".join(f"{display_name(a)} -> {display_name(b)}" for a, b in edges))
    out += ["", f"STATUS (last {WINDOW_S // 60} min):"]
    for svc, s in sorted(stats.items()):
        out.append(f"  {svc}: {s['errors']} errors, {s['warns']} warnings, {s['health']}")
    if not anomalies:
        out.append("  (no warnings or errors in the lookback window)")
    if incident["label"] == "single":
        out.append(f"  ROOT SERVICE (decided by the system, not you): {incident['root']}")
    elif incident["label"] == "ambiguous":
        out.append(f"  CANDIDATE SERVICES (decided by the system, not you -- pick whichever you can verify with code): {', '.join(incident['candidates'])}")
    if incident["symptoms"]:
        out.append(f"  SYMPTOM SERVICES (affected BY the root cause, never the cause themselves): {', '.join(incident['symptoms'])}")
    out += ["", "LOG LINES (id | time | severity | service | message):"]
    out += [f"  {l.id} | {l.to_dict()['time']} | {l.severity} | {l.service} | {l.message}" for l in lines]
    out += ["", "CODE CHUNKS:"]
    for i, ch in enumerate(chunks, 1):
        out.append(f"--- c{i} | service={display_name(ch.service)} | {ch.file}:{ch.start_line}-{ch.end_line} | {ch.name}")
        out += [f"{ch.start_line + j:>4}: {t}" for j, t in enumerate(ch.lines)]
    return "\n".join(out)


def _call_model(context: str) -> dict:
    # Env is read per call so .env changes apply after load_dotenv in main.py.
    url = os.environ.get("OLLAMA_URL", OLLAMA_URL).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", OLLAMA_MODEL)
    body = json.dumps({
        "model": model,
        "stream": False,
        "format": REPORT_TOOL["input_schema"],  # constrains output to the report schema
        "options": {"temperature": 0, "num_ctx": 16384},
        "messages": [
            {"role": "system", "content": SYSTEM + "\n\nRespond with a JSON object matching the report schema."},
            {"role": "user", "content": context},
        ],
    }).encode()
    req = urllib.request.Request(f"{url}/api/chat", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        if e.code == 404:
            raise QueryError(503, f"Ollama model {model!r} not found. Run: ollama pull {model}")
        raise QueryError(502, f"Ollama error {e.code}: {detail}")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise QueryError(503, f"Cannot reach Ollama at {url} ({getattr(e, 'reason', e)}). Start it with `ollama serve`.")
    try:
        report = json.loads(data["message"]["content"])
    except (KeyError, TypeError, ValueError):
        raise QueryError(502, "The model returned no structured report.")
    if not isinstance(report, dict):
        raise QueryError(502, "The model returned no structured report.")
    return report


def _score_incident(incident: dict, indexer: CodeIndexer, failing: dict) -> tuple[dict, list, float]:
    """Retrieval + confidence for one incident -- no LLM call. Used for every
    incident in the `incidents` list, including ones the model never explains.

    Boost still decides which chunk ranks #1 (ranking is unchanged -- that chunk
    is still the one shown and cited). Confidence, however, is fed the RAW,
    unboosted cosine similarity of that same top-ranked chunk: boost is derived
    from the same anomaly/graph signal the dominance signal already counts, so
    feeding the boosted score into confidence too would double-count it. The
    0..1 clamp in _compute_confidence is a no-op now (raw cosine similarity is
    already bounded to that range) -- kept only as a defensive safety net."""
    root_anomaly = failing.get(incident["root"]) if incident["root"] else None
    root_id = _root_id_of(incident, indexer) if incident["root"] else None
    query = _build_retrieval_query(incident["root"] or "", root_anomaly)
    boost = _boost_for(root_id, indexer)
    scored = indexer.search_scored(query, k=MAX_CHUNKS, boost=boost) if query else []
    top_boosted = scored[0][0] if scored else 0.0
    top_raw = scored[0][1] if scored else 0.0
    conf = _compute_confidence(incident["root_errors"], incident["root_warns"], len(incident["candidates"]), top_raw)
    return conf, scored, top_boosted


_EMPTY_INCIDENT = {
    "component_ids": set(), "failing_services": [], "candidates": [], "root": None,
    "symptoms": [], "label": "none", "root_errors": 0, "root_warns": 0,
    "is_minor": False, "activity": None, "last_error_age_s": None,
}


def _diagnose(question: str, anomalies: list[dict], indexer: CodeIndexer, services: dict[str, str], now: datetime | None = None) -> dict:
    """Pure code, no LLM, no HTTP: routes the question, partitions the currently
    failing services into incidents, and scores every one of them (retrieval +
    confidence). This is the entire deterministic core of the pipeline --
    run_query() below just adds the one LLM call (for the incident actually
    being answered) and response formatting on top. Also the thing
    backend/eval tests call directly, so they exercise the real
    routing/scoping/confidence/activity logic with zero LLM calls. `now` is the
    activity reference time -- passed explicitly so a fixture with fixed
    timestamps doesn't read as "stopped for days" just because real wall-clock
    time has moved on since it was written; defaults to datetime.now()."""
    now = now or datetime.now()
    route = _route_question(question, services)
    mode, target = route["mode"], route["target"]

    failing = {a["service"]: a for a in anomalies if a["errors"] > 0}
    incidents = _partition_incidents(failing, indexer, services, now)

    confidences: list[dict] = []
    chunks_lists: list[list] = []
    boosted_scores: list[float] = []
    for inc in incidents:
        conf, scored, top_boosted = _score_incident(inc, indexer, failing)
        confidences.append(conf)
        chunks_lists.append(scored)
        boosted_scores.append(top_boosted)

    answer_type = "incident"
    chain: list[str] = []
    primary_idx: int | None = None

    if mode == "unknown_service":
        answer_type = "unknown_service"
    elif mode == "specific":
        if target not in failing:
            answer_type = "healthy"
        else:
            inc = _incident_for(target, incidents)
            primary_idx = incidents.index(inc)
            chain = [target] if target == inc["root"] else (_chain_to_root(target, inc["root"], inc, indexer, services) if inc["label"] == "single" else [])
    else:  # general
        if incidents:
            primary_idx = 0
            chain = _incident_chain(incidents[0], indexer)
        else:
            answer_type = "healthy"

    return {
        "mode": mode, "target": target, "answer_type": answer_type,
        "incidents": incidents, "confidences": confidences, "chunks_lists": chunks_lists,
        "boosted_scores": boosted_scores, "primary_idx": primary_idx, "chain": chain, "failing": failing,
    }


def run_query(question: str, logs: LogAnalyzer, indexer: CodeIndexer) -> dict:
    now = datetime.now()
    services = _service_ids(indexer)  # display -> id
    _, edges = indexer.graph()
    stats = logs.stats(now)
    anomalies, lines = _bundle(logs, indexer, now)

    d = _diagnose(question, anomalies, indexer, services, now)
    mode, target, answer_type = d["mode"], d["target"], d["answer_type"]
    incidents, chain, primary_idx = d["incidents"], d["chain"], d["primary_idx"]

    primary = incidents[primary_idx] if primary_idx is not None else dict(_EMPTY_INCIDENT)
    primary_conf = d["confidences"][primary_idx] if primary_idx is not None else _compute_confidence(0, 0, 0, 0.0)
    primary_chunks = [ch for _, _, ch in d["chunks_lists"][primary_idx]] if primary_idx is not None else []
    primary_boosted = d["boosted_scores"][primary_idx] if primary_idx is not None else 0.0

    # ---- call the model ONLY for the one incident actually being answered --
    if answer_type == "incident" and primary["root"]:
        ctx = _render_context(question, list(services), edges, anomalies, lines, primary_chunks, stats, primary)
        r = _call_model(ctx)
    else:
        r = {}

    line_by_id = {l.id: l for l in lines}
    chunk_by_id = {f"c{i}": ch for i, ch in enumerate(primary_chunks, 1)}

    model_root_field = r.get("root_service", "")
    evidence_summary = r.get("evidence_summary", "")
    narrative_ok = _narrative_ok(model_root_field, evidence_summary, primary) if r else False
    if answer_type == "healthy":
        final_summary = (f"No errors in {target} in the last 5 minutes." if mode == "specific"
                          else "No service currently has real errors in the lookback window; there is nothing to diagnose.")
    elif answer_type == "unknown_service":
        final_summary = f"No service with that name ({target!r}) in this system."
    else:
        final_summary = evidence_summary if narrative_ok else _fallback_narrative(primary)

    evidence_ids = [i for i in dict.fromkeys(r.get("evidence_log_ids", [])) if i in line_by_id] if r else []
    chunk = chunk_by_id.get(r.get("code_chunk_id", "")) if r else None
    chunk_matches_root = chunk is not None and primary["label"] == "single" and display_name(chunk.service) == primary["root"]
    fix_lines = [
        {"kind": f["kind"], "text": f["text"]} for f in (r.get("fix") or [])
        if f.get("kind") in ("add", "remove", "context") and isinstance(f.get("text"), str)
    ] if r else []
    chunk_text = {t.strip() for t in chunk.lines} if chunk else set()
    fix_valid = chunk_matches_root and fix_lines and all(f["kind"] == "add" or f["text"].strip() in chunk_text for f in fix_lines)

    has_incident = primary["label"] != "none" and answer_type == "incident"
    root_display = primary["root"]
    root_id = services[root_display] if root_display else None
    trace_path = [display_name(s) for s in indexer.path_to(root_id)] if root_id else []
    affected_ids = (indexer.callers(root_id) | indexer.callees(root_id)) - {root_id} if root_id else set()
    affected = []
    for sid in sorted(affected_ids, key=lambda s: (s not in indexer.callers(root_id), s)):
        dname = display_name(sid)
        s = stats.get(dname, {"errors": 0, "warns": 0, "health": "healthy"})
        rel = "calls" if sid in indexer.callers(root_id) else "called by"
        note = (f"{s['errors']} errors, {s['warns']} warnings in last {WINDOW_S // 60}m"
                if s["errors"] or s["warns"] else f"no errors in window; {rel} {root_display}")
        affected.append({"id": dname, "name": dname, "health": s["health"], "note": note})

    root_lines = next((a["lines"] for a in anomalies if a["service"] == root_display), [])
    root_errors_lines = [l for l in root_lines if l.severity == "error"]
    timeline = []
    if root_lines:
        timeline.append({"time": root_lines[0].to_dict()["time"][:8], "label": "First anomaly", "severity": "warn" if root_lines[0].severity == "warn" else "error"})
    if root_errors_lines and (not root_lines or root_errors_lines[0].id != root_lines[0].id):
        timeline.append({"time": root_errors_lines[0].to_dict()["time"][:8], "label": "Escalated", "severity": "error"})
    timeline.append({
        "time": now.strftime("%H:%M:%S"),
        "label": {"single": "Root cause identified", "ambiguous": "Anomaly detected"}.get(primary["label"], "Investigation closed"),
        "severity": "info",
    })

    rs = stats.get(root_display, {"errors": 0, "warns": 0}) if root_display else {"errors": 0, "warns": 0}
    cited = [line_by_id[i] for i in evidence_ids]
    stat_list = [
        {"label": "Errors (5m)", "value": f"{rs['errors']:,}", "tone": "critical" if rs["errors"] else None, "sourceLogIds": [root_errors_lines[-1].id] if root_errors_lines else evidence_ids[:1]},
        {"label": "Warnings (5m)", "value": f"{rs['warns']:,}", "sourceLogIds": [next((l.id for l in reversed(root_lines) if l.severity == "warn"), (evidence_ids or [None])[0])]},
        {"label": "First seen", "value": root_lines[0].to_dict()["time"][:8] if root_lines else "—", "sourceLogIds": [root_lines[0].id] if root_lines else []},
        {"label": "Services touched", "value": str(len(affected) + 1 if has_incident else 0), "sourceLogIds": evidence_ids[:1]},
    ]
    for s_ in stat_list:
        s_["sourceLogIds"] = [i for i in s_["sourceLogIds"] if i]
    stat_list = [{k: v for k, v in s_.items() if v is not None} for s_ in stat_list]

    node_details = {}
    for nd in (r.get("node_details") or []) if r else []:
        svc, ch = nd.get("service"), chunk_by_id.get(nd.get("code_chunk_id", ""))
        if svc not in services or ch is None:
            continue
        matches = [
            {"logId": m["log_id"], "lineIndex": m["line_offset"]}
            for m in nd.get("matches", [])
            if m.get("log_id") in line_by_id and isinstance(m.get("line_offset"), int) and 0 <= m["line_offset"] < len(ch.lines)
        ]
        node_details[svc] = {"bridge": nd.get("bridge", ""), "filename": ch.file, "startLine": ch.start_line, "lines": ch.lines, "matches": matches}

    if primary["label"] == "single" and answer_type == "incident":
        root_cause_label = r.get("root_cause_line") if (r and r.get("root_cause_line")) else (
            f"{root_display} · {r.get('root_cause_function', '')} {r.get('failure_type', '')}".strip(" ·") if narrative_ok and root_display else final_summary
        )
    elif has_incident:
        root_cause_label = f"{root_display} · anomaly detected (diagnosis unconfirmed)"
    else:
        root_cause_label = ""

    # SPECIFIC + found -> only that one incident (asking about payment-service never
    # surfaces an unrelated notify-worker incident just because both happen to be
    # failing). GENERAL, and SPECIFIC + healthy (nothing to scope down to, and section
    # 2 says other failures should still be mentioned separately) -> every incident.
    # unknown_service -> nothing to list.
    if mode == "specific" and answer_type == "incident":
        source = [(primary_idx, incidents[primary_idx])]
    elif mode == "unknown_service":
        source = []
    else:
        source = list(enumerate(incidents))

    incidents_out = []
    for i, inc in source:
        conf = d["confidences"][i]
        inc_chain = chain if i == primary_idx and mode == "specific" else _incident_chain(inc, indexer)
        incidents_out.append({
            "root": inc["root"], "candidates": inc["candidates"], "symptoms": inc["symptoms"],
            "chain": inc_chain, "root_errors": inc["root_errors"], "label": inc["label"],
            "score": conf["score"], "confidence_label": conf["label"], "signals": conf["signals"],
            "raw_relevance": conf["signals"]["relevance"], "boosted_score": round(d["boosted_scores"][i], 3),
            "is_minor": inc["is_minor"], "activity": inc["activity"], "last_error_age_s": inc["last_error_age_s"],
        })

    diagnosis_block = {
        "failing_services": primary["failing_services"], "root": primary["root"], "candidates": primary["candidates"],
        "symptoms": primary["symptoms"], "root_errors": primary["root_errors"], "label": primary["label"],
        "confidence_label": primary_conf["label"], "score": primary_conf["score"], "signals": primary_conf["signals"],
        # raw_relevance is the same (clamped) raw cosine already in signals["relevance"] --
        # surfaced again under its own name so a calculation table can show it next to
        # boosted_score without digging into signals. boosted_score is NOT part of the
        # confidence calculation (see _score_incident) -- it's what ranking used to pick
        # the top hit, kept here only for comparison/display.
        "raw_relevance": primary_conf["signals"]["relevance"], "boosted_score": round(primary_boosted, 3),
        "is_minor": primary["is_minor"], "activity": primary["activity"], "last_error_age_s": primary["last_error_age_s"],
        "config": CONFIG,
    }
    print("[ARGUS diagnosis] " + json.dumps({
        "mode": mode, "target": target, "answer_type": answer_type,
        **diagnosis_block, "narrative_ok": narrative_ok, "model_named": model_root_field,
        "num_incidents": len(incidents),
    }, indent=2))

    return {
        "question": question,
        "mode": mode,
        "target": target,
        "answer_type": answer_type,
        "summary": final_summary,
        "confident_cause_found": primary["label"] == "single" and answer_type == "incident",
        "has_incident": has_incident,
        "confidence": primary_conf["label"],
        "root_cause": root_cause_label,
        "root_cause_service": root_display or "",
        "root_cause_function": r.get("root_cause_function", "") if narrative_ok else "",
        "failure_type": r.get("failure_type", "") if narrative_ok else "",
        "evidence_logs": [l.to_dict() for l in cited],
        "relevant_code": {"filename": chunk.file, "start_line": chunk.start_line, "lines": chunk.lines} if fix_valid or chunk_matches_root else None,
        "recommended_fix": {"filename": chunk.file, "lines": fix_lines} if fix_valid else None,
        "ruled_out": "" if primary["label"] == "single" else _fallback_narrative(primary),
        "trace_path": trace_path,
        "node_ids": list(dict.fromkeys(trace_path + [a["service"] for a in anomalies])),
        "affected_nodes": affected,
        "timeline": timeline,
        "stats": stat_list,
        "node_details": node_details,
        "incidents": incidents_out,
        "diagnosis": diagnosis_block,  # backward-compat: primary incident, same shape as Prompt 1
    }
