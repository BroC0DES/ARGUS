"""Step 1 of the eval harness: sanitize a copy of mock-codebase2/packages and
record the hash of the untouched original.

- Copies mock-codebase2/packages -> eval/_sanitized/packages, excluding
  node_modules, dist, and any cache dirs.
- Strips every comment paragraph (a contiguous run of `//`-only lines) that
  mentions "BUG #", "TO BREAK", "TO FIX", or "planted" (case-insensitive) --
  whole paragraphs, not just the matching line, so no dangling half-sentence
  that still names the cause survives either.
- Verifies the sanitized copy is clean (case-insensitive search for those
  four markers must come back zero) and prints ONLY that verification
  result, per instructions.
- Writes eval/baseline_hash.json: the sha256 of the ORIGINAL (untouched,
  still-commented) mock-codebase2/packages, via backend/eval/code_hash.py.

The original mock-codebase2/packages is only ever READ here, never written.

Run: python eval/sanitize.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "mock-codebase2" / "packages"
OUT = HERE / "_sanitized" / "packages"
BASELINE_HASH_PATH = HERE / "baseline_hash.json"

sys.path.insert(0, str(ROOT / "backend" / "eval"))
from code_hash import compute_code_hash  # noqa: E402

_SKIP_DIRS = {"node_modules", "dist", "build", ".turbo", "__pycache__", ".cache"}
_MARKERS = ("bug #", "to break", "to fix", "planted")


def _should_skip_dir(name: str) -> bool:
    return name in _SKIP_DIRS or name.startswith(".")


def _copy_tree(src: Path, dst: Path) -> list[Path]:
    """Copy src -> dst, skipping _SKIP_DIRS. Returns every copied file path."""
    if dst.exists():
        shutil.rmtree(dst)
    copied: list[Path] = []
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        if any(_should_skip_dir(part) for part in rel.parts):
            continue
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            copied.append(target)
    return copied


def _line_matches(line: str) -> bool:
    low = line.lower()
    return any(m in low for m in _MARKERS)


def _strip_marked_paragraphs(text: str) -> str:
    """Remove every contiguous run of `//`-only comment lines that contains
    at least one marker line, keeping every other line untouched. A second,
    defensive pass then deletes any single leftover line that still matches
    (covers a marker mixed into a non-`//`-only line, none observed in this
    codebase today, but the grep check downstream must come back zero
    regardless of shape)."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip().startswith("//"):
            j = i
            block: list[str] = []
            while j < n and lines[j].strip().startswith("//"):
                block.append(lines[j])
                j += 1
            if any(_line_matches(b) for b in block):
                i = j
                continue
            out.extend(block)
            i = j
            continue
        out.append(line)
        i += 1
    # Defensive second pass: drop any single remaining matching line outright.
    out = [l for l in out if not _line_matches(l)]
    return "\n".join(out)


def sanitize() -> Path:
    if not SRC.is_dir():
        raise SystemExit(f"Source not found: {SRC}")
    copied = _copy_tree(SRC, OUT)
    for p in copied:
        if p.suffix in (".ts", ".tsx"):
            original = p.read_text(encoding="utf-8")
            cleaned = _strip_marked_paragraphs(original)
            if cleaned != original:
                p.write_text(cleaned, encoding="utf-8")
    return OUT


def verify_clean(root: Path) -> int:
    """Case-insensitive search across every file under root for the four
    markers. Returns the total number of matching lines (must be 0)."""
    pattern = re.compile("|".join(re.escape(m) for m in _MARKERS), re.IGNORECASE)
    hits = 0
    for p in root.rglob("*"):
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            hits += sum(1 for line in text.split("\n") if pattern.search(line))
    return hits


def write_baseline_hash() -> None:
    h = compute_code_hash(SRC)
    BASELINE_HASH_PATH.write_text(json.dumps({
        "hash": h,
        "algorithm": "sha256",
        "computed_from": str(SRC.relative_to(ROOT)).replace("\\", "/"),
        "note": "Hash of the ORIGINAL commented mock-codebase2/packages (never modified).",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_baseline_hash()
    out_dir = sanitize()
    n = verify_clean(out_dir)
    print(f"Sanitized-copy marker check ({out_dir}): {n} matches for 'BUG #' / 'TO BREAK' / 'TO FIX' / 'planted' (must be 0)")
    if n != 0:
        raise SystemExit(1)
