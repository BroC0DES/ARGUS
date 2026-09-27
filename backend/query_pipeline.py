"""POST /query pipeline:

  Log Analyzer (current anomalies)
    -> Code Indexer (retrieval + dependency graph)
    -> bundle context
    -> local Ollama model (schema-constrained JSON = structured report)
    -> validate against what was actually computed this request
    -> response

The model chooses the diagnosis. Everything checkable is checked or computed
here: evidence ids must exist in the bundle, the service must be in the graph,
code chunks come from disk, and trace path / blast radius / timeline / stats are
derived from the graph and logs, never from the model.
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
    "description": "Report the result of the investigation. Cite only ids that appear in the provided context.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "description": "ONE plain-language sentence that directly answers the engineer's question, stated as fact. No hedging words."},
            "confident_cause_found": {"type": "boolean", "description": "True only if the logs and code together clearly identify one root cause. False if the signal is weak, contradictory, or absent."},
            "confidence": {"type": "string", "enum": ["high", "low"]},
            "root_cause_service": {"type": "string", "description": "Exact service name from the services list. Best candidate even when not confident."},
            "root_cause_function": {"type": "string", "description": "Function name, e.g. charge_card()"},
            "failure_type": {"type": "string", "description": "One or two words, e.g. 'timeout', 'pool exhaustion'"},
            "root_cause_line": {"type": "string", "description": "Short label like 'payment-service · charge() gateway timeout'"},
            "evidence_log_ids": {"type": "array", "items": {"type": "string"}, "description": "Ids of the log lines that prove the diagnosis (or, if not confident, the lines that were reviewed)."},
            "code_chunk_id": {"type": "string", "description": "Id of the code chunk where the cause lives. Omit if not confident."},
            "fix": {
                "type": "array",
                "description": "Diff against the chunk: each line has kind remove|add|context. 'remove' and 'context' lines must be copied verbatim from the chunk.",
                "items": {"type": "object", "properties": {"kind": {"type": "string", "enum": ["remove", "add", "context"]}, "text": {"type": "string"}}, "required": ["kind", "text"]},
            },
            "ruled_out": {"type": "string", "description": "If not confident: what was checked and why no candidate cleared the bar, 1-2 sentences. Else empty."},
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
        "required": ["answer", "confident_cause_found", "confidence", "root_cause_service", "evidence_log_ids"],
    },
}

SYSTEM = """You are ARGUS, an incident investigation agent. You are given live log lines, the service dependency graph, and code retrieved from the indexed repository. Diagnose using ONLY that context.

Rules:
- Answer the engineer's actual question; if it concerns a specific service or symptom, scope the investigation to it.
- Cite only log ids and code chunk ids that appear in the context. Never invent ids, functions, or numbers.
- A cause is confident only when specific log lines AND specific code line(s) support it. If the evidence is thin, ambiguous, or the logs look healthy, set confident_cause_found=false, confidence=low, and explain in ruled_out what you checked.
- Symptoms propagate up the dependency graph: an upstream caller's errors often come from a downstream dependency. Prefer the deepest service whose own code produced the error.
- For fixes, copy 'remove' and 'context' lines verbatim from the chunk; keep the diff minimal.
- State findings as facts, no hedging words like 'possibly'. Uncertainty is expressed only through confidence."""


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
    chunks = indexer.search(query, k=MAX_CHUNKS, boost=boost)
    return anomalies, lines, chunks


def _render_context(question, services, edges, anomalies, lines, chunks, stats) -> str:
    out = [f"QUESTION: {question}", "", "SERVICES: " + ", ".join(sorted(services))]
    out.append("DEPENDENCIES (A -> B means A calls B): " + "; ".join(f"{display_name(a)} -> {display_name(b)}" for a, b in edges))
    out += ["", f"STATUS (last {WINDOW_S // 60} min):"]
    for svc, s in sorted(stats.items()):
        out.append(f"  {svc}: {s['errors']} errors, {s['warns']} warnings, {s['health']}")
    if not anomalies:
        out.append("  (no warnings or errors in the lookback window)")
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
    anomalies, lines, chunks = _bundle(question, logs, indexer, now)
    ctx = _render_context(question, list(services), edges, anomalies, lines, chunks, stats)
    r = _call_model(ctx)

    line_by_id = {l.id: l for l in lines}
    chunk_by_id = {f"c{i}": ch for i, ch in enumerate(chunks, 1)}

    # ---- validate the model's claims against what was computed this request ----
    root_display = r.get("root_cause_service", "")
    if root_display not in services:
        raise QueryError(502, f"The model named an unknown service: {root_display!r}.")
    evidence_ids = [i for i in dict.fromkeys(r.get("evidence_log_ids", [])) if i in line_by_id]
    chunk = chunk_by_id.get(r.get("code_chunk_id", ""))
    confident = bool(r.get("confident_cause_found")) and bool(evidence_ids) and chunk is not None
    confidence = "high" if confident and r.get("confidence") == "high" else "low"
    if chunk is not None and display_name(chunk.service) != root_display and confident:
        confidence = "low"  # cited code isn't in the service blamed
    fix_lines = [
        {"kind": f["kind"], "text": f["text"]} for f in (r.get("fix") or [])
        if f.get("kind") in ("add", "remove", "context") and isinstance(f.get("text"), str)
    ]
    chunk_text = {t.strip() for t in chunk.lines} if chunk else set()
    if confident and any(f["kind"] != "add" and f["text"].strip() not in chunk_text for f in fix_lines):
        confidence = "low"  # fix claims to edit code that isn't in the chunk

    # ---- computed (not model-provided) fields ----
    root_id = services[root_display]
    trace_path = [display_name(s) for s in indexer.path_to(root_id)]
    affected_ids = (indexer.callers(root_id) | indexer.callees(root_id)) - {root_id} if confident else set()
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
    timeline.append({"time": now.strftime("%H:%M:%S"), "label": "Root cause identified" if confident else "Investigation closed", "severity": "info"})

    rs = stats.get(root_display, {"errors": 0, "warns": 0})
    cited = [line_by_id[i] for i in evidence_ids]
    stat_list = [
        {"label": "Errors (5m)", "value": f"{rs['errors']:,}", "tone": "critical" if rs["errors"] else None, "sourceLogIds": [root_errors[-1].id] if root_errors else evidence_ids[:1]},
        {"label": "Warnings (5m)", "value": f"{rs['warns']:,}", "sourceLogIds": [next((l.id for l in reversed(root_lines) if l.severity == "warn"), (evidence_ids or [None])[0])]},
        {"label": "First seen", "value": root_lines[0].to_dict()["time"][:8] if root_lines else "—", "sourceLogIds": [root_lines[0].id] if root_lines else []},
        {"label": "Services touched", "value": str(len(affected) + 1 if confident else len(anomalies)), "sourceLogIds": evidence_ids[:1]},
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
        "summary": r.get("answer", ""),
        "confident_cause_found": confident,
        "confidence": confidence,
        "root_cause": r.get("root_cause_line") or f"{root_display} · {r.get('root_cause_function', '')} {r.get('failure_type', '')}".strip(),
        "root_cause_service": root_display,
        "root_cause_function": r.get("root_cause_function", ""),
        "failure_type": r.get("failure_type", ""),
        "evidence_logs": [l.to_dict() for l in cited],
        "relevant_code": {"filename": chunk.file, "start_line": chunk.start_line, "lines": chunk.lines} if chunk and confident else None,
        "recommended_fix": {"filename": chunk.file, "lines": fix_lines} if chunk and confident and fix_lines else None,
        "ruled_out": r.get("ruled_out", "") if not confident else "",
        "trace_path": trace_path,
        "node_ids": list(dict.fromkeys(trace_path + [a["service"] for a in anomalies])),
        "affected_nodes": affected,
        "timeline": timeline,
        "stats": stat_list,
        "node_details": node_details,
    }
