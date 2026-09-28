"""POST /query pipeline:

  Log Analyzer (current anomalies)
    -> deterministic root-cause classification (plain code, dependency graph)
    -> Code Indexer (retrieval, for citing code + a relevance signal)
    -> bundle context
    -> local Ollama model (schema-constrained JSON = explanation text only)
    -> validate the model's text against what the code already decided
    -> response

The model never chooses the diagnosis. WHICH service is the root cause is
decided entirely by _classify_incident() below, from real error counts and the
real dependency graph -- the model cannot override it, and its own self-rated
confidence is never consulted. The model's only job is to write the
explanation, and even that is checked afterward: if its text doesn't name the
code-chosen root (or claims a symptom is the cause), the text is discarded and
a deterministic fallback sentence is used instead. Confidence is likewise
computed from measurable signals (see compute_confidence), never asked of the
model. Evidence ids must exist in the bundle, the service must be in the
graph, code chunks come from disk, and trace path / blast radius / timeline /
stats are derived from the graph and logs, never from the model.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime

from code_indexer import CodeIndexer, display_name
from log_analyzer import LogAnalyzer, WINDOW_S

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "180"))
MAX_LOG_LINES = 90
MAX_CHUNKS = 6


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


def _bundle(question: str, logs: LogAnalyzer, indexer: CodeIndexer, now: datetime):
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

    boost: dict[str, float] = {}
    for a in anomalies:
        sid = a["service"].replace("-", "_")
        boost[sid] = boost.get(sid, 1.0) * 1.6
        for n in indexer.callees(sid):
            boost[n] = max(boost.get(n, 1.0), 1.2)
    query = question + " " + " ".join(l.message for a in anomalies for l in a["lines"][-6:])
    return anomalies, lines, boost, query


def _classify_incident(anomalies: list[dict], indexer: CodeIndexer, services: dict[str, str]) -> dict:
    """Part A: deterministic root-cause selection. Plain code, no LLM involved --
    this is the ONLY place that decides which service is the root cause; nothing
    downstream (including the model) is allowed to change it.

    failing_services: every service with real errors (>0) in the last 5 min.
    A failing service is a ROOT CANDIDATE only if none of its own dependencies
    (callees -- what it calls) are ALSO failing: it's the bottom of the failure
    chain, not just inheriting an error from something downstream of it.
    Everything else failing is a SYMPTOM of some candidate.

    - Exactly one candidate -> that's the root cause (label "single").
    - Several unrelated candidates -> ambiguous: no single root, list them all
      (label "ambiguous"; `root` is still set, to the earliest one, so the graph
      has somewhere to point, but confidence is capped low by compute_confidence
      regardless -- see the dominance signal).
    - No candidates (nothing failing, or every failing service's failure chain
      loops back on itself) -> label "none", root is None, and the graph stays
      fully neutral.
    """
    failing = [a for a in anomalies if a["errors"] > 0]
    by_name = {a["service"]: a for a in failing}
    failing_ids = {services[a["service"]] for a in failing if a["service"] in services}

    def is_candidate(a: dict) -> bool:
        sid = services.get(a["service"])
        return sid is not None and not (indexer.callees(sid) & failing_ids)

    candidates = [a["service"] for a in failing if is_candidate(a)]
    candidates.sort(key=lambda n: by_name[n]["first_error"] or by_name[n]["first_seen"])

    if len(candidates) == 1:
        label = "single"
    elif len(candidates) > 1:
        label = "ambiguous"
    else:
        label = "none"
    root = candidates[0] if candidates else None
    symptoms = [a["service"] for a in failing if a["service"] not in candidates]

    return {
        "failing_services": [a["service"] for a in failing],
        "candidates": candidates,
        "root": root,
        "symptoms": symptoms,
        "root_errors": by_name[root]["errors"] if root else 0,
        "label": label,
    }


def _compute_confidence(diag: dict, top_relevance: float) -> dict:
    """Part B: confidence computed entirely from measurable signals -- never from
    the model's own self-report, which (see wip-validation notes) doesn't
    reliably track actual evidence strength: it flipped between runs on
    identical-shaped data, and separately stayed "low" on textbook-clear
    cascading failures because the model second-guessed a correct code-chosen
    root. Removing it from the decision fixes both.

    - Grounding gate: no root (label "none"), or the root somehow has zero
      errors, forces low/0 -- there is nothing to be confident ABOUT.
    - evidence: min(root_errors / 20, 1.0) -- more corroborating error lines
      from the root itself, more confidence, capped so one very noisy service
      can't alone max this out.
    - relevance: the top TF-IDF retrieval score this query got (post-boost,
      clamped to 0..1) -- how well the retrieved code actually matches the
      failure signature. A relevance score, not a probability of correctness.
    - dominance: 1.0 with exactly one root candidate, 1/N with N unrelated
      candidates (more ambiguity, less confidence), 0 with none.
    Weighted 0.4 evidence + 0.25 relevance + 0.35 dominance (dominance weighted
    heaviest: whether we structurally know WHO is responsible matters more
    than how many lines happen to be in the log window). >= 0.65 -> high.
    """
    relevance = round(max(0.0, min(top_relevance, 1.0)), 3)
    if diag["label"] == "none" or diag["root"] is None or diag["root_errors"] <= 0:
        return {"label": "low", "score": 0.0, "signals": {"evidence": 0.0, "dominance": 0.0, "relevance": relevance}}
    evidence = round(min(diag["root_errors"] / 20.0, 1.0), 3)
    dominance = round(1.0 / len(diag["candidates"]), 3) if diag["candidates"] else 0.0
    score = round(0.4 * evidence + 0.25 * relevance + 0.35 * dominance, 3)
    return {"label": "high" if score >= 0.65 else "low", "score": score, "signals": {"evidence": evidence, "dominance": dominance, "relevance": relevance}}


def _fallback_narrative(diag: dict) -> str:
    """The deterministic sentence used whenever the model's own text fails
    validation (see _narrative_ok) -- or always, for label "none", since there's
    nothing for the model to legitimately narrate there."""
    root, candidates, symptoms, label = diag["root"], diag["candidates"], diag["symptoms"], diag["label"]
    if label == "single":
        tail = f" {', '.join(symptoms)} {'is' if len(symptoms) == 1 else 'are'} affected because {'it depends' if len(symptoms) == 1 else 'they depend'} on it." if symptoms else ""
        return f"{root} is the root cause.{tail}"
    if label == "ambiguous":
        tail = f" {', '.join(symptoms)} {'is' if len(symptoms) == 1 else 'are'} affected because {'it depends' if len(symptoms) == 1 else 'they depend'} on one or more of them." if symptoms else ""
        return f"{', '.join(candidates)} are failing independently, with no single common cause between them.{tail}"
    return "No service currently has real errors in the lookback window; there is nothing to diagnose."


def _narrative_ok(model_root_field: str, evidence_summary: str, diag: dict) -> bool:
    """The model's text is trusted only if BOTH hold: its own root_service field
    names one of the code-chosen candidates (never a symptom, never something
    invented), AND its prose actually names that service. label "none" has no
    legitimate candidate to name, so it never passes -- _fallback_narrative's
    fixed sentence is used unconditionally there."""
    if diag["label"] == "none" or model_root_field not in diag["candidates"]:
        return False
    return model_root_field.lower() in (evidence_summary or "").lower()


def _render_context(question, services, edges, anomalies, lines, chunks, stats, diag) -> str:
    out = [f"QUESTION: {question}", "", "SERVICES: " + ", ".join(sorted(services))]
    out.append("DEPENDENCIES (A -> B means A calls B): " + "; ".join(f"{display_name(a)} -> {display_name(b)}" for a, b in edges))
    out += ["", f"STATUS (last {WINDOW_S // 60} min):"]
    for svc, s in sorted(stats.items()):
        out.append(f"  {svc}: {s['errors']} errors, {s['warns']} warnings, {s['health']}")
    if not anomalies:
        out.append("  (no warnings or errors in the lookback window)")
    if diag["label"] == "single":
        out.append(f"  ROOT SERVICE (decided by the system, not you): {diag['root']}")
    elif diag["label"] == "ambiguous":
        out.append(f"  CANDIDATE SERVICES (decided by the system, not you -- pick whichever you can verify with code): {', '.join(diag['candidates'])}")
    if diag["symptoms"]:
        out.append(f"  SYMPTOM SERVICES (affected BY the root cause, never the cause themselves): {', '.join(diag['symptoms'])}")
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


def run_query(question: str, logs: LogAnalyzer, indexer: CodeIndexer) -> dict:
    now = datetime.now()
    services = _service_ids(indexer)  # display -> id
    _, edges = indexer.graph()
    stats = logs.stats(now)
    anomalies, lines, boost, retrieval_query = _bundle(question, logs, indexer, now)

    # ---- A: decide the root cause, in code, before the model ever runs ----
    diag = _classify_incident(anomalies, indexer, services)

    # Retrieval happens after classification (not before) so the top score used by
    # compute_confidence's relevance signal, and the chunks shown to the model, can be
    # boosted toward whatever the classifier actually picked as well as any other
    # anomalous service -- boost itself is unchanged (still keyed off all anomalies).
    scored_chunks = indexer.search_scored(retrieval_query, k=MAX_CHUNKS, boost=boost)
    chunks = [ch for _, ch in scored_chunks]
    top_relevance = scored_chunks[0][0] if scored_chunks else 0.0

    ctx = _render_context(question, list(services), edges, anomalies, lines, chunks, stats, diag)
    r = _call_model(ctx)

    line_by_id = {l.id: l for l in lines}
    chunk_by_id = {f"c{i}": ch for i, ch in enumerate(chunks, 1)}

    # ---- validate the model's TEXT only -- it cannot change the root ----
    model_root_field = r.get("root_service", "")
    evidence_summary = r.get("evidence_summary", "")
    narrative_ok = _narrative_ok(model_root_field, evidence_summary, diag)
    final_summary = evidence_summary if narrative_ok else _fallback_narrative(diag)

    evidence_ids = [i for i in dict.fromkeys(r.get("evidence_log_ids", [])) if i in line_by_id]
    chunk = chunk_by_id.get(r.get("code_chunk_id", ""))
    # Code/fix are only ever surfaced for a clean single root, and only when the
    # model's own citation actually belongs to that root's service -- otherwise we'd be
    # showing "relevant code" for a service nobody decided was responsible.
    chunk_matches_root = chunk is not None and diag["label"] == "single" and display_name(chunk.service) == diag["root"]
    fix_lines = [
        {"kind": f["kind"], "text": f["text"]} for f in (r.get("fix") or [])
        if f.get("kind") in ("add", "remove", "context") and isinstance(f.get("text"), str)
    ]
    chunk_text = {t.strip() for t in chunk.lines} if chunk else set()
    fix_valid = chunk_matches_root and fix_lines and all(f["kind"] == "add" or f["text"].strip() in chunk_text for f in fix_lines)

    # ---- B: confidence, computed, never asked of the model ----
    confidence = _compute_confidence(diag, top_relevance)

    # ---- C: everything that explains the decision -- returned AND printed ----
    print(
        "[ARGUS diagnosis] "
        + json.dumps({
            "failing_services": diag["failing_services"], "root": diag["root"], "candidates": diag["candidates"],
            "symptoms": diag["symptoms"], "root_errors": diag["root_errors"], "label": diag["label"],
            "confidence_label": confidence["label"], "confidence_score": confidence["score"], "signals": confidence["signals"],
            "narrative_ok": narrative_ok, "model_named": model_root_field,
        }, indent=2)
    )

    has_incident = diag["label"] != "none"
    root_display = diag["root"]  # None only when label == "none"

    # ---- computed (not model-provided) graph fields ----
    root_id = services[root_display] if root_display else None
    trace_path = [display_name(s) for s in indexer.path_to(root_id)] if root_id else []
    affected_ids = (indexer.callers(root_id) | indexer.callees(root_id)) - {root_id} if root_id else set()
    affected = []
    for sid in sorted(affected_ids, key=lambda s: (s not in indexer.callers(root_id), s)):
        d = display_name(sid)
        s = stats.get(d, {"errors": 0, "warns": 0, "health": "healthy"})
        rel = "calls" if sid in indexer.callers(root_id) else "called by"
        note = (f"{s['errors']} errors, {s['warns']} warnings in last {WINDOW_S // 60}m"
                if s["errors"] or s["warns"] else f"no errors in window; {rel} {root_display}")
        affected.append({"id": d, "name": d, "health": s["health"], "note": note})

    root_lines = next((a["lines"] for a in anomalies if a["service"] == root_display), [])
    root_errors = [l for l in root_lines if l.severity == "error"]
    timeline = []
    if root_lines:
        timeline.append({"time": root_lines[0].to_dict()["time"][:8], "label": "First anomaly", "severity": "warn" if root_lines[0].severity == "warn" else "error"})
    if root_errors and (not root_lines or root_errors[0].id != root_lines[0].id):
        timeline.append({"time": root_errors[0].to_dict()["time"][:8], "label": "Escalated", "severity": "error"})
    timeline.append({
        "time": now.strftime("%H:%M:%S"),
        "label": {"single": "Root cause identified", "ambiguous": "Anomaly detected"}.get(diag["label"], "Investigation closed"),
        "severity": "info",
    })

    rs = stats.get(root_display, {"errors": 0, "warns": 0}) if root_display else {"errors": 0, "warns": 0}
    cited = [line_by_id[i] for i in evidence_ids]
    stat_list = [
        {"label": "Errors (5m)", "value": f"{rs['errors']:,}", "tone": "critical" if rs["errors"] else None, "sourceLogIds": [root_errors[-1].id] if root_errors else evidence_ids[:1]},
        {"label": "Warnings (5m)", "value": f"{rs['warns']:,}", "sourceLogIds": [next((l.id for l in reversed(root_lines) if l.severity == "warn"), (evidence_ids or [None])[0])]},
        {"label": "First seen", "value": root_lines[0].to_dict()["time"][:8] if root_lines else "—", "sourceLogIds": [root_lines[0].id] if root_lines else []},
        {"label": "Services touched", "value": str(len(affected) + 1 if has_incident else 0), "sourceLogIds": evidence_ids[:1]},
    ]
    for s_ in stat_list:
        s_["sourceLogIds"] = [i for i in s_["sourceLogIds"] if i]
    stat_list = [{k: v for k, v in s_.items() if v is not None} for s_ in stat_list]

    node_details = {}
    for nd in r.get("node_details") or []:
        svc, ch = nd.get("service"), chunk_by_id.get(nd.get("code_chunk_id", ""))
        if svc not in services or ch is None:
            continue
        matches = [
            {"logId": m["log_id"], "lineIndex": m["line_offset"]}
            for m in nd.get("matches", [])
            if m.get("log_id") in line_by_id and isinstance(m.get("line_offset"), int) and 0 <= m["line_offset"] < len(ch.lines)
        ]
        node_details[svc] = {"bridge": nd.get("bridge", ""), "filename": ch.file, "startLine": ch.start_line, "lines": ch.lines, "matches": matches}

    return {
        "question": question,
        "summary": final_summary,
        "confident_cause_found": diag["label"] == "single",
        "has_incident": has_incident,
        "confidence": confidence["label"],
        "root_cause": (f"{root_display} · {r.get('root_cause_function', '')} {r.get('failure_type', '')}".strip(" ·")
                       if narrative_ok and root_display else final_summary if root_display else ""),
        "root_cause_service": root_display or "",
        "root_cause_function": r.get("root_cause_function", "") if narrative_ok else "",
        "failure_type": r.get("failure_type", "") if narrative_ok else "",
        "evidence_logs": [l.to_dict() for l in cited],
        "relevant_code": {"filename": chunk.file, "start_line": chunk.start_line, "lines": chunk.lines} if fix_valid or chunk_matches_root else None,
        "recommended_fix": {"filename": chunk.file, "lines": fix_lines} if fix_valid else None,
        "ruled_out": "" if diag["label"] == "single" else _fallback_narrative(diag),
        "trace_path": trace_path,
        "node_ids": list(dict.fromkeys(trace_path + [a["service"] for a in anomalies])),
        "affected_nodes": affected,
        "timeline": timeline,
        "stats": stat_list,
        "node_details": node_details,
        "diagnosis": {  # Part C -- everything the decision was based on, for inspection
            "failing_services": diag["failing_services"], "root": diag["root"], "candidates": diag["candidates"],
            "symptoms": diag["symptoms"], "root_errors": diag["root_errors"], "label": diag["label"],
            "confidence_label": confidence["label"], "score": confidence["score"], "signals": confidence["signals"],
        },
    }
