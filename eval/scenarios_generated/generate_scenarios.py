"""Generates the eval harness's labeled scenarios (Prompt: "build the
evaluation harness").

Ground truth is derived from two things only, never from running the
pipeline:
  1. The real 7-edge dependency graph (asserted separately by the harness
     against the sanitized CodeIndexer), or the small synthetic graph used
     by the renamed_graph category.
  2. query_pipeline.CONFIG's real thresholds (imported, never re-typed),
     applied to the exact error/warn counts and timings this script itself
     chooses for each scenario.

For a single competitor, score = 0.4*evidence + 0.35*1.0 + 0.25*relevance.
Relevance (TF-IDF cosine) is NOT predicted here -- instead every hand-built
scenario is deliberately kept in the zone where the label is the same at
relevance=0 and relevance=1 (>=15 weighted errors -> guaranteed "high" per
the current CONFIG values; <2.5 -> guaranteed "low"), so the expected label
is certain without peeking at retrieval. The three reused
eval/fixtures_thin/ fixtures (low_volume category) fall in the genuinely
uncertain middle by construction (they're real fixtures, not authored by
this script) -- they're marked "borderline": true and still get an expected
label ("low", matching the category's intent), but a mismatch there is a
legitimate finding, not a harness bug.

Two or more competitors always forces "low" regardless of relevance (see
query_pipeline._compute_confidence) -- deterministic either way.

Output (gitignored except this script -- see .gitignore / CLAUDE.md):
  eval/scenarios_generated/<id>.log   -- the raw log fixture, real
                                          timestamps, no labels inside
  eval/reference_answers.json          -- {id: {category, question, mode,
                                          target, repo, split, expected}}

Run: python eval/scenarios_generated/generate_scenarios.py
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL_DIR = HERE.parent
ROOT = EVAL_DIR.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
from query_pipeline import CONFIG  # noqa: E402

SEED = 20260928
rng = random.Random(SEED)

OUT_LOGS = HERE
REFERENCE_PATH = EVAL_DIR / "reference_answers.json"
THIN_DIR = EVAL_DIR / "fixtures_thin"

# ---- sanitized-graph service names (must match the 7-edge graph the
# harness asserts against eval/_sanitized/packages) --------------------------
AG, OS, PS, DB, NW, LW = "api-gateway", "orders-service", "payment-service", "db-pool", "notify-worker", "ledger-worker"
SANITIZED = "sanitized"

# ---- synthetic-graph service names (renamed_graph category only) ----------
FD, CR, BU, AS = "front-door", "core-router", "billing-unit", "archive-store"
SYNTHETIC = "synthetic"

ANCHOR0 = datetime(2026, 9, 28, 9, 0, 0)
_order_ctr = [10000]


def _oid() -> str:
    _order_ctr[0] += 1
    return f"ord_{_order_ctr[0]}"


def _ts(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def _fmtline(t: datetime, level: str, svc: str, msg: str) -> str:
    return f"{_ts(t)} {level} {svc} {msg}"


def mk(anchor: datetime, events: list[tuple[float, str, str, str]]) -> tuple[list[str], datetime]:
    """events: (offset_seconds_before_anchor, LEVEL, service, message).
    Always appends one final INFO filler line at offset 0 (the anchor
    itself), so "now" == the file's real last line, exactly, every time.
    Returns (sorted formatted lines, anchor)."""
    all_events = list(events) + [(0.0, "INFO", "notify-worker" if events and events[0][2] != "front-door" and events[0][2] not in (FD, CR, BU, AS) else "front-door", f"heartbeat {_oid()}")]
    rows = []
    for off, lvl, svc, msg in all_events:
        t = anchor - timedelta(seconds=off)
        rows.append((t, _fmtline(t, lvl, svc, msg)))
    rows.sort(key=lambda p: p[0])
    return [l for _, l in rows], anchor


def burst(service: str, n: int, template: str, last_offset_s: float, spread_s: float, level: str = "ERROR") -> list[tuple[float, str, str, str]]:
    """n events on `service`, the LAST one `last_offset_s` seconds before the
    anchor, spread evenly backward across `spread_s` seconds before that."""
    out = []
    step = spread_s / max(n - 1, 1)
    for i in range(n):
        off = last_offset_s + (n - 1 - i) * step
        out.append((off, level, service, template.format(o=_oid())))
    return out


def weighted(errors: float, warns: float) -> float:
    return errors + CONFIG["WARNING_WEIGHT"] * warns


def expected_label(root_errors: float, root_warns: float, num_competitors: int) -> tuple[str | None, bool]:
    """Returns (label, borderline). borderline=True means the label is NOT
    certain from evidence+dominance alone (relevance-dependent) -- every
    hand-authored scenario below asserts borderline is False for itself."""
    if num_competitors > 1:
        return "low", False
    if root_errors <= 0:
        return None, False
    w = weighted(root_errors, root_warns)
    evidence = min(w / CONFIG["EVIDENCE_DIVISOR"], 1.0)
    lo = CONFIG["WEIGHT_EVIDENCE"] * evidence + CONFIG["WEIGHT_DOMINANCE"] * 1.0
    hi = lo + CONFIG["WEIGHT_RELEVANCE"] * 1.0
    if lo >= CONFIG["HIGH_THRESHOLD"]:
        return "high", False
    if hi < CONFIG["HIGH_THRESHOLD"]:
        return "low", False
    return "low", True  # matches category intent for the 3 reused thin fixtures; flagged


def expected_activity(last_error_offset_s: float | None) -> str | None:
    if last_error_offset_s is None:
        return None
    return "ongoing" if last_error_offset_s <= CONFIG["ONGOING_CUTOFF_S"] else "stopped"


SCENARIOS: list[dict] = []


def add(id_, category, question, mode, target, repo, lines, expected):
    if not expected.get("borderline") and expected.get("label") not in (None, "high", "low"):
        raise ValueError(f"{id_}: bad label {expected.get('label')!r}")
    SCENARIOS.append({
        "id": id_, "category": category, "question": question, "mode": mode,
        "target": target, "repo": repo, "lines": lines, "expected": expected,
    })


def base_expected(answer_type="incident", roots=(), primary_root=None, chain=None,
                   label=None, activity=None, competing=(), borderline=False) -> dict:
    return {
        "answer_type": answer_type, "roots": sorted(set(roots)), "primary_root": primary_root,
        "chain": chain, "label": label, "activity": activity,
        "competing": sorted(set(competing)), "borderline": borderline,
    }


# =============================================================================
# 1) single_fault -- each planted bug, varied volume and timing (6)
# =============================================================================
for i, (n, off, spread) in enumerate([(30, 8, 200), (18, 20, 240), (45, 3, 260)]):
    anchor = ANCHOR0 + timedelta(hours=i)
    ev = burst(PS, n, "gateway.charge timeout after 3000ms order={o}", off, spread)
    lines, _ = mk(anchor, ev)
    lbl, bd = expected_label(n, 0, 1)
    mode = "specific" if i == 2 else "general"
    q = "What is wrong with payment-service?" if mode == "specific" else "What is happening in the system right now?"
    add(f"sf-bug1-{i+1:02d}", "single_fault", q, mode, PS if mode == "specific" else None, SANITIZED, lines,
        base_expected(roots=[PS], primary_root=PS, chain=[PS] if mode == "specific" else None,
                       label=lbl, activity=expected_activity(off), borderline=bd))

for i, (n, off, spread) in enumerate([(32, 6, 220), (16, 25, 180), (40, 2, 270)]):
    anchor = ANCHOR0 + timedelta(hours=10 + i)
    ev = (burst(DB, n, "connection pool exhausted order={o} code=POOL_EXHAUSTED active=5 max=5", off, spread)
          + burst(PS, max(n // 3, 5), "transaction record failed order={o} code=POOL_EXHAUSTED", off + 0.3, spread)
          + burst(LW, max(n // 3, 5), "ledger write failed order={o} code=POOL_EXHAUSTED", off + 0.7, spread)
          + burst(OS, max(n // 3, 5), "order save failed order={o} code=POOL_EXHAUSTED", off + 1.1, spread))
    lines, _ = mk(anchor, ev)
    lbl, bd = expected_label(n, 0, 1)
    mode = "specific" if i == 1 else "general"
    q = "What is wrong with db-pool?" if mode == "specific" else "What is happening in the system right now?"
    add(f"sf-bug2-{i+1:02d}", "single_fault", q, mode, DB if mode == "specific" else None, SANITIZED, lines,
        base_expected(roots=[DB], primary_root=DB, chain=[DB] if mode == "specific" else None,
                       label=lbl, activity=expected_activity(off), borderline=bd))

# =============================================================================
# 2) cascade -- ask about the root AND about a victim (4)
# =============================================================================
for i, (n, off, spread) in enumerate([(30, 5, 230), (55, 10, 260)]):
    anchor = ANCHOR0 + timedelta(hours=20 + i)
    ev = (burst(DB, n, "connection pool exhausted order={o} code=POOL_EXHAUSTED active=5 max=5", off, spread)
          + burst(PS, n, "transaction record failed order={o} code=POOL_EXHAUSTED", off + 0.3, spread)
          + burst(LW, n, "ledger write failed order={o} code=POOL_EXHAUSTED", off + 0.6, spread)
          + burst(OS, n, "order save failed order={o} code=POOL_EXHAUSTED", off + 0.9, spread))
    lines, _ = mk(anchor, ev)
    lbl, bd = expected_label(n, 0, 1)
    act = expected_activity(off)
    # root question
    add(f"cas-root-{i+1:02d}", "cascade", "What is happening in the system right now?", "general", None, SANITIZED, lines,
        base_expected(roots=[DB], primary_root=DB, chain=[AG, OS, DB], label=lbl, activity=act, borderline=bd))
    # victim question (payment-service for i=0, ledger-worker for i=1)
    victim = PS if i == 0 else LW
    add(f"cas-victim-{i+1:02d}", "cascade", f"What is wrong with {victim}?", "specific", victim, SANITIZED, lines,
        base_expected(roots=[DB], primary_root=DB, chain=[victim, DB], label=lbl, activity=act, borderline=bd))

# =============================================================================
# 3) clean -- no warnings or errors at all (3)
# =============================================================================
for i, (question, mode, target) in enumerate([
    ("What is happening in the system right now?", "general", None),
    ("What is wrong with orders-service?", "specific", OS),
    ("What is wrong with notify-worker?", "specific", NW),
]):
    anchor = ANCHOR0 + timedelta(hours=30 + i)
    ev = [(200 - k * 20, "INFO", AG, f"request routed order={_oid()}") for k in range(6)]
    lines, _ = mk(anchor, ev)
    add(f"clean-{i+1:02d}", "clean", question, mode, target, SANITIZED, lines,
        base_expected(answer_type="healthy", roots=[], primary_root=None, label=None, activity=None))

# =============================================================================
# 4) noisy_warnings -- warnings only, zero errors anywhere (3)
# =============================================================================
for i, (question, mode, target) in enumerate([
    ("What is happening in the system right now?", "general", None),
    ("What is wrong with payment-service?", "specific", PS),
    ("What is happening in the system right now?", "general", None),
]):
    anchor = ANCHOR0 + timedelta(hours=40 + i)
    ev = (burst(PS, 12, "elevated latency order={o} latency=1800ms", 10, 200, level="WARN")
          + burst(DB, 8, "connection pool nominal but slow active=4 idle=1 order={o}", 30, 200, level="WARN")
          + [(150, "WARN", AG, "elevated latency downstream p95=1800ms window=60s")])
    lines, _ = mk(anchor, ev)
    add(f"nw-{i+1:02d}", "noisy_warnings", question, mode, target, SANITIZED, lines,
        base_expected(answer_type="healthy", roots=[], primary_root=None, label=None, activity=None))

# =============================================================================
# 5) low_volume -- reuse eval/fixtures_thin verbatim (3), thin evidence
# =============================================================================
_THIN = [
    ("lv-cascade-01", "scenario-cascading-failure.log",
     "What is happening in the system right now?", "general", None,
     base_expected(roots=[DB], primary_root=DB, label="low", activity="ongoing", borderline=True)),
    ("lv-dbexh-01", "scenario-db-exhaustion.log",
     "What is happening in the system right now?", "general", None,
     base_expected(roots=[DB], primary_root=DB, label="low", activity="ongoing", borderline=True)),
    ("lv-paytimeout-01", "scenario-payment-timeout.log",
     "What is wrong with payment-service?", "specific", PS,
     base_expected(roots=[PS], primary_root=PS, chain=[PS], label="low", activity="ongoing", borderline=True)),
]
for id_, fname, q, mode, target, expected in _THIN:
    text = (THIN_DIR / fname).read_text(encoding="utf-8")
    lines = [l for l in text.splitlines() if l.strip()]
    add(id_, "low_volume", q, mode, target, SANITIZED, lines, expected)

# =============================================================================
# 6) two_unrelated_faults -- both incidents, separately (3)
# =============================================================================
for i, (nA, nB) in enumerate([(30, 30), (20, 22)]):
    anchor = ANCHOR0 + timedelta(hours=50 + i)
    ev = (burst(NW, nA, "email send failed order={o} code=SMTP_ERROR", 6, 230)
          + burst(LW, nB, "ledger write failed order={o} code=LEDGER_DOWN", 12, 230))
    lines, _ = mk(anchor, ev)
    lblA, bdA = expected_label(nA, 0, 1)
    lblB, bdB = expected_label(nB, 0, 1)
    # Real tie-break (query_pipeline._partition_incidents): primary incident
    # is highest total weighted errors, ties broken by root NAME ascending --
    # not by which of nA/nB is declared first. Equal counts here (30==30)
    # means "ledger-worker" wins the tie (alphabetically first).
    strongest, lbl = sorted([(NW, nA, lblA), (LW, nB, lblB)], key=lambda t: (-t[1], t[0]))[0][0::2]
    add(f"tuf-general-{i+1:02d}", "two_unrelated_faults", "What is happening in the system right now?", "general", None, SANITIZED, lines,
        base_expected(roots=[NW, LW], primary_root=strongest, label=lbl, activity="ongoing", borderline=bdA or bdB))
anchor = ANCHOR0 + timedelta(hours=52)
ev = burst(NW, 30, "email send failed order={o} code=SMTP_ERROR", 6, 230) + burst(LW, 30, "ledger write failed order={o} code=LEDGER_DOWN", 12, 230)
lines, _ = mk(anchor, ev)
add("tuf-specific-01", "two_unrelated_faults", "What is wrong with notify-worker?", "specific", NW, SANITIZED, lines,
    base_expected(roots=[NW], primary_root=NW, chain=[NW], label="high", activity="ongoing"))

# =============================================================================
# 7) stale_logs -- errors older than the 30-minute lookback (3)
# =============================================================================
for i, (svc, root_display, off) in enumerate([(DB, DB, 2200), (PS, PS, 2600), (LW, LW, 3000)]):
    anchor = ANCHOR0 + timedelta(hours=60 + i)
    ev = burst(svc, 30, "failure order={o} code=STALE", off, 200)
    lines, _ = mk(anchor, ev)
    mode = "specific" if i == 1 else "general"
    q = f"What is wrong with {root_display}?" if mode == "specific" else "What is happening in the system right now?"
    add(f"sl-{i+1:02d}", "stale_logs", q, mode, root_display if mode == "specific" else None, SANITIZED, lines,
        base_expected(answer_type="healthy", roots=[], primary_root=None, label=None, activity=None))

# =============================================================================
# 8) mixed_errors -- many unrelated messages on one service, plus a clear root (3)
# =============================================================================
for i, (svc, mode) in enumerate([(NW, "general"), (LW, "specific"), (PS, "general")]):
    anchor = ANCHOR0 + timedelta(hours=70 + i)
    n = 30
    ev = burst(svc, n, "operation failed order={o} code=ERR", 5, 230)
    noise = []
    for other in (AG, OS, DB, LW if svc != LW else NW, PS if svc != PS else AG):
        noise += burst(other, 15, "latency spike order={o} p95=900ms", rng.uniform(20, 200), 200, level="WARN")
        noise += [(rng.uniform(20, 200), "INFO", other, f"request routed order={_oid()}") for _ in range(10)]
    lines, _ = mk(anchor, ev + noise)
    lbl, bd = expected_label(n, 0, 1)
    q = f"What is wrong with {svc}?" if mode == "specific" else "What is happening in the system right now?"
    add(f"me-{i+1:02d}", "mixed_errors", q, mode, svc if mode == "specific" else None, SANITIZED, lines,
        base_expected(roots=[svc], primary_root=svc, chain=[svc] if mode == "specific" else None,
                       label=lbl, activity="ongoing", borderline=bd))

# =============================================================================
# 9) recently_stopped -- errors ended 1-4 min before reference time (3)
# =============================================================================
for i, (svc, n, off) in enumerate([(DB, 30, 120), (PS, 25, 210), (NW, 20, 72)]):
    anchor = ANCHOR0 + timedelta(hours=80 + i)
    if svc == DB:
        ev = (burst(DB, n, "connection pool exhausted order={o} code=POOL_EXHAUSTED active=5 max=5", off, 200)
              + burst(PS, n, "transaction record failed order={o} code=POOL_EXHAUSTED", off + 0.3, 200)
              + burst(LW, n, "ledger write failed order={o} code=POOL_EXHAUSTED", off + 0.6, 200)
              + burst(OS, n, "order save failed order={o} code=POOL_EXHAUSTED", off + 0.9, 200))
        root, chain_root = DB, [AG, OS, DB]
    else:
        ev = burst(svc, n, "operation failed order={o} code=ERR", off, 200)
        root, chain_root = svc, [svc]
    lines, _ = mk(anchor, ev)
    lbl, bd = expected_label(n, 0, 1)
    mode = "specific" if i == 1 else "general"
    q = f"What is wrong with {root}?" if mode == "specific" else "What is happening in the system right now?"
    add(f"rs-{i+1:02d}", "recently_stopped", q, mode, root if mode == "specific" else None, SANITIZED, lines,
        base_expected(roots=[root], primary_root=root, chain=chain_root if mode == "specific" else None,
                       label=lbl, activity="stopped", borderline=bd))

# =============================================================================
# 10) two_upstream_roots -- orders-service (disqualified parent) + 2 sibling
#     candidates it calls (payment-service, notify-worker), both clearing the
#     competitor floor -> ambiguous, low, both named (3)
# =============================================================================
for i, (nPS, nNW, nOS, off) in enumerate([(30, 28, 6, 8), (40, 12, 5, 5)]):
    anchor = ANCHOR0 + timedelta(hours=90 + i)
    ev = (burst(PS, nPS, "gateway.charge timeout after 3000ms order={o}", off, 220)
          + burst(NW, nNW, "email send failed order={o} code=SMTP_ERROR", off + 0.4, 220)
          + burst(OS, nOS, "order save failed order={o} code=DOWNSTREAM_ERROR", off + 0.2, 220))
    lines, _ = mk(anchor, ev)
    strongest = PS if nPS >= nNW else NW
    add(f"tur-{i+1:02d}", "two_upstream_roots", "What is happening in the system right now?", "general", None, SANITIZED, lines,
        base_expected(roots=[strongest], primary_root=strongest, label="low", activity="ongoing", competing=[PS, NW]))
anchor = ANCHOR0 + timedelta(hours=92)
ev = (burst(PS, 30, "gateway.charge timeout after 3000ms order={o}", 8, 220)
      + burst(NW, 28, "email send failed order={o} code=SMTP_ERROR", 8.4, 220)
      + burst(OS, 6, "order save failed order={o} code=DOWNSTREAM_ERROR", 8.2, 220))
lines, _ = mk(anchor, ev)
add("tur-specific-01", "two_upstream_roots", "What is wrong with orders-service?", "specific", OS, SANITIZED, lines,
    base_expected(roots=[PS], primary_root=PS, chain=None, label="low", activity="ongoing", competing=[PS, NW]))

# =============================================================================
# 11) three_upstream_roots -- 394 / 180 / 150 (3)
# =============================================================================
for i, (nPS, nNW, nLW, mode) in enumerate([(394, 180, 150, "general"), (300, 120, 100, "general"), (394, 180, 150, "specific")]):
    anchor = ANCHOR0 + timedelta(hours=100 + i)
    ev = (burst(PS, nPS, "gateway.charge timeout after 3000ms order={o}", 5, 250)
          + burst(NW, nNW, "email send failed order={o} code=SMTP_ERROR", 5.3, 250)
          + burst(LW, nLW, "ledger write failed order={o} code=LEDGER_DOWN", 5.6, 250)
          + burst(OS, 8, "order save failed order={o} code=DOWNSTREAM_ERROR", 5.1, 250))
    lines, _ = mk(anchor, ev)
    target = PS if mode == "specific" else None
    q = "What is wrong with payment-service?" if mode == "specific" else "What is happening in the system right now?"
    add(f"tur3-{i+1:02d}", "three_upstream_roots", q, mode, target, SANITIZED, lines,
        base_expected(roots=[PS], primary_root=PS, chain=None if mode == "specific" else None, label="low",
                       activity="ongoing", competing=[PS, NW, LW]))

# =============================================================================
# 12) subfloor_competitor -- 394 vs 2: clear root, the 2-error service is minor (3)
# =============================================================================
for i, mode in enumerate(["general", "specific", "specific"]):
    anchor = ANCHOR0 + timedelta(hours=110 + i)
    ev = (burst(PS, 394, "gateway.charge timeout after 3000ms order={o}", 4, 260)
          + burst(NW, 2, "email send failed order={o} code=SMTP_ERROR", 30, 60)
          + burst(OS, 5, "order save failed order={o} code=DOWNSTREAM_ERROR", 4.5, 260))
    lines, _ = mk(anchor, ev)
    if mode == "general":
        target, q = None, "What is happening in the system right now?"
        add(f"sfc-{i+1:02d}", "subfloor_competitor", q, mode, target, SANITIZED, lines,
            base_expected(roots=[PS, NW], primary_root=PS, label="high", activity="ongoing"))
    elif i == 1:  # ask about the strong root
        add(f"sfc-{i+1:02d}", "subfloor_competitor", "What is wrong with payment-service?", "specific", PS, SANITIZED, lines,
            base_expected(roots=[PS], primary_root=PS, chain=[PS], label="high", activity="ongoing"))
    else:  # ask about the subfloor/minor service itself
        add(f"sfc-{i+1:02d}", "subfloor_competitor", "What is wrong with notify-worker?", "specific", NW, SANITIZED, lines,
            base_expected(roots=[NW], primary_root=NW, chain=[NW], label="low", activity="ongoing"))

# =============================================================================
# 13) stray_error -- cascade plus 1 error on a healthy/unrelated service (3)
# =============================================================================
for i, mode in enumerate(["general", "specific", "general"]):
    anchor = ANCHOR0 + timedelta(hours=120 + i)
    if i < 2:
        ev = (burst(DB, 30, "connection pool exhausted order={o} code=POOL_EXHAUSTED active=5 max=5", 5, 230)
              + burst(PS, 10, "transaction record failed order={o} code=POOL_EXHAUSTED", 5.3, 230)
              + burst(NW, 1, "email send failed order={o} code=SMTP_ERROR", 40, 5))
        primary_root, chain_root = DB, [AG, OS, DB]
    else:
        ev = (burst(PS, 30, "gateway.charge timeout after 3000ms order={o}", 5, 230)
              + burst(NW, 1, "email send failed order={o} code=SMTP_ERROR", 40, 5))
        primary_root, chain_root = PS, [PS]
    lines, _ = mk(anchor, ev)
    if mode == "general":
        add(f"se-{i+1:02d}", "stray_error", "What is happening in the system right now?", "general", None, SANITIZED, lines,
            base_expected(roots=[primary_root, NW], primary_root=primary_root, label="high", activity="ongoing"))
    else:
        # Question asks about primary_root itself (the root, not a victim) --
        # _diagnose()'s chain for "target == root" is just [target], never
        # the full entry-to-root path (that's only for general mode / a
        # victim question). See query_pipeline._diagnose's `chain = [target]
        # if target == inc["root"] else ...`.
        add(f"se-{i+1:02d}", "stray_error", f"What is wrong with {primary_root}?", "specific", primary_root, SANITIZED, lines,
            base_expected(roots=[primary_root], primary_root=primary_root, chain=[primary_root], label="high", activity="ongoing"))

# =============================================================================
# 14) healthy_service_question -- specific question about a healthy service,
#     while a real (unrelated) incident may be active elsewhere (3)
# =============================================================================
anchor = ANCHOR0 + timedelta(hours=130)
ev = (burst(DB, 30, "connection pool exhausted order={o} code=POOL_EXHAUSTED active=5 max=5", 5, 230)
      + burst(PS, 30, "transaction record failed order={o} code=POOL_EXHAUSTED", 5.3, 230)
      + burst(LW, 30, "ledger write failed order={o} code=POOL_EXHAUSTED", 5.6, 230)
      + burst(OS, 30, "order save failed order={o} code=POOL_EXHAUSTED", 5.9, 230))
lines, _ = mk(anchor, ev)
add("hsq-01", "healthy_service_question", "What is wrong with notify-worker?", "specific", NW, SANITIZED, lines,
    base_expected(answer_type="healthy", roots=[DB], primary_root=None, label=None, activity=None))

anchor = ANCHOR0 + timedelta(hours=131)
ev = burst(PS, 25, "gateway.charge timeout after 3000ms order={o}", 5, 230)
lines, _ = mk(anchor, ev)
add("hsq-02", "healthy_service_question", "What is wrong with db-pool?", "specific", DB, SANITIZED, lines,
    base_expected(answer_type="healthy", roots=[PS], primary_root=None, label=None, activity=None))

anchor = ANCHOR0 + timedelta(hours=132)
ev = [(200 - k * 20, "INFO", AG, f"request routed order={_oid()}") for k in range(6)]
lines, _ = mk(anchor, ev)
add("hsq-03", "healthy_service_question", "What is wrong with ledger-worker?", "specific", LW, SANITIZED, lines,
    base_expected(answer_type="healthy", roots=[], primary_root=None, label=None, activity=None))

# =============================================================================
# 15) unknown_service_question -- specific question naming a plausible but
#     nonexistent service (3)
# =============================================================================
for i, (fake, log_kind) in enumerate([("shipping-service", "clean"), ("cache-pool", "incident"), ("auth-worker", "clean")]):
    anchor = ANCHOR0 + timedelta(hours=140 + i)
    if log_kind == "incident":
        ev = (burst(DB, 30, "connection pool exhausted order={o} code=POOL_EXHAUSTED active=5 max=5", 5, 230)
              + burst(PS, 30, "transaction record failed order={o} code=POOL_EXHAUSTED", 5.3, 230))
    else:
        ev = [(200 - k * 20, "INFO", AG, f"request routed order={_oid()}") for k in range(6)]
    lines, _ = mk(anchor, ev)
    add(f"usq-{i+1:02d}", "unknown_service_question", f"What is wrong with {fake}?", "specific", fake, SANITIZED, lines,
        base_expected(answer_type="unknown_service", roots=[], primary_root=None, label=None, activity=None))

# =============================================================================
# 16) renamed_graph -- same structures, different service names, to prove
#     nothing is hardcoded (3, separate synthetic CodeIndexer)
# =============================================================================
anchor = ANCHOR0 + timedelta(hours=150)
ev = burst(AS, 30, "archive write failed order={o} code=STORE_ERROR", 5, 230) + burst(BU, 30, "billing settle failed order={o} code=STORE_ERROR", 5.3, 230)
lines, _ = mk(anchor, ev)
lbl, bd = expected_label(30, 0, 1)
add("rg-root-01", "renamed_graph", "What is happening in the system right now?", "general", None, SYNTHETIC, lines,
    base_expected(roots=[AS], primary_root=AS, chain=[FD, CR, AS], label=lbl, activity="ongoing", borderline=bd))

add("rg-victim-01", "renamed_graph", f"What is wrong with {BU}?", "specific", BU, SYNTHETIC, lines,
    base_expected(roots=[AS], primary_root=AS, chain=[BU, AS], label=lbl, activity="ongoing", borderline=bd))

anchor = ANCHOR0 + timedelta(hours=151)
ev = burst(BU, 28, "billing charge timeout order={o} code=GATEWAY_TIMEOUT", 4, 220)
lines, _ = mk(anchor, ev)
lbl, bd = expected_label(28, 0, 1)
add("rg-single-01", "renamed_graph", "What is happening in the system right now?", "general", None, SYNTHETIC, lines,
    base_expected(roots=[BU], primary_root=BU, chain=[FD, CR, BU], label=lbl, activity="ongoing", borderline=bd))

# =============================================================================
# split: 50/50, stratified per category, seeded shuffle
# =============================================================================
by_cat: dict[str, list[str]] = {}
for s in SCENARIOS:
    by_cat.setdefault(s["category"], []).append(s["id"])

split_of: dict[str, str] = {}
odd_flip = 0
for cat, ids in by_cat.items():
    ids_shuf = list(ids)
    rng.shuffle(ids_shuf)
    n = len(ids_shuf)
    half = n // 2
    if n % 2 == 1:
        # alternate which side gets the extra one, so the overall total stays 50/50
        extra_to_tune = (odd_flip % 2 == 0)
        odd_flip += 1
        tune_n = half + 1 if extra_to_tune else half
    else:
        tune_n = half
    for i, sid in enumerate(ids_shuf):
        split_of[sid] = "tune" if i < tune_n else "test"

for s in SCENARIOS:
    s["split"] = split_of[s["id"]]

# =============================================================================
# write outputs
# =============================================================================
for f in OUT_LOGS.glob("*.log"):
    f.unlink()

reference: dict[str, dict] = {}
for s in SCENARIOS:
    (OUT_LOGS / f"{s['id']}.log").write_text("\n".join(s["lines"]) + "\n", encoding="utf-8")
    reference[s["id"]] = {
        "category": s["category"], "question": s["question"], "mode": s["mode"],
        "target": s["target"], "repo": s["repo"], "split": s["split"], "expected": s["expected"],
    }

REFERENCE_PATH.write_text(json.dumps({
    "seed": SEED, "count": len(SCENARIOS), "generated_at": datetime.now().isoformat(timespec="seconds"),
    "scenarios": reference,
}, indent=2) + "\n", encoding="utf-8")

tune_n = sum(1 for s in SCENARIOS if s["split"] == "tune")
test_n = sum(1 for s in SCENARIOS if s["split"] == "test")
print(f"Generated {len(SCENARIOS)} scenarios across {len(by_cat)} categories -> {tune_n} tune / {test_n} test")
for cat, ids in sorted(by_cat.items()):
    t = sum(1 for i in ids if split_of[i] == "tune")
    print(f"  {cat}: {len(ids)} (tune={t}, test={len(ids)-t})")
print(f"Wrote {len(SCENARIOS)} .log files to {OUT_LOGS}")
print(f"Wrote {REFERENCE_PATH}")
