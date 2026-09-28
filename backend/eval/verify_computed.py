"""Pure-code verification that confidence is fed the RAW (unboosted) cosine
similarity, while ranking/citation still uses the boosted score unchanged. No
LLM calls, no HTTP, no real log files -- in-memory LogLine fixtures, same
approach as verify_routing.py.

Run: python backend/eval/verify_computed.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
os.environ.setdefault("REPO_PATH", os.path.normpath(os.path.join(BACKEND, "..", "mock-codebase2", "packages")))

from code_indexer import CodeIndexer, display_name  # noqa: E402
from log_analyzer import LogLine  # noqa: E402
import query_pipeline as qp  # noqa: E402

indexer = CodeIndexer(os.environ["REPO_PATH"])
services = qp._service_ids(indexer)
NOW = datetime.now()

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, cond, "" if cond else detail))


def mk_anomaly(service: str, n_errors: int, error_tpl: str) -> dict:
    t0 = NOW - timedelta(seconds=280)
    step = 280 / max(n_errors, 1)
    lines = [LogLine(id=f"l_{service}_{i}", ts=t0 + timedelta(seconds=i * step), severity="error", service=service, message=error_tpl.format(i=i)) for i in range(n_errors)]
    return {"service": service, "errors": n_errors, "warns": 0, "first_seen": lines[0].ts, "first_error": lines[0].ts,
            "last_seen": lines[-1].ts, "top_signatures": [], "lines": lines}


SCENARIOS = {
    "cascading-failure": [
        mk_anomaly("db-pool", 30, "connection pool exhausted order=ord_{i} code=POOL_EXHAUSTED active=5 max=5"),
        mk_anomaly("payment-service", 30, "transaction record failed order=ord_{i} code=POOL_EXHAUSTED"),
        mk_anomaly("ledger-worker", 30, "ledger write failed order=ord_{i} code=POOL_EXHAUSTED"),
        mk_anomaly("orders-service", 30, "order save failed order=ord_{i} code=POOL_EXHAUSTED"),
    ],
    "db-exhaustion": [
        mk_anomaly("db-pool", 30, "connection pool exhausted order=ord_{i} code=POOL_EXHAUSTED active=5 max=5"),
        mk_anomaly("payment-service", 8, "transaction record failed order=ord_{i} code=POOL_EXHAUSTED"),
    ],
    "payment-timeout": [
        mk_anomaly("payment-service", 30, "charge failed order=ord_{i} code=GATEWAY_TIMEOUT"),
    ],
}


def diagnose(question, anomalies):
    return qp._diagnose(question, anomalies, indexer, services)


for name, anomalies in SCENARIOS.items():
    d = diagnose("What is happening in the system right now?", anomalies)
    inc = d["incidents"][d["primary_idx"]]
    conf = d["confidences"][d["primary_idx"]]
    scored = d["chunks_lists"][d["primary_idx"]]  # list of (boosted, raw, chunk), ranked
    boosted_top = d["boosted_scores"][d["primary_idx"]]

    root_id = qp._root_id_of(inc, indexer)
    boost = qp._boost_for(root_id, indexer)
    root_anomaly = next(a for a in anomalies if a["service"] == inc["root"])
    query = qp._build_retrieval_query(inc["root"], root_anomaly)
    # independently recompute retrieval, unboosted, to get an oracle raw value
    unboosted_scored = indexer.search_scored(query, k=qp.MAX_CHUNKS, boost=None)

    top_chunk = scored[0][2]
    top_boosted, top_raw = scored[0][0], scored[0][1]
    b = boost.get(top_chunk.service, 1.0)

    check(f"[{name}] ranking used boost (boosted != raw when boost>1)", b > 1.0 and abs(top_boosted - top_raw * b) < 1e-9,
          f"boost={b} boosted={top_boosted} raw={top_raw}")
    check(f"[{name}] boosted_score field matches top-ranked boosted value", abs(boosted_top - top_boosted) < 1e-9,
          f"boosted_scores[primary]={boosted_top} vs top-ranked={top_boosted}")
    check(f"[{name}] confidence signals.relevance == raw (not boosted)", abs(conf["signals"]["relevance"] - round(top_raw, 3)) < 1e-9,
          f"signals.relevance={conf['signals']['relevance']} raw={round(top_raw, 3)}")
    check(f"[{name}] clamp never triggers (raw already in 0..1)", 0.0 <= top_raw <= 1.0, f"raw={top_raw}")
    # oracle: same top chunk should be the highest-raw chunk among the unboosted ranking
    # restricted to the boosted top hit's own chunk identity (ranking order can legitimately
    # differ pre/post boost; we're only checking the VALUE recorded for the chosen chunk).
    oracle_raw = next((raw for _, raw, ch in unboosted_scored if ch is top_chunk), None)
    check(f"[{name}] raw value matches an independent unboosted recompute", oracle_raw is not None and abs(oracle_raw - top_raw) < 1e-9,
          f"recomputed={oracle_raw} stored={top_raw}")
    expected_score = round(0.4 * round(min((inc['root_errors'] + 0.25 * inc['root_warns']) / 20.0, 1.0), 3) + 0.25 * round(top_raw, 3) + 0.35 * round(1.0 / len(inc['candidates']), 3), 3)
    check(f"[{name}] total score matches hand-computed formula with raw relevance", abs(conf["score"] - expected_score) < 1e-9,
          f"actual={conf['score']} expected={expected_score}")

failed = [r for r in results if not r[1]]
for name, passed, detail in results:
    if not passed:
        print(f"FAIL  {name} -- {detail}")
print(f"\n{len(results) - len(failed)} of {len(results)} PASS")
