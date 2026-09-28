"""Pure-code verification of the competitor/floor mechanism, root selection by
weighted_errors, activity, and explain() wiring (Prompt 5 / "formula limits").
No LLM calls, no HTTP, no real log files -- in-memory LogLine fixtures.

Run: python backend/eval/verify_limits.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
os.environ.setdefault("REPO_PATH", os.path.normpath(os.path.join(BACKEND, "..", "mock-codebase2", "packages")))

from code_indexer import CodeIndexer  # noqa: E402
from log_analyzer import LogLine  # noqa: E402
import explain as explain_module  # noqa: E402
import query_pipeline as qp  # noqa: E402

indexer = CodeIndexer(os.environ["REPO_PATH"])
services = qp._service_ids(indexer)
NOW = datetime.now()

results: list[tuple[str, bool, str]] = []


def check(name, cond, detail=""):
    results.append((name, cond, "" if cond else detail))


def mk_anomaly(service, n, tpl, end_offset_s=10.0, span_s=280.0):
    """n errors ending `end_offset_s` seconds before NOW (default: recent/ongoing),
    spread back over `span_s` seconds before that."""
    t_end = NOW - timedelta(seconds=end_offset_s)
    t0 = t_end - timedelta(seconds=span_s)
    step = span_s / max(n, 1)
    lines = [LogLine(id=f"l_{service}_{i}", ts=t0 + timedelta(seconds=i * step), severity="error", service=service, message=tpl.format(i=i)) for i in range(n)]
    return {"service": service, "errors": n, "warns": 0, "first_seen": lines[0].ts, "first_error": lines[0].ts,
            "last_seen": lines[-1].ts, "top_signatures": [], "lines": lines}


def diagnose(question, anomalies, now=NOW):
    return qp._diagnose(question, anomalies, indexer, services, now)


def primary_of(d):
    return d["incidents"][d["primary_idx"]] if d["primary_idx"] is not None else dict(qp._EMPTY_INCIDENT)


def conf_of(d):
    return d["confidences"][d["primary_idx"]] if d["primary_idx"] is not None else qp._compute_confidence(0, 0, 0, 0.0)


def competing_of(d):
    return d["competing_candidates"][d["primary_idx"]] if d["primary_idx"] is not None else []


def reason_of(d):
    return explain_module.confidence_reason(primary_of(d), conf_of(d), competing_of(d), qp.CONFIG["EVIDENCE_DIVISOR"])


POOL_TPL = "connection pool exhausted order=ord_{i} code=POOL_EXHAUSTED active=5 max=5"

# =============================================================================
# a) cascade, root errors ending 4 min ago -> stopped, same score/label as ongoing
# =============================================================================
def cascade(end_offset_s):
    return [
        mk_anomaly("db-pool", 30, POOL_TPL, end_offset_s=end_offset_s),
        mk_anomaly("payment-service", 30, "transaction record failed order=ord_{i} code=POOL_EXHAUSTED", end_offset_s=end_offset_s),
        mk_anomaly("ledger-worker", 30, "ledger write failed order=ord_{i} code=POOL_EXHAUSTED", end_offset_s=end_offset_s),
        mk_anomaly("orders-service", 30, "order save failed order=ord_{i} code=POOL_EXHAUSTED", end_offset_s=end_offset_s),
    ]

d_ongoing = diagnose("What is happening?", cascade(10.0))
d_stopped = diagnose("What is happening?", cascade(240.0))
p_on, p_off = primary_of(d_ongoing), primary_of(d_stopped)
c_on, c_off = conf_of(d_ongoing), conf_of(d_stopped)
check("a) ongoing activity == 'ongoing'", p_on["activity"] == "ongoing", f"got {p_on['activity']!r}")
check("a) stopped activity == 'stopped'", p_off["activity"] == "stopped", f"got {p_off['activity']!r}")
check("a) same score ongoing vs stopped", c_on["score"] == c_off["score"], f"ongoing={c_on['score']} stopped={c_off['score']}")
check("a) same confidence label ongoing vs stopped", c_on["label"] == c_off["label"], f"ongoing={c_on['label']} stopped={c_off['label']}")
check("a) same structural label ongoing vs stopped", p_on["label"] == p_off["label"], f"ongoing={p_on['label']} stopped={p_off['label']}")

# =============================================================================
# b) victim (orders-service) with two unrelated upstream roots (payment-service,
#    ledger-worker) at 30 errors each, bridged through the victim -> low
# =============================================================================
TWO_UPSTREAM_EQUAL = [
    mk_anomaly("payment-service", 30, "transaction record failed order=ord_{i} code=X"),
    mk_anomaly("ledger-worker", 30, "ledger write failed order=ord_{i} code=X"),
    mk_anomaly("orders-service", 5, "order save failed order=ord_{i} code=X"),
]
d_b = diagnose("What is happening?", TWO_UPSTREAM_EQUAL)
p_b, c_b = primary_of(d_b), conf_of(d_b)
check("b) two equal upstream roots -> 2 competitors", len(p_b["candidates"]) == 2, f"candidates={p_b['candidates']!r}")
check("b) two equal upstream roots -> confidence low", c_b["label"] == "low", f"got {c_b['label']!r}")

# =============================================================================
# c) cascade + 1 stray error on notify-worker (bridged in via orders-service) ->
#    primary unchanged, notify-worker split out as its own minor incident
# =============================================================================
CASCADE_PLUS_STRAY = cascade(10.0) + [mk_anomaly("notify-worker", 1, "email failed order=ord_{i} code=X")]
d_c = diagnose("What is happening?", CASCADE_PLUS_STRAY)
p_c = primary_of(d_c)
check("c) primary root unchanged (db-pool)", p_c["root"] == "db-pool", f"got {p_c['root']!r}")
check("c) primary still single competitor", p_c["label"] == "single" and len(p_c["candidates"]) == 1, f"label={p_c['label']} candidates={p_c['candidates']!r}")
notify_incs = [inc for inc in d_c["incidents"] if inc["root"] == "notify-worker"]
check("c) notify-worker split into its own incident", len(notify_incs) == 1, f"found {len(notify_incs)} matching incidents")
check("c) notify-worker incident is_minor", bool(notify_incs) and notify_incs[0]["is_minor"], f"is_minor={notify_incs[0]['is_minor'] if notify_incs else 'N/A'}")

# =============================================================================
# d) general vs specific(root) -> same score (regression check post-refactor)
# =============================================================================
d_gen = diagnose("What is happening?", cascade(10.0))
d_spec = diagnose("What is wrong with db-pool?", cascade(10.0))
check("d) general vs specific(root) same score", conf_of(d_gen)["score"] == conf_of(d_spec)["score"],
      f"general={conf_of(d_gen)['score']} specific={conf_of(d_spec)['score']}")

# =============================================================================
# e) three unrelated roots at 394/180/150 -> three separate incidents, each
#    high, ordered 394,180,150 (db-pool, api-gateway, notify-worker: mutually
#    unrelated leaves as long as their common callers stay healthy)
# =============================================================================
THREE_UNRELATED = [
    mk_anomaly("db-pool", 394, POOL_TPL),
    mk_anomaly("api-gateway", 180, "upstream 5xx order=ord_{i} code=X"),
    mk_anomaly("notify-worker", 150, "email failed order=ord_{i} code=X"),
]
d_e = diagnose("What is happening?", THREE_UNRELATED)
check("e) three separate incidents", len(d_e["incidents"]) == 3, f"got {len(d_e['incidents'])}")
check("e) each incident high confidence", all(c["label"] == "high" for c in d_e["confidences"]), f"labels={[c['label'] for c in d_e['confidences']]}")
check("e) ordered 394,180,150", [inc["root_errors"] for inc in d_e["incidents"]] == [394, 180, 150], f"got {[inc['root_errors'] for inc in d_e['incidents']]}")

# =============================================================================
# f) victim (orders-service) with three upstream roots at 394/180/150 -> low
# =============================================================================
THREE_UPSTREAM = [
    mk_anomaly("payment-service", 394, "transaction record failed order=ord_{i} code=X"),
    mk_anomaly("ledger-worker", 180, "ledger write failed order=ord_{i} code=X"),
    mk_anomaly("notify-worker", 150, "email failed order=ord_{i} code=X"),
    mk_anomaly("orders-service", 5, "order save failed order=ord_{i} code=X"),
]
d_f = diagnose("What is happening?", THREE_UPSTREAM)
p_f, c_f = primary_of(d_f), conf_of(d_f)
check("f) three upstream competitors", len(p_f["candidates"]) == 3, f"candidates={p_f['candidates']!r}")
check("f) confidence low", c_f["label"] == "low", f"got {c_f['label']!r}")

# =============================================================================
# g) victim with upstream roots at 394 and 2 -> root is 394 one, high, the
#    2-error service listed as minor
# =============================================================================
STRONG_AND_WEAK = [
    mk_anomaly("payment-service", 394, "transaction record failed order=ord_{i} code=X"),
    mk_anomaly("ledger-worker", 2, "ledger write failed order=ord_{i} code=X"),
    mk_anomaly("orders-service", 5, "order save failed order=ord_{i} code=X"),
]
d_g = diagnose("What is happening?", STRONG_AND_WEAK)
p_g, c_g = primary_of(d_g), conf_of(d_g)
check("g) root is the 394 one", p_g["root"] == "payment-service", f"got {p_g['root']!r}")
check("g) high confidence", c_g["label"] == "high", f"got {c_g['label']!r}")
weak_incs = [inc for inc in d_g["incidents"] if inc["root"] == "ledger-worker"]
check("g) 2-error service listed as minor", bool(weak_incs) and weak_incs[0]["is_minor"], f"found={len(weak_incs)}")

# =============================================================================
# h) upstream roots at 394 and 390 -> low
# =============================================================================
BOTH_STRONG = [
    mk_anomaly("payment-service", 394, "transaction record failed order=ord_{i} code=X"),
    mk_anomaly("ledger-worker", 390, "ledger write failed order=ord_{i} code=X"),
    mk_anomaly("orders-service", 5, "order save failed order=ord_{i} code=X"),
]
d_h = diagnose("What is happening?", BOTH_STRONG)
c_h = conf_of(d_h)
check("h) confidence low", c_h["label"] == "low", f"got {c_h['label']!r}")

# =============================================================================
# confidence_reason / competing_candidates (Prompt 6 / "explanation")
# =============================================================================

# a) two upstream roots at 394/390 (reuses h's fixture): low, reason names
#    both services and both counts, competing_candidates has 2 entries.
comp_h, reason_h = competing_of(d_h), reason_of(d_h)
check("a) competing_candidates has 2 entries", len(comp_h) == 2, f"got {comp_h!r}")
check("a) reason names both services and counts", reason_h is not None and all(
    tok in reason_h for tok in ("payment-service", "394", "ledger-worker", "390")
), f"reason={reason_h!r}")
check("a) reason never says 'similar'", reason_h is not None and "similar" not in reason_h, f"reason={reason_h!r}")

# b) three roots at 394/180/150 upstream of one victim (reuses f's fixture):
#    3 entries ordered by count.
comp_f, reason_f = competing_of(d_f), reason_of(d_f)
check("b) 3 entries ordered by count", [c["service"] for c in comp_f] == ["payment-service", "ledger-worker", "notify-worker"],
      f"got {[c['service'] for c in comp_f]!r}")
check("b) reason names all three counts, 'all' phrasing", reason_f is not None and all(
    tok in reason_f for tok in ("394", "180", "150", "are all plausible root causes")
), f"reason={reason_f!r}")

# c) roots at 394 and 2 (reuses g's fixture): high, competing_candidates
#    empty, reason null, paragraph does not claim it can't name a cause.
comp_g, reason_g = competing_of(d_g), reason_of(d_g)
check("c) competing_candidates empty when high", comp_g == [], f"got {comp_g!r}")
check("c) reason null when high", reason_g is None, f"got {reason_g!r}")
explain_input_g = dict(
    failing_services=p_g["failing_services"], root=p_g["root"], candidates=p_g["candidates"],
    symptoms=p_g["symptoms"], root_errors=p_g["root_errors"], label=c_g["label"], score=c_g["score"],
    signals=c_g["signals"], is_eval=False,
)
paragraph_g = explain_module.explain(explain_input_g)
check("c) paragraph does not say it cannot name a single cause", "cannot name a single cause" not in paragraph_g
      and "not name a single cause" not in paragraph_g, f"paragraph={paragraph_g!r}")

# d) one clear root with only 5 errors, nothing else failing: low, competing
#    empty, reason mentions the 5 errors and the evidence divisor.
ISOLATED_THIN = [mk_anomaly("notify-worker", 5, "generic failure occurred id={i}")]
d_d = diagnose("What is happening?", ISOLATED_THIN)
p_d, c_d = primary_of(d_d), conf_of(d_d)
comp_d, reason_d = competing_of(d_d), reason_of(d_d)
check("d) confidence low", c_d["label"] == "low", f"got {c_d['label']!r}")
check("d) competing_candidates empty (not ambiguity)", comp_d == [], f"got {comp_d!r}")
check("d) reason mentions 5 errors and the divisor", reason_d is not None and "5" in reason_d
      and str(qp.CONFIG["EVIDENCE_DIVISOR"]) in reason_d, f"reason={reason_d!r}")

# e) rename the services in memory (a-svc, b-svc): confidence_reason is pure
#    code fed only from its arguments, so it must use the given names, never
#    a name from the real mock codebase.
SYNTH_INCIDENT = {"root": "a-svc", "root_errors": 50}
SYNTH_CONF = {"label": "low", "signals": {"evidence": 1.0, "relevance": 1.0, "dominance": 0.5}}
SYNTH_COMPETING = [
    {"service": "a-svc", "weighted_errors": 50, "share_of_top": 1.0, "label": "ambiguous"},
    {"service": "b-svc", "weighted_errors": 40, "share_of_top": 0.8, "label": None},
]
reason_synth = explain_module.confidence_reason(SYNTH_INCIDENT, SYNTH_CONF, SYNTH_COMPETING, qp.CONFIG["EVIDENCE_DIVISOR"])
check("e) reason uses the renamed services", reason_synth is not None and "a-svc" in reason_synth and "b-svc" in reason_synth,
      f"reason={reason_synth!r}")
check("e) no real service name hardcoded into the reason", reason_synth is not None and not any(
    name in reason_synth for name in ("payment-service", "ledger-worker", "db-pool", "notify-worker", "orders-service", "api-gateway")
), f"reason={reason_synth!r}")

# =============================================================================
# i) test_explain still prints PASS  (also covers TEST item "f")
# =============================================================================
proc = subprocess.run([sys.executable, "-m", "eval.test_explain"], cwd=BACKEND, capture_output=True, text=True)
check("i) test_explain prints PASS", proc.stdout.strip() == "PASS", f"stdout={proc.stdout!r} stderr={proc.stderr!r}")

# =============================================================================
failed = [r for r in results if not r[1]]
for name, passed, detail in results:
    if not passed:
        print(f"FAIL  {name} -- {detail}")
print(f"\n{len(results) - len(failed)} of {len(results)} PASS")
