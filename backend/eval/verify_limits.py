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
# i) test_explain still prints PASS
# =============================================================================
proc = subprocess.run([sys.executable, "-m", "eval.test_explain"], cwd=BACKEND, capture_output=True, text=True)
check("i) test_explain prints PASS", proc.stdout.strip() == "PASS", f"stdout={proc.stdout!r} stderr={proc.stderr!r}")

# =============================================================================
failed = [r for r in results if not r[1]]
for name, passed, detail in results:
    if not passed:
        print(f"FAIL  {name} -- {detail}")
print(f"\n{len(results) - len(failed)} of {len(results)} PASS")
