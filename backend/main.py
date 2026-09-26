"""ARGUS backend. Run:  uvicorn main:app --reload --port 8000"""
from __future__ import annotations

import os
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

REPO_PATH = os.environ.get("REPO_PATH") or str((HERE.parent / "sample_repo"))
LOG_PATH = os.environ.get("LOG_PATH") or str(HERE / "logs" / "app.log")

indexer = CodeIndexer(REPO_PATH)
logs = LogAnalyzer(LOG_PATH)

app = FastAPI(title="ARGUS")
app.add_middleware(
    CORSMiddleware,
    # 5173 is the documented dev port; 5174 is where Vite lands if 5173 is taken.
    allow_origins=[f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 5174)],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryBody(BaseModel):
    question: str = Field(default="", max_length=2000)


@app.get("/health")
def health():
    return {"ok": True, "repo": REPO_PATH, "log": LOG_PATH, "has_api_key": bool(os.environ.get("ANTHROPIC_API_KEY"))}


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
