"""Traffic simulator: appends realistic log lines to the file the Log Analyzer reads.

Mostly healthy traffic through the sample repo's call chain
(api-gateway -> orders-service -> payment-service -> ledger-worker / db-pool),
with occasional anomaly bursts so the status strip pulses during a demo.

    python traffic_sim.py                     # auto: random bursts every 60-120s
    python traffic_sim.py --scenario payment  # start a payment gateway-timeout burst now
    python traffic_sim.py --scenario db       # db-pool exhaustion
    python traffic_sim.py --scenario ambiguous# latency warnings with no clear cause (low signal)
    python traffic_sim.py --scenario none     # healthy traffic only

While running, type a scenario name + Enter (payment | db | ambiguous | none) to switch live.
Stop and restart freely: it only ever appends.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")
LOG_PATH = Path(os.environ.get("LOG_PATH") or HERE / "logs" / "app.log")

SCENARIOS = ("payment", "db", "ambiguous", "none")
state = {"scenario": "none", "until": 0.0}


def write(service: str, level: str, msg: str):
    ts = datetime.now()
    line = f"{ts.strftime('%Y-%m-%dT%H:%M:%S')}.{ts.microsecond // 1000:03d} {level} {service} {msg}\n"
    with open(LOG_PATH, "a", encoding="utf8") as f:
        f.write(line)


def order_id() -> str:
    return f"ord_{random.randint(1000, 9999)}"


def healthy_request():
    o = order_id()
    lat = random.randint(180, 620)
    write("api-gateway", "INFO", f"POST /checkout order={o}")
    write("orders-service", "INFO", f"submit_order order={o} items={random.randint(1, 5)}")
    write("payment-service", "INFO", f"gateway.charge ok latency {lat}ms order={o}")
    write("ledger-worker", "INFO", f"record_entry order={o} amount={random.randint(5, 400)}.00")
    if random.random() < 0.6:
        write("notify-worker", "INFO", f"receipt queued order={o}")


def payment_burst_request():
    o = order_id()
    write("api-gateway", "INFO", f"POST /checkout order={o}")
    write("orders-service", "INFO", f"submit_order order={o} items={random.randint(1, 5)}")
    write("payment-service", "WARN", f"gateway.charge latency {random.randint(2500, 2990)}ms (p99 threshold 1200ms)")
    if random.random() < 0.85:
        write("payment-service", "ERROR", f"gateway.charge timeout after 3000ms order={o}")
        write("payment-service", "ERROR", f"charge failed order={o} code=GATEWAY_TIMEOUT")
        write("orders-service", "WARN", f"charge failed, retry {random.randint(1, 3)}/3 order={o}")
        if random.random() < 0.4:
            write("api-gateway", "WARN", f"elevated p99 latency on /checkout ({random.randint(4200, 8000)}ms)")
        if random.random() < 0.5:
            write("ledger-worker", "INFO", f"ledger entry deferred order={o}")
    else:
        write("payment-service", "INFO", f"gateway.charge ok latency {random.randint(2600, 2990)}ms order={o}")


def db_burst_request():
    o = order_id()
    write("api-gateway", "INFO", f"POST /checkout order={o}")
    write("orders-service", "INFO", f"submit_order order={o} items={random.randint(1, 5)}")
    write("db-pool", "WARN", f"pool saturated: {random.randint(19, 20)}/20 connections in use, {random.randint(4, 15)} waiting")
    if random.random() < 0.8:
        write("db-pool", "ERROR", "acquire timeout after 5000ms: pool exhausted")
        write("payment-service", "ERROR", f"charge failed order={o} code=DB_UNAVAILABLE")
        write("orders-service", "WARN", f"charge failed, retry {random.randint(1, 3)}/3 order={o}")


def ambiguous_request():
    """Latency creeps up in orders-service with no error signature to pin it on."""
    o = order_id()
    write("api-gateway", "INFO", f"POST /checkout order={o}")
    write("orders-service", "WARN", f"submit_order slow: {random.randint(900, 1900)}ms order={o}")
    write("payment-service", "INFO", f"gateway.charge ok latency {random.randint(300, 700)}ms order={o}")
    write("db-pool", "INFO", f"pool usage {random.randint(6, 12)}/20")
    write("notify-worker", "INFO", f"receipt queued order={o}")


def watch_stdin():
    for raw in sys.stdin:
        name = raw.strip().lower()
        if name in SCENARIOS:
            state["scenario"], state["until"] = name, time.time() + 45
            print(f"[sim] scenario -> {name}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="auto", choices=("auto",) + SCENARIOS)
    ap.add_argument("--interval", type=float, default=0.8, help="mean seconds between requests")
    args = ap.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[sim] writing to {LOG_PATH}  (type payment|db|ambiguous|none + Enter to switch)", flush=True)
    threading.Thread(target=watch_stdin, daemon=True).start()

    next_auto = time.time() + random.uniform(20, 40)
    if args.scenario not in ("auto", "none"):
        state["scenario"], state["until"] = args.scenario, time.time() + 45

    while True:
        now = time.time()
        if args.scenario == "auto" and state["scenario"] == "none" and now >= next_auto:
            state["scenario"] = random.choice(("payment", "payment", "db", "ambiguous"))
            state["until"] = now + random.uniform(30, 45)
            print(f"[sim] auto burst: {state['scenario']}", flush=True)
        if state["scenario"] != "none" and now >= state["until"]:
            print(f"[sim] burst over: {state['scenario']}", flush=True)
            state["scenario"] = "none"
            next_auto = now + random.uniform(60, 120)

        {"payment": payment_burst_request, "db": db_burst_request, "ambiguous": ambiguous_request}.get(
            state["scenario"], healthy_request)()
        time.sleep(random.uniform(args.interval * 0.5, args.interval * 1.5))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
