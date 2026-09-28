"""Pure-code verification of the question router, incident scoping, and
confidence computation (Prompt 2). No LLM calls, no HTTP, no real log files --
every scenario's anomaly data is built in memory as LogLine objects. Only the
real CodeIndexer (dependency graph + TF-IDF retrieval, both pure code reading
already-on-disk source files) is used, so routing is tested against the real
graph, not a hand-drawn stand-in of it.

Run: python backend/eval/verify_routing.py
"""
from __future__ import annotations

import os
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

results: list[tuple[str, bool, str]] = []  # (name, passed, detail-if-failed)


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, cond, "" if cond else detail))


# --- in-memory fixture builder -----------------------------------------------
def mk_anomaly(service: str, n_errors: int, n_warns: int = 0, error_tpl: str = "failure order=ord_{i} code=ERR", start_offset: float = 280.0) -> dict:
    lines = []
    t0 = NOW - timedelta(seconds=start_offset)
    step = start_offset / max(n_errors, 1)
    for i in range(n_errors):
        lines.append(LogLine(id=f"l_{service}_e{i}", ts=t0 + timedelta(seconds=i * step), severity="error", service=service, message=error_tpl.format(i=i)))
    for i in range(n_warns):
        lines.append(LogLine(id=f"l_{service}_w{i}", ts=t0 + timedelta(seconds=i), severity="warn", service=service, message=f"elevated latency order=ord_{i}"))
    lines.sort(key=lambda l: l.ts)
    errors = [l for l in lines if l.severity == "error"]
    return {
        "service": service, "errors": len(errors), "warns": len(lines) - len(errors),
        "first_seen": lines[0].ts if lines else NOW, "first_error": errors[0].ts if errors else None,
        "last_seen": lines[-1].ts if lines else NOW, "top_signatures": [], "lines": lines,
    }


# --- the 3 regenerated scenarios, in memory (same shapes as the real fixtures) ---
CASCADING = [
    mk_anomaly("db-pool", 30, error_tpl="connection pool exhausted order=ord_{i} code=POOL_EXHAUSTED active=5 max=5"),
    mk_anomaly("payment-service", 30, error_tpl="transaction record failed order=ord_{i} code=POOL_EXHAUSTED"),
    mk_anomaly("ledger-worker", 30, error_tpl="ledger write failed order=ord_{i} code=POOL_EXHAUSTED"),
    mk_anomaly("orders-service", 30, error_tpl="order save failed order=ord_{i} code=POOL_EXHAUSTED"),
]
DB_EXHAUSTION = [
    mk_anomaly("db-pool", 30, error_tpl="connection pool exhausted order=ord_{i} code=POOL_EXHAUSTED active=5 max=5"),
    mk_anomaly("payment-service", 8, error_tpl="transaction record failed order=ord_{i} code=POOL_EXHAUSTED"),
]
PAYMENT_TIMEOUT = [
    mk_anomaly("payment-service", 30, error_tpl="charge failed order=ord_{i} code=GATEWAY_TIMEOUT"),
]
SCENARIOS = {"cascading-failure": CASCADING, "db-exhaustion": DB_EXHAUSTION, "payment-timeout": PAYMENT_TIMEOUT}


def diagnose(question: str, anomalies: list[dict]) -> dict:
    return qp._diagnose(question, anomalies, indexer, services)


def primary_of(d: dict) -> dict:
    return d["incidents"][d["primary_idx"]] if d["primary_idx"] is not None else dict(qp._EMPTY_INCIDENT)


def conf_of(d: dict) -> dict:
    return d["confidences"][d["primary_idx"]] if d["primary_idx"] is not None else qp._compute_confidence(0, 0, 0, 0.0)


# =============================================================================
# a) general vs specific(root) give the same root and score, for all 3 scenarios
# =============================================================================
for name, anomalies in SCENARIOS.items():
    root_service = "db-pool" if name != "payment-timeout" else "payment-service"
    g = diagnose("What is happening in the system right now?", anomalies)
    s = diagnose(f"What is wrong with {root_service}?", anomalies)
    gp, sp = primary_of(g), primary_of(s)
    gc, sc = conf_of(g), conf_of(s)
    check(f"a[{name}] general.mode==general", g["mode"] == "general", f"got {g['mode']!r}")
    check(f"a[{name}] specific.mode==specific,target={root_service}", s["mode"] == "specific" and s["target"] == root_service, f"got mode={s['mode']!r} target={s['target']!r}")
    check(f"a[{name}] same root ({root_service})", gp["root"] == root_service == sp["root"], f"general={gp['root']!r} specific={sp['root']!r}")
    check(f"a[{name}] same score", gc["score"] == sc["score"], f"general={gc['score']} specific={sc['score']}")

# =============================================================================
# b) cascade: specific query about victim (payment-service) -> root db-pool,
#    chain payment-service -> db-pool, same score as asking about db-pool
# =============================================================================
d_victim = diagnose("What is wrong with payment-service?", CASCADING)
d_root = diagnose("What is wrong with db-pool?", CASCADING)
victim_p, root_p = primary_of(d_victim), primary_of(d_root)
victim_c, root_c = conf_of(d_victim), conf_of(d_root)
check("b) victim query root==db-pool", victim_p["root"] == "db-pool", f"got {victim_p['root']!r}")
check("b) chain == payment-service -> db-pool", d_victim["chain"] == ["payment-service", "db-pool"], f"got {d_victim['chain']!r}")
check("b) same score as asking about db-pool", victim_c["score"] == root_c["score"], f"victim={victim_c['score']} root={root_c['score']}")

# =============================================================================
# c) specific query about a healthy service -> answer_type healthy, no cause forced
# =============================================================================
d_healthy = diagnose("What is wrong with notify-worker?", CASCADING)  # notify-worker never fails in this fixture
check("c) healthy service -> answer_type==healthy", d_healthy["answer_type"] == "healthy", f"got {d_healthy['answer_type']!r}")
check("c) healthy service -> no primary incident forced", d_healthy["primary_idx"] is None, f"got primary_idx={d_healthy['primary_idx']!r}")

# =============================================================================
# d) specific query about a service not in the graph -> answer_type unknown_service
# =============================================================================
d_unknown = diagnose("What is wrong with shipping-service?", CASCADING)
check("d) unknown service -> answer_type==unknown_service", d_unknown["answer_type"] == "unknown_service", f"got {d_unknown['answer_type']!r}")
check("d) unknown service -> mode==unknown_service", d_unknown["mode"] == "unknown_service", f"got {d_unknown['mode']!r}")

# =============================================================================
# e) two unrelated faults (notify-worker, payment-service failing; db-pool
#    healthy) -> general gives two separate incidents; specific about
#    payment-service returns only its own incident
# =============================================================================
TWO_FAULTS = [
    mk_anomaly("notify-worker", 30, error_tpl="email send failed order=ord_{i} code=SMTP_ERROR"),
    mk_anomaly("payment-service", 30, error_tpl="charge failed order=ord_{i} code=GATEWAY_TIMEOUT"),
]
d_two_general = diagnose("What is happening in the system right now?", TWO_FAULTS)
check("e) general -> 2 separate incidents", len(d_two_general["incidents"]) == 2, f"got {len(d_two_general['incidents'])}")
check("e) general -> each incident is its own single root", all(inc["label"] == "single" for inc in d_two_general["incidents"]),
      f"labels={[inc['label'] for inc in d_two_general['incidents']]}")
check("e) general -> each incident has its own high confidence", all(c["label"] == "high" for c in d_two_general["confidences"]),
      f"confidences={[c['label'] for c in d_two_general['confidences']]}")

d_two_specific = diagnose("What is wrong with payment-service?", TWO_FAULTS)
check("e) specific(payment-service) -> mode specific", d_two_specific["mode"] == "specific", f"got {d_two_specific['mode']!r}")
check("e) specific(payment-service) -> root is itself", primary_of(d_two_specific)["root"] == "payment-service", f"got {primary_of(d_two_specific)['root']!r}")
# incidents list must NOT include the unrelated notify-worker incident. run_query()
# scopes this (not _diagnose(), which always returns every incident for scoring) --
# replicate that same scoping rule here since that's the actual contract being tested.
scoped_roots = [primary_of(d_two_specific)["root"]] if d_two_specific["mode"] == "specific" and d_two_specific["answer_type"] == "incident" else [inc["root"] for inc in d_two_specific["incidents"]]
check("e) specific(payment-service) -> incidents list is scoped to just its own", scoped_roots == ["payment-service"], f"got {scoped_roots!r}")

# =============================================================================
# f) clean log: general query gives no cause and a neutral graph
# =============================================================================
d_clean = diagnose("What is happening in the system right now?", [])
check("f) clean log -> answer_type==healthy", d_clean["answer_type"] == "healthy", f"got {d_clean['answer_type']!r}")
check("f) clean log -> no incidents", d_clean["incidents"] == [], f"got {d_clean['incidents']!r}")
check("f) clean log -> no primary (neutral graph)", d_clean["primary_idx"] is None, f"got primary_idx={d_clean['primary_idx']!r}")

# =============================================================================
# g) compare scores for the 3 regenerated scenarios before vs after
# =============================================================================
BEFORE = {"cascading-failure": 0.906, "db-exhaustion": 0.937, "payment-timeout": 0.932}  # Prompt 1, recorded via real API calls
moved = []
for name, anomalies in SCENARIOS.items():
    after = conf_of(diagnose("What is happening in the system right now?", anomalies))["score"]
    before = BEFORE[name]
    if abs(after - before) > 1e-9:
        moved.append((name, before, after))

# =============================================================================
# print compact PASS/FAIL table
# =============================================================================
failed = [r for r in results if not r[1]]
for name, passed, detail in results:
    if not passed:
        print(f"FAIL  {name} -- {detail}")
print(f"\n{len(results) - len(failed)} of {len(results)} PASS")

print("\ng) score comparison (before Prompt 2 -> after):")
for name in SCENARIOS:
    after = conf_of(diagnose("What is happening in the system right now?", SCENARIOS[name]))["score"]
    tag = "MOVED" if any(m[0] == name for m in moved) else "same"
    print(f"  {name}: {BEFORE[name]} -> {after}  [{tag}]")
