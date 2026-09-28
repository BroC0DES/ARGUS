"""Hash baseline for the eval harness.

compute_code_hash() hashes every *.ts file under a repo root (sorted by
repo-relative path, forward slashes) so the harness can prove which exact
version of the code a run's numbers came from -- the ORIGINAL commented
mock-codebase2/packages, or the sanitized copy. node_modules and dist are
excluded (build output / dependencies, not source).

Never imports code_indexer or query_pipeline -- this stays a standalone,
dependency-free utility so it can be run before anything else.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

_SKIP_DIRS = {"node_modules", "dist"}


def _ts_files(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*.ts"):
        if any(part in _SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        out.append(p)
    return out


def compute_code_hash(root: str | Path) -> str:
    """sha256 over sorted (relative_path, contents) pairs of every *.ts file
    under `root`, excluding node_modules and dist. Deterministic regardless
    of filesystem iteration order or OS path separators."""
    root = Path(root).resolve()
    files = sorted(_ts_files(root), key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for p in files:
        rel = p.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(compute_code_hash(target))
