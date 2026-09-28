"""Regenerates the three canned demo scenario logs at realistic error volume.

The originals (kept verbatim in eval/fixtures_thin/ for reuse as low-volume test
cases) had only 3-6 errors on the root service -- enough to demo the story, too
thin to be a meaningful confidence-scoring test. This writes new versions with
30+ errors on the root service inside a single 5-minute window, keeping the same
services, story, and log line format (log_analyzer.LINE_RE:
"<ISO8601 with .mmmZ> LEVEL service message"), and the same victim-to-root error
ratio each original scenario had. Output overwrites mock-codebase2/logs/ (the
files the scenario selector actually reads); the originals are untouched in
eval/fixtures_thin/.

Run: python eval/generate_fixtures.py
"""
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "mock-codebase2" / "logs"
BASE = datetime(2026, 9, 27, 16, 0, 0)  # arbitrary anchor; scenario_sim shifts to "now" on replay


def ts(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def line(t: datetime, level: str, svc: str, msg: str) -> str:
    return f"{ts(t)} {level} {svc} {msg}"


# ---------------------------------------------------------------------------
def gen_cascading_failure() -> list[str]:
    """Story: db-pool exhaustion cascades into payment-service, ledger-worker,
    and orders-service (all depend on db-pool) -- same as the original, just 30
    failure events instead of 3, 1:1:1:1 ratio preserved exactly."""
    out = []
    t = BASE
    out.append(line(t, "INFO", "api-gateway", "request routed order=ord_9500"))
    out.append(line(t + timedelta(milliseconds=400), "INFO", "payment-service", "gateway.charge succeeded order=ord_9500 latency=520ms"))
    out.append(line(t + timedelta(milliseconds=500), "INFO", "db-pool", "transaction recorded order=ord_9500"))
    out.append(line(t + timedelta(milliseconds=600), "INFO", "ledger-worker", "ledger entry written order=ord_9500"))
    out.append(line(t + timedelta(milliseconds=700), "INFO", "orders-service", "order saved order=ord_9500"))
    out.append(line(t + timedelta(milliseconds=800), "INFO", "notify-worker", "confirmation email queued order=ord_9500"))

    t = BASE + timedelta(seconds=270)  # ~4.5 min quiet gap, then the incident starts
    N = 30
    for i in range(N):
        order = f"ord_95{20 + i}"
        e = t + timedelta(seconds=i * 9.5)
        out.append(line(e, "ERROR", "db-pool", f"connection pool exhausted order={order} code=POOL_EXHAUSTED active=5 max=5"))
        out.append(line(e + timedelta(milliseconds=300), "ERROR", "payment-service", f"transaction record failed order={order} code=POOL_EXHAUSTED"))
        out.append(line(e + timedelta(milliseconds=900), "ERROR", "ledger-worker", f"ledger write failed order={order} code=POOL_EXHAUSTED"))
        out.append(line(e + timedelta(milliseconds=1200), "ERROR", "orders-service", f"order save failed order={order} code=POOL_EXHAUSTED"))
        out.append(line(e + timedelta(milliseconds=1400), "INFO", "notify-worker", f"confirmation email queued order={order}"))
        if i == 14:  # same "elevated error rate" warning the original had, mid-burst
            out.append(line(e + timedelta(seconds=2), "WARN", "api-gateway", "elevated error rate downstream 5xx=15 window=60s"))
    return out


# ---------------------------------------------------------------------------
def gen_db_exhaustion() -> list[str]:
    """Story: db-pool exhaustion, most requests fail there alone; a smaller
    fraction also produce a payment-service error (the original's 4:1 db-pool
    to payment-service ratio, preserved at 30:~7)."""
    out = []
    t = BASE
    out.append(line(t, "INFO", "api-gateway", "request routed order=ord_9001"))
    out.append(line(t + timedelta(milliseconds=300), "INFO", "orders-service", "checkout started order=ord_9001"))
    out.append(line(t + timedelta(milliseconds=800), "INFO", "payment-service", "gateway.charge succeeded order=ord_9001 latency=540ms"))
    out.append(line(t + timedelta(milliseconds=900), "INFO", "db-pool", "transaction recorded order=ord_9001"))
    out.append(line(t + timedelta(seconds=1), "INFO", "orders-service", "order saved order=ord_9001"))
    out.append(line(t + timedelta(milliseconds=1100), "INFO", "notify-worker", "confirmation email queued order=ord_9001"))

    t = BASE + timedelta(seconds=190)  # ~3 min quiet gap, matches original's pacing
    N = 30
    for i in range(N):
        order = f"ord_90{10 + i}"
        e = t + timedelta(seconds=i * 9.0)
        out.append(line(e, "INFO", "api-gateway", f"request routed order={order}"))
        out.append(line(e + timedelta(milliseconds=300), "INFO", "payment-service", f"gateway.charge succeeded order={order} latency={490 + (i % 30)}ms"))
        out.append(line(e + timedelta(milliseconds=350), "ERROR", "db-pool", f"connection pool exhausted order={order} code=POOL_EXHAUSTED active=5 max=5"))
        if i % 4 == 0:  # same ~1-in-4 ratio the original had (4 db-pool : 1 payment-service)
            out.append(line(e + timedelta(milliseconds=400), "ERROR", "payment-service", f"transaction record failed order={order} code=POOL_EXHAUSTED"))
        if i % 5 == 0:
            out.append(line(e + timedelta(milliseconds=500), "INFO", "notify-worker", f"confirmation email queued order={order}"))
    return out


# ---------------------------------------------------------------------------
def gen_payment_timeout() -> list[str]:
    """Story: payment-service's own gateway call times out repeatedly. No
    victims (db-pool/orders-service stay healthy, same as the original -- the
    timeout happens before any downstream call), 15 attempts x 2 errors = 30."""
    out = []
    t = BASE
    out.append(line(t, "INFO", "api-gateway", "request routed order=ord_8860"))
    out.append(line(t + timedelta(seconds=1, milliseconds=500), "INFO", "orders-service", "checkout started order=ord_8860"))
    out.append(line(t + timedelta(seconds=2, milliseconds=200), "INFO", "payment-service", "gateway.charge succeeded order=ord_8860 latency=612ms"))
    out.append(line(t + timedelta(seconds=2, milliseconds=300), "INFO", "db-pool", "transaction recorded order=ord_8860"))
    out.append(line(t + timedelta(seconds=2, milliseconds=350), "INFO", "orders-service", "order saved order=ord_8860"))
    out.append(line(t + timedelta(seconds=2, milliseconds=400), "INFO", "notify-worker", "confirmation email queued order=ord_8860"))

    t = BASE + timedelta(seconds=160)  # ~2.5 min quiet gap, matches original's pacing
    N = 15  # 15 attempts x 2 errors each = 30
    for i in range(N):
        order = f"ord_88{71 + i}"
        e = t + timedelta(seconds=i * 19.0)
        out.append(line(e, "ERROR", "payment-service", f"gateway.charge timeout after 3000ms order={order}"))
        out.append(line(e + timedelta(milliseconds=100), "INFO", "payment-service", f"retry 1/3 order={order}"))
        out.append(line(e + timedelta(milliseconds=800), "ERROR", "payment-service", f"charge failed order={order} code=GATEWAY_TIMEOUT"))
        if i % 3 == 0:
            out.append(line(e + timedelta(milliseconds=900), "INFO", "payment-service", "circuit breaker half-open payment->stripe"))

    out.append(line(t + timedelta(seconds=N * 19 + 20), "INFO", "db-pool", "connection pool nominal active=4 idle=1"))
    out.append(line(t + timedelta(seconds=N * 19 + 30), "INFO", "notify-worker", "confirmation email queued order=ord_8865"))
    return out


SCENARIOS = {
    "scenario-cascading-failure.log": gen_cascading_failure,
    "scenario-db-exhaustion.log": gen_db_exhaustion,
    "scenario-payment-timeout.log": gen_payment_timeout,
}

if __name__ == "__main__":
    for filename, gen in SCENARIOS.items():
        lines = gen()
        out_path = OUT_DIR / filename
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        errors = sum(1 for l in lines if " ERROR " in l)
        print(f"{filename}: {len(lines)} lines, {errors} ERROR lines")
