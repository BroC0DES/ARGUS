"""Log Analyzer: reads the log file fresh from disk on every call.

Line format (written by traffic_sim.py, or any app that follows it):
    2026-09-27T14:22:07.318 ERROR payment-service gateway.charge timeout after 3000ms order=ord_8871

A line's id is `l<byte offset>`: stable while the file only grows, unique, and
ordered chronologically, so ids can be compared and merged client-side.
"""
from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

LINE_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3})\s+(INFO|WARN|ERROR)\s+(\S+)\s+(.*)$")
SEVERITY = {"INFO": "info", "WARN": "warn", "ERROR": "error"}
TAIL_BYTES = 512 * 1024

WINDOW_S = 300  # status window: last 5 minutes
ANOMALY_ERRORS = 3  # >= this many errors in the window = active anomaly
CRITICAL_ERRORS = 5


@dataclass
class LogLine:
    id: str
    ts: datetime
    severity: str
    service: str
    message: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.ts.strftime("%H:%M:%S.") + f"{self.ts.microsecond // 1000:03d}",
            "ts": self.ts.isoformat(timespec="milliseconds"),
            "severity": self.severity,
            "service": self.service,
            "text": self.message,
        }


def _signature(message: str) -> str:
    """Collapse ids and numbers so repeated failures group together."""
    return re.sub(r"\d+", "N", re.sub(r"\b(ord|usr|req)_\w+", r"\1_*", message))


class LogAnalyzer:
    def __init__(self, log_path: str):
        self.path = Path(log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _tail(self, max_lines: int) -> list[LogLine]:
        if not self.path.exists():
            return []
        with open(self.path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - TAIL_BYTES)
            f.seek(start)
            data = f.read()
        offset = start
        lines: list[LogLine] = []
        chunks = data.split(b"\n")
        if start > 0:  # first fragment is probably a partial line
            offset += len(chunks[0]) + 1
            chunks = chunks[1:]
        for raw in chunks:
            line_offset = offset
            offset += len(raw) + 1
            m = LINE_RE.match(raw.decode("utf8", "replace").rstrip("\r"))
            if not m:
                continue
            ts, sev, svc, msg = m.groups()
            lines.append(LogLine(f"l{line_offset}", datetime.fromisoformat(ts), SEVERITY[sev], svc, msg))
        return lines[-max_lines:]

    def recent(self, n: int = 60) -> list[LogLine]:
        return self._tail(n)

    def by_ids(self, ids: list[str]) -> list[LogLine]:
        want = set(ids)
        return [l for l in self._tail(5000) if l.id in want]

    def stats(self, now: datetime | None = None) -> dict[str, dict]:
        """Per-service error/warn counts over the trailing WINDOW_S seconds."""
        now = now or datetime.now()
        out: dict[str, dict] = defaultdict(lambda: {"errors": 0, "warns": 0, "last_error_id": None, "last_ts": None})
        for l in self._tail(5000):
            s = out[l.service]
            s["last_ts"] = l.ts
            if (now - l.ts).total_seconds() > WINDOW_S:
                continue
            if l.severity == "error":
                s["errors"] += 1
                s["last_error_id"] = l.id
            elif l.severity == "warn":
                s["warns"] += 1
        for s in out.values():
            e, w = s["errors"], s["warns"]
            s["health"] = "critical" if e >= CRITICAL_ERRORS else "degraded" if e >= 1 or w >= 5 else "healthy"
            s["anomaly"] = e >= ANOMALY_ERRORS
        return dict(out)

    def anomalies(self, lookback_s: int = 1800, now: datetime | None = None) -> list[dict]:
        """Services with warn/error activity, most severe first, with the lines that show it."""
        now = now or datetime.now()
        recent = [l for l in self._tail(5000) if (now - l.ts).total_seconds() <= lookback_s]
        per: dict[str, list[LogLine]] = defaultdict(list)
        for l in recent:
            if l.severity in ("warn", "error"):
                per[l.service].append(l)
        result = []
        for svc, ls in per.items():
            errors = [l for l in ls if l.severity == "error"]
            sigs = Counter(_signature(l.message) for l in ls)
            result.append({
                "service": svc,
                "errors": len(errors),
                "warns": len(ls) - len(errors),
                "first_seen": ls[0].ts,
                "first_error": errors[0].ts if errors else None,
                "last_seen": ls[-1].ts,
                "top_signatures": sigs.most_common(3),
                "lines": ls,
            })
        result.sort(key=lambda a: (-a["errors"], -a["warns"]))
        return result
