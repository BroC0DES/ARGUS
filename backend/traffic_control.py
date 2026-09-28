"""Manages mock-codebase2's traffic simulator (traffic_sim2.mjs) as a child
process, so the frontend's Traffic ON/OFF button can start and stop real
checkout-request traffic without anyone touching a terminal.

main.py starts it once automatically at backend startup (so "start the
backend" is also "traffic is on from the start", per the Launch ARGUS.bat
flow) and stops it at backend shutdown. The /traffic endpoint lets it be
stopped and restarted at any point after that, from the UI.

Never touches dev.mjs or the services themselves -- only the traffic
generator, which is the one piece meant to be toggled on demand.
"""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path

MOCK_CODEBASE_DIR = Path(__file__).parent.parent / "mock-codebase2"

_lock = threading.Lock()
_proc: subprocess.Popen | None = None
_last_error: str | None = None


def is_running() -> bool:
    with _lock:
        return _proc is not None and _proc.poll() is None


def last_error() -> str | None:
    return _last_error


def start() -> bool:
    """Starts traffic_sim2.mjs if it isn't already running. Returns the
    resulting running state. Never raises -- a missing `node` on PATH (or
    any other launch failure) is recorded in last_error() and reported to
    the caller as running=False, instead of taking the rest of the backend
    down with it."""
    global _proc, _last_error
    with _lock:
        if _proc is not None and _proc.poll() is None:
            return True
        try:
            _proc = subprocess.Popen(
                ["node", "traffic_sim2.mjs"],
                cwd=str(MOCK_CODEBASE_DIR),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            _last_error = None
            return True
        except OSError as e:
            _proc = None
            _last_error = str(e)
            return False


def stop() -> bool:
    """Stops traffic_sim2.mjs if it's running. Always returns True (stopping
    an already-stopped simulator is a no-op success, not an error)."""
    global _proc
    with _lock:
        if _proc is None or _proc.poll() is not None:
            _proc = None
            return True
        _proc.terminate()
        try:
            _proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _proc.kill()
            _proc.wait(timeout=5)
        _proc = None
        return True
