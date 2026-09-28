"""ARGUS backend. Run:  uvicorn main:app --reload --port 8000"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

from code_indexer import CodeIndexer, display_name  # noqa: E402  (after load_dotenv)
from log_analyzer import LogAnalyzer, WINDOW_S  # noqa: E402
from query_pipeline import QueryError, run_query  # noqa: E402
import scenario_sim  # noqa: E402

REPO_PATH = os.environ.get("REPO_PATH") or str((HERE.parent / "sample_repo"))
LOG_PATH = os.environ.get("LOG_PATH") or str(HERE / "logs" / "app.log")
# Canned demo scenarios (payment-timeout, db-exhaustion, cascading-failure) now replay
# into their OWN file instead of overwriting LOG_PATH -- see set_scenario() below. This
# means live traffic (traffic_sim2.mjs / real mock-codebase2 services) can keep writing
# to LOG_PATH the whole time without corrupting whichever scenario fixture is on screen,
# and switching back to "Live traffic" needs no cleanup.
SCENARIO_LOG_PATH = os.environ.get("SCENARIO_LOG_PATH") or str(Path(LOG_PATH).parent / "scenario_active.log")

indexer = CodeIndexer(REPO_PATH)
logs = LogAnalyzer(LOG_PATH)
active_scenario = "none"  # "none" = whatever's actually being written to LOG_PATH (traffic_sim.py or live traffic)

app = FastAPI(title="ARGUS")
app.add_middleware(
    CORSMiddleware,
    # 5173 is the documented dev port; 5174 is where Vite lands if 5173 is taken.
    allow_origins=[f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 5174)],
    allow_methods=["*"],
    allow_headers=["*"],
)

warmup_state = {"done": False, "error": None}


def _warm_ollama() -> None:
    """Fire one throwaway completion at Ollama so the model is already loaded into
    memory before a real user query arrives. On this kind of setup (local CPU-only
    Ollama, no GPU), the FIRST call after the Ollama server starts (or after the
    model has been idle) pays a one-off cost to load the weights into RAM -- 100s+
    is normal for a few-billion-parameter model -- on top of normal generation
    time. Without this, that cost lands on whichever demo query happens to be
    first. Runs in a background thread so it never blocks startup; best-effort,
    so any failure here (Ollama not running yet, wrong model name, etc.) is left
    for the first real /query call to report properly instead of crashing here."""
    try:
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        model = os.environ.get("OLLAMA_MODEL", "mistral")
        body = json.dumps({"model": model, "stream": False, "messages": [{"role": "user", "content": "ping"}]}).encode()
        req = urllib.request.Request(f"{url}/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=280):
            pass
        warmup_state["done"] = True
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        warmup_state["error"] = str(e)


@app.on_event("startup")
def warm_model_on_startup() -> None:
    threading.Thread(target=_warm_ollama, daemon=True).start()


class QueryBody(BaseModel):
    question: str = Field(default="", max_length=2000)


class ScenarioBody(BaseModel):
    name: str = Field(max_length=64)


@app.get("/health")
def health():
    return {
        "ok": True, "repo": REPO_PATH, "log": str(logs.path), "llm": "ollama",
        "ollama_model": os.environ.get("OLLAMA_MODEL", "mistral"),
        "active_scenario": active_scenario,
        "available_scenarios": sorted(scenario_sim.SCENARIOS),
        "model_warm": warmup_state["done"], "warmup_error": warmup_state["error"],
    }


@app.post("/scenario")
def set_scenario(body: ScenarioBody):
    """Switch which file the Log Analyzer reads: a scenario fixture, replayed with
    timestamps shifted to "now" (see scenario_sim.py), or LOG_PATH (live traffic).
    Canned scenarios replay into SCENARIO_LOG_PATH -- a dedicated file, never
    LOG_PATH itself -- so live traffic (traffic_sim2.mjs / real mock-codebase2
    services) can keep writing the whole time without corrupting the fixture
    that's on screen, and flipping back to "Live traffic" needs no cleanup."""
    global active_scenario
    if body.name == "none":
        active_scenario = "none"
        logs.path = Path(LOG_PATH)
        return {"active_scenario": active_scenario, "lines_written": 0, "backed_up_to": None}
    try:
        n, backup_path = scenario_sim.replay(body.name, SCENARIO_LOG_PATH)
    except scenario_sim.ScenarioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    active_scenario = body.name
    logs.path = Path(SCENARIO_LOG_PATH)
    return {"active_scenario": active_scenario, "lines_written": n, "backed_up_to": backup_path}


@app.get("/graph")
def graph():
    """Live dependency graph. Node status is computed from the current log data."""
    services, edges = indexer.graph()
    pos = indexer.layout()
    stats = logs.stats()
    nodes = []
    for sid in services:
        name = display_name(sid)
        s = stats.get(name, {"errors": 0, "warns": 0, "health": "healthy", "anomaly": False})
        x, y = pos[sid]
        nodes.append({
            "id": name, "name": name, "x": x, "y": y,
            "rate": f"{s['errors']}/{WINDOW_S // 60}m",
            "health": s["health"], "anomaly": s["anomaly"],
            "errors": s["errors"], "warnings": s["warns"],
        })
    return {"nodes": nodes, "edges": [{"from": display_name(a), "to": display_name(b)} for a, b in edges]}


@app.get("/logs")
def get_logs(n: int = 60):
    """Most recent N lines, read from disk on every call."""
    n = max(1, min(n, 500))
    return {"lines": [l.to_dict() for l in logs.recent(n)]}


@app.post("/query")
def query(body: QueryBody):
    question = body.question.strip() or "What is happening in the system right now?"
    try:
        return run_query(question, logs, indexer)
    except QueryError as e:
        raise HTTPException(status_code=e.status, detail=e.detail)
