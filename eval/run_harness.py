"""Eval harness runner.

No LLM calls, no HTTP: calls query_pipeline._diagnose() (the same in-process,
no-LLM decision core the /query endpoint uses -- router, incident
partitioning, confidence, TF-IDF retrieval) directly, exactly the way
backend/eval/verify_routing.py already does. run_query() and the live
REPO_PATH/indexer are never touched.

Steps:
  1. Build a SEPARATE CodeIndexer on eval/_sanitized/packages, assert its
     graph == the 7 real edges.
  2. Build a second SEPARATE CodeIndexer on the synthetic renamed-graph
     fixture (renamed_graph category only).
  3. For every scenario in eval/reference_answers.json: read its generated
     .log file (eval/scenarios_generated/<id>.log) as-is, no replay, no
     wall-clock -- `now` = that file's own last line's timestamp. Run
     _diagnose() TWICE (determinism check) and score against the reference
     answer.
  4. Also run the TEST-split "sanitized" scenarios once more against the
     ORIGINAL, still-commented mock-codebase2/packages (read-only) and
     report the accuracy gap.
  5. Write eval/runs/ (raw per-run rows), eval/results.json, eval/results.md.

Run: python eval/run_harness.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from code_indexer import CodeIndexer, display_name  # noqa: E402
from log_analyzer import LogAnalyzer, LINE_RE  # noqa: E402
import query_pipeline as qp  # noqa: E402
from explain import confidence_reason  # noqa: E402

SANITIZED_PACKAGES = HERE / "_sanitized" / "packages"
ORIGINAL_PACKAGES = ROOT / "mock-codebase2" / "packages"
SYNTHETIC_PACKAGES = HERE / "fixtures_synthetic_graph" / "packages"
SCENARIOS_DIR = HERE / "scenarios_generated"
REFERENCE_PATH = HERE / "reference_answers.json"
RUNS_DIR = HERE / "runs"
RESULTS_JSON = HERE / "results.json"
RESULTS_MD = HERE / "results.md"

EXPECTED_EDGES = {
    ("api-gateway", "orders-service"), ("orders-service", "payment-service"),
    ("orders-service", "db-pool"), ("orders-service", "notify-worker"),
    ("orders-service", "ledger-worker"), ("ledger-worker", "db-pool"),
    ("payment-service", "db-pool"),
}


def _display_edges(indexer: CodeIndexer) -> set[tuple[str, str]]:
    _, edges = indexer.graph()
    return {(display_name(a), display_name(b)) for a, b in edges}


def _last_line_ts(log_path: Path) -> datetime:
    lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    m = LINE_RE.match(lines[-1])
    if not m:
        raise ValueError(f"{log_path}: last line doesn't parse: {lines[-1]!r}")
    return datetime.fromisoformat(m.group(1))


def _diagnose_scenario(indexer: CodeIndexer, services: dict[str, str], scenario: dict, log_path: Path) -> dict:
    now = _last_line_ts(log_path)
    la = LogAnalyzer(str(log_path))
    anomalies = la.anomalies(now=now)
    d = qp._diagnose(scenario["question"], anomalies, indexer, services, now=now)

    primary = d["incidents"][d["primary_idx"]] if d["primary_idx"] is not None else dict(qp._EMPTY_INCIDENT)
    primary_conf = d["confidences"][d["primary_idx"]] if d["primary_idx"] is not None else qp._compute_confidence(0, 0, 0, 0.0)
    primary_competing = d["competing_candidates"][d["primary_idx"]] if d["primary_idx"] is not None else []
    reason = confidence_reason(primary, primary_conf, primary_competing, qp.CONFIG["EVIDENCE_DIVISOR"])

    # Replicate run_query()'s scoping rule for which incidents are actually
    # shown (see query_pipeline.run_query, "SPECIFIC + found -> only that one
    # incident" block) -- same replication backend/eval/verify_routing.py
    # already uses, since _diagnose() itself always returns every incident
    # (needed to score all of them), and this scoping is what a real answer
    # would show the user.
    if d["mode"] == "specific" and d["answer_type"] == "incident":
        shown_roots = {primary["root"]} if primary["root"] else set()
    elif d["mode"] == "unknown_service":
        shown_roots = set()
    else:
        shown_roots = {inc["root"] for inc in d["incidents"] if inc["root"]}

    chain = d["chain"] if (d["mode"] == "specific" and primary.get("label") == "single") else None
    label = primary_conf["label"] if (primary.get("label") not in (None, "none") and d["answer_type"] == "incident") else None

    return {
        "mode": d["mode"], "answer_type": d["answer_type"],
        "roots": sorted(shown_roots), "primary_root": primary.get("root"), "chain": chain,
        "label": label, "score": primary_conf["score"], "signals": primary_conf["signals"],
        "activity": primary.get("activity"), "last_error_age_s": primary.get("last_error_age_s"),
        "competing_candidates": [c["service"] for c in primary_competing],
        "confidence_reason": reason,
        "failing_services": primary.get("failing_services", []), "root": primary.get("root"),
        "candidates": primary.get("candidates", []), "symptoms": primary.get("symptoms", []),
        "root_errors": primary.get("root_errors", 0),
    }


def _match(expected: dict, actual: dict, mode: str) -> bool:
    et = expected["answer_type"]
    if et in ("healthy", "unknown_service", "none"):
        return actual["answer_type"] == et
    if actual["answer_type"] != "incident":
        return False
    roots_ok = set(actual["roots"]) == set(expected["roots"]) and actual["primary_root"] == expected["primary_root"]
    chain_ok = True
    if mode == "specific" and expected.get("chain") is not None:
        chain_ok = actual["chain"] == expected["chain"]
    ambiguous_ok = True
    if expected.get("label") == "low" and expected.get("competing"):
        ambiguous_ok = actual["label"] == "low" and set(actual["competing_candidates"]) == set(expected["competing"])
    return roots_ok and chain_ok and ambiguous_ok


def _verdict(match: bool, actual_label: str | None, expected: dict) -> str:
    if expected["answer_type"] in ("healthy", "unknown_service", "none"):
        if match:
            return "correct abstention"
        return "wrong but confident" if actual_label == "high" else "wrong, honestly unsure"
    if match:
        if actual_label == "high":
            return "correct and confident"
        return "correct but hedged" if expected.get("label") == "high" else "correctly uncertain"
    return "wrong but confident" if actual_label == "high" else "wrong, honestly unsure"


def run_all(indexer_by_repo: dict[str, CodeIndexer], services_by_repo: dict[str, dict[str, str]],
            scenarios: dict[str, dict], run_tag: str, only_ids: set[str] | None = None) -> list[dict]:
    rows = []
    for sid, sc in sorted(scenarios.items()):
        if only_ids is not None and sid not in only_ids:
            continue
        log_path = SCENARIOS_DIR / f"{sid}.log"
        indexer = indexer_by_repo[sc["repo"]]
        services = services_by_repo[sc["repo"]]
        run1 = _diagnose_scenario(indexer, services, sc, log_path)
        run2 = _diagnose_scenario(indexer, services, sc, log_path)
        consistent = run1 == run2
        expected = sc["expected"]
        matched = _match(expected, run1, sc["mode"])
        verdict = _verdict(matched, run1["label"], expected)
        activity_correct = run1["activity"] == expected.get("activity")
        row = {
            "id": sid, "category": sc["category"], "split": sc["split"], "mode": sc["mode"],
            "question": sc["question"], "expected": expected, "actual": run1,
            "match": matched, "verdict": verdict, "consistency": consistent, "activity_correct": activity_correct,
            "failing_services": run1["failing_services"], "root": run1["root"], "candidates": run1["candidates"],
            "symptoms": run1["symptoms"], "root_errors": run1["root_errors"], "label": run1["label"],
            "score": run1["score"], "signals": run1["signals"], "activity": run1["activity"],
            "confidence_reason": run1["confidence_reason"], "competing_candidates": run1["competing_candidates"],
            "is_eval": True,
        }
        rows.append(row)
    (RUNS_DIR).mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{run_tag}.json").write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
    return rows


def _bucket(score: float) -> str:
    if score < 0.5:
        return "<0.5"
    if score < 0.65:
        return "0.5-0.65"
    if score < 0.8:
        return "0.65-0.8"
    return ">0.8"


def compute_metrics(rows: list[dict]) -> dict:
    def frac(sub):
        n = len(sub)
        k = sum(1 for r in sub if r["match"])
        return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None}

    m: dict = {"overall": frac(rows)}
    by_cat: dict[str, dict] = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    m["per_category"] = {c: frac(rs) for c, rs in sorted(by_cat.items())}

    high = [r for r in rows if r["label"] == "high"]
    m["high_confidence_precision"] = frac(high)
    wrong_high = [r for r in high if not r["match"]]
    m["false_confidence_rate"] = {"k": len(wrong_high), "n": len(high), "pct": round(100 * len(wrong_high) / len(high), 1) if high else None}

    expected_high = [r for r in rows if r["expected"].get("label") == "high"]
    over_abstain = [r for r in expected_high if r["label"] == "low"]
    m["over_abstention"] = {"k": len(over_abstain), "n": len(expected_high), "pct": round(100 * len(over_abstain) / len(expected_high), 1) if expected_high else None}

    buckets = {"<0.5": [], "0.5-0.65": [], "0.65-0.8": [], ">0.8": []}
    for r in rows:
        buckets[_bucket(r["score"])].append(r)
    m["calibration"] = {b: frac(rs) for b, rs in buckets.items()}

    m["consistency"] = frac2 = {"k": sum(1 for r in rows if r["consistency"]), "n": len(rows)}
    frac2["pct"] = round(100 * frac2["k"] / frac2["n"], 1) if rows else None

    act_checked = [r for r in rows if r["expected"].get("activity") is not None]
    m["activity_accuracy"] = {
        "k": sum(1 for r in act_checked if r["activity_correct"]), "n": len(act_checked),
        "pct": round(100 * sum(1 for r in act_checked if r["activity_correct"]) / len(act_checked), 1) if act_checked else None,
    }
    return m


def write_results_md(all_rows_by_split: dict[str, list[dict]], metrics_by_split: dict[str, dict],
                      baseline_gap: dict) -> None:
    lines = ["# ARGUS eval harness results", ""]
    for split in ("test", "tune"):
        rows = all_rows_by_split[split]
        m = metrics_by_split[split]
        lines.append(f"## {split.upper()} split ({'headline' if split == 'test' else 'tuning'}) -- {m['overall']['k']} of {m['overall']['n']} correct ({m['overall']['pct']}%)")
        lines.append("")
        lines.append("| id | category | mode | expected | actual | match | verdict | consistent |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in sorted(rows, key=lambda r: (r["category"], r["id"])):
            exp = r["expected"]
            act = r["actual"]
            exp_s = exp["answer_type"] if exp["answer_type"] != "incident" else f"root={exp.get('primary_root')} label={exp.get('label')}"
            act_s = act["answer_type"] if act["answer_type"] != "incident" else f"root={act.get('primary_root')} label={act.get('label')}"
            lines.append(f"| {r['id']} | {r['category']} | {r['mode']} | {exp_s} | {act_s} | {'✓' if r['match'] else '✗'} | {r['verdict']} | {'✓' if r['consistency'] else '✗'} |")
        lines.append("")
        lines.append("### Metrics")
        lines.append(f"- Overall accuracy: {m['overall']['k']} of {m['overall']['n']} ({m['overall']['pct']}%)")
        lines.append(f"- High-confidence precision: {m['high_confidence_precision']['k']} of {m['high_confidence_precision']['n']} ({m['high_confidence_precision']['pct']}%)")
        lines.append(f"- False-confidence rate (wrong among high): {m['false_confidence_rate']['k']} of {m['false_confidence_rate']['n']} ({m['false_confidence_rate']['pct']}%)")
        lines.append(f"- Over-abstention (expected high, labeled low): {m['over_abstention']['k']} of {m['over_abstention']['n']} ({m['over_abstention']['pct']}%)")
        lines.append(f"- Consistency (2 runs identical): {m['consistency']['k']} of {m['consistency']['n']} ({m['consistency']['pct']}%)")
        lines.append(f"- Activity accuracy: {m['activity_accuracy']['k']} of {m['activity_accuracy']['n']} ({m['activity_accuracy']['pct']}%)")
        lines.append("")
        lines.append("Per-category:")
        for c, cm in m["per_category"].items():
            lines.append(f"- {c}: {cm['k']} of {cm['n']} ({cm['pct']}%)")
        lines.append("")
        lines.append("Calibration by score bucket:")
        for b, cm in m["calibration"].items():
            lines.append(f"- {b}: {cm['k']} of {cm['n']} correct ({cm['pct']}%)" if cm["n"] else f"- {b}: 0 of 0")
        lines.append("")

    lines.append("## Failures (test split, wrong-but-confident first)")
    fails = [r for r in all_rows_by_split["test"] if not r["match"]]
    fails.sort(key=lambda r: (r["verdict"] != "wrong but confident", r["id"]))
    if not fails:
        lines.append("None.")
    for r in fails:
        lines.append(f"### {r['id']} ({r['category']}, {r['mode']}) -- {r['verdict']}")
        lines.append(f"- Question: {r['question']}")
        lines.append(f"- Expected: {r['expected']}")
        lines.append(f"- Actual: {r['actual']}")
        lines.append(f"- Logs: {r['failing_services']}, root_errors={r['root_errors']}")
        lines.append(f"- Why: {r['confidence_reason']}")
        lines.append("")

    lines.append("## Original-vs-sanitized codebase gap (test split, sanitized-repo scenarios only)")
    lines.append(f"- Sanitized accuracy: {baseline_gap['sanitized']['k']} of {baseline_gap['sanitized']['n']} ({baseline_gap['sanitized']['pct']}%)")
    lines.append(f"- Original (commented) accuracy: {baseline_gap['original']['k']} of {baseline_gap['original']['n']} ({baseline_gap['original']['pct']}%)")
    lines.append(f"- Gap: {baseline_gap['gap_pct']} percentage points")
    lines.append("")

    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ref = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    scenarios = ref["scenarios"]

    sanitized_indexer = CodeIndexer(str(SANITIZED_PACKAGES))
    got_edges = _display_edges(sanitized_indexer)
    if got_edges != EXPECTED_EDGES:
        print(f"GRAPH MISMATCH on {SANITIZED_PACKAGES}: expected {sorted(EXPECTED_EDGES)}, got {sorted(got_edges)}")
        raise SystemExit(1)
    synthetic_indexer = CodeIndexer(str(SYNTHETIC_PACKAGES))

    indexer_by_repo = {"sanitized": sanitized_indexer, "synthetic": synthetic_indexer}
    services_by_repo = {r: qp._service_ids(ix) for r, ix in indexer_by_repo.items()}

    all_rows = run_all(indexer_by_repo, services_by_repo, scenarios, run_tag="sanitized_all")
    by_split = {"tune": [r for r in all_rows if r["split"] == "tune"], "test": [r for r in all_rows if r["split"] == "test"]}
    metrics_by_split = {s: compute_metrics(rs) for s, rs in by_split.items()}

    # Headline gap: TEST split, sanitized-repo scenarios only, against the
    # ORIGINAL (still-commented) mock-codebase2/packages -- read-only, never
    # modified, never the live indexer.
    original_indexer = CodeIndexer(str(ORIGINAL_PACKAGES))
    original_services = qp._service_ids(original_indexer)
    sanitized_test_ids = {sid for sid, sc in scenarios.items() if sc["split"] == "test" and sc["repo"] == "sanitized"}
    orig_rows = run_all({"sanitized": original_indexer}, {"sanitized": original_services}, scenarios, run_tag="original_headline", only_ids=sanitized_test_ids)

    def frac(rs):
        k = sum(1 for r in rs if r["match"])
        n = len(rs)
        return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None}

    sanitized_test_sub = [r for r in by_split["test"] if r["id"] in sanitized_test_ids]
    baseline_gap = {"sanitized": frac(sanitized_test_sub), "original": frac(orig_rows)}
    baseline_gap["gap_pct"] = round((baseline_gap["sanitized"]["pct"] or 0) - (baseline_gap["original"]["pct"] or 0), 1)

    RESULTS_JSON.write_text(json.dumps({
        "seed": ref["seed"], "generated_at": ref["generated_at"], "run_at": datetime.now().isoformat(timespec="seconds"),
        "rows": all_rows, "summary": {"tune": metrics_by_split["tune"], "test": metrics_by_split["test"], "baseline_gap": baseline_gap},
    }, indent=2, default=str) + "\n", encoding="utf-8")

    write_results_md(by_split, metrics_by_split, baseline_gap)

    print(f"TEST  : {metrics_by_split['test']['overall']['k']} of {metrics_by_split['test']['overall']['n']} correct ({metrics_by_split['test']['overall']['pct']}%)")
    print(f"TUNE  : {metrics_by_split['tune']['overall']['k']} of {metrics_by_split['tune']['overall']['n']} correct ({metrics_by_split['tune']['overall']['pct']}%)")
    print(f"Failures (test): {sum(1 for r in by_split['test'] if not r['match'])} of {len(by_split['test'])}")
    print(f"Original-vs-sanitized gap: {baseline_gap['gap_pct']} pts (sanitized {baseline_gap['sanitized']['pct']}% vs original {baseline_gap['original']['pct']}%)")
    print(f"Wrote {RESULTS_JSON}")
    print(f"Wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
