"""Demo scenario switcher.

The scenario log files under mock-codebase2/logs/ ship with fixed, long-past
timestamps (they're static demo fixtures, not a live feed). Pointed at LOG_PATH
as-is, the Log Analyzer would correctly see them as stale and report nothing --
that's not a bug, it's the same "is this actually recent" check that makes the
rest of ARGUS trustworthy. So switching a scenario means replaying its lines
into LOG_PATH with every timestamp shifted by the same delta, chosen so the
scenario's last (most severe) line lands at "now". Relative spacing between
events is preserved exactly; only the anchor point moves.

The scenario fixtures themselves are only ever read, never modified. What DOES
change is LOG_PATH -- replay() overwrites it, so whatever was in there before
(real traffic, or a previously-replayed scenario) would otherwise be silently
lost. backup_current() snapshots it first, so nothing disappears without a copy.
"""
from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# Tolerates an optional trailing "Z" (UTC) the same way log_analyzer.LINE_RE does --
# the scenario files use it, traffic_sim.py's own format doesn't.
_LINE_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3})Z?(\s+.*)$")

SCENARIOS = {
    "payment-timeout": "scenario-payment-timeout.log",
    "db-exhaustion": "scenario-db-exhaustion.log",
    "cascading-failure": "scenario-cascading-failure.log",
    # Test scenarios -- same mock-codebase2/logs/ folder, same replay() mechanism above,
    # no behavior change; just four more named fixtures for the frontend's "Test
    # scenarios" group.
    "two-faults": "test-two-faults.log",
    "stray-error": "test-stray-error.log",
    "thin-evidence": "test-thin-evidence.log",
    "ambiguous-orders": "test-ambiguous-orders.log",
}

MAX_BACKUPS = 20  # oldest ones are pruned so a long demo session doesn't pile up forever


class ScenarioError(Exception):
    pass


def scenarios_dir() -> Path:
    d = os.environ.get("SCENARIOS_PATH")
    if d:
        return Path(d)
    return Path(__file__).parent.parent / "mock-codebase2" / "logs"


def backups_dir(log_path: str) -> Path:
    return Path(log_path).parent / "backups"


def backup_current(log_path: str) -> str | None:
    """Copy whatever's currently at log_path into backups_dir() before it gets
    overwritten. Returns the backup's path, or None if there was nothing to back
    up (file missing or empty) -- switching scenarios back-to-back with nothing
    real in between doesn't need a backup."""
    src = Path(log_path)
    if not src.exists() or src.stat().st_size == 0:
        return None

    dest_dir = backups_dir(log_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = dest_dir / f"{src.stem}-{stamp}{src.suffix}"
    shutil.copy2(src, dest)

    # Prune oldest backups beyond MAX_BACKUPS.
    backups = sorted(dest_dir.glob(f"{src.stem}-*{src.suffix}"), key=lambda p: p.stat().st_mtime)
    for old in backups[:-MAX_BACKUPS]:
        old.unlink(missing_ok=True)

    return str(dest)


def replay(name: str, log_path: str) -> tuple[int, str | None]:
    """Overwrite log_path with the named scenario's lines, timestamps shifted so
    the last line lands at "now". Backs up whatever was there first. Returns
    (lines_written, backup_path_or_None)."""
    if name not in SCENARIOS:
        raise ScenarioError(f"Unknown scenario: {name!r}. Choose one of {sorted(SCENARIOS)}.")
    src = scenarios_dir() / SCENARIOS[name]
    if not src.exists():
        raise ScenarioError(f"Scenario file not found: {src}")

    parsed: list[tuple[datetime, str]] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = _LINE_RE.match(line)
        if m:
            parsed.append((datetime.fromisoformat(m.group(1)), m.group(2)))
    if not parsed:
        raise ScenarioError(f"No parseable log lines in {src}")

    shift = datetime.now() - parsed[-1][0]
    out_lines = []
    for ts, rest in parsed:
        new_ts = ts + shift
        stamp = new_ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{new_ts.microsecond // 1000:03d}"
        out_lines.append(stamp + rest)

    backup_path = backup_current(log_path)

    out_path = Path(log_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return len(out_lines), backup_path
