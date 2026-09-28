"""Code Indexer: tree-sitter parse of REPO_PATH -> function chunks, service
dependency graph, and TF-IDF retrieval over the chunks.

Services are the directories under <repo>/services/ (or, if absent, the top-level
directories that contain source files). An edge A -> B means "A imports B", i.e.
A depends on / calls B. Python and TypeScript are both supported; a service id is
always normalized to underscores (matching Python's own module-name convention)
regardless of which language it's written in, so display_name() and log-line
service names (hyphenated) map onto it the same way either way.
"""
from __future__ import annotations

import math
import os
import re
import threading
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_python as tspython
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser

_PARSER_PY = Parser(Language(tspython.language()))
_PARSER_TS = Parser(Language(tsts.language_typescript()))
_SOURCE_EXTS = (".py", ".ts", ".tsx")
_SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "tests", "test", "dist", "build"}
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def display_name(service_id: str) -> str:
    return service_id.replace("_", "-")


def tokenize(text: str) -> list[str]:
    """Split identifiers on snake_case and camelCase so 'charge_card' matches 'charge'."""
    out: list[str] = []
    for word in _TOKEN_RE.findall(text):
        parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", word).lower().split()
        out.extend(parts)
    return out


@dataclass
class Chunk:
    service: str
    file: str  # repo-relative, forward slashes
    name: str
    start_line: int  # 1-based
    end_line: int
    lines: list[str]
    tokens: Counter = field(default_factory=Counter, repr=False)


@dataclass
class Index:
    services: list[str]
    edges: list[tuple[str, str]]
    chunks: list[Chunk]
    idf: dict[str, float]
    signature: tuple


def _discover_services(repo: Path) -> dict[str, Path]:
    """Service id is always the underscore form of the directory name (e.g. a TS
    package folder 'db-pool' becomes id 'db_pool'), so display_name() and the
    hyphen->underscore lookup in query_pipeline._bundle() work the same regardless
    of which language a service happens to be written in."""
    root = repo / "services" if (repo / "services").is_dir() else repo
    found: dict[str, Path] = {}
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name not in _SKIP_DIRS and not d.name.startswith("."):
            if any(p.suffix in _SOURCE_EXTS for p in d.rglob("*") if p.is_file()):
                found[d.name.replace("-", "_")] = d
    return found


def _source_files(d: Path):
    for p in sorted(d.rglob("*")):
        if p.suffix not in _SOURCE_EXTS or any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.suffix == ".py" and p.name == "__init__.py":
            continue
        yield p


def _imports_py(tree_root, src: bytes) -> list[str]:
    mods: list[str] = []
    stack = [tree_root]
    while stack:
        n = stack.pop()
        if n.type == "import_from_statement":
            m = n.child_by_field_name("module_name")
            if m is not None:
                mods.append(src[m.start_byte:m.end_byte].decode("utf8", "replace"))
        elif n.type == "import_statement":
            for c in n.children:
                if c.type in ("dotted_name", "aliased_import"):
                    mods.append(src[c.start_byte:c.end_byte].decode("utf8", "replace").split(" as ")[0])
        else:
            stack.extend(n.children)
    return mods


def _imports_ts(tree_root, src: bytes) -> list[str]:
    """TS imports are relative paths ('../../db-pool/src/pool'), not dotted module
    names. Convert '/' -> '.' and '-' -> '_' so the result can be split on '.' and
    matched against services the exact same way _build() already does for Python."""
    mods: list[str] = []
    stack = [tree_root]
    while stack:
        n = stack.pop()
        if n.type in ("import_statement", "export_statement"):
            src_field = n.child_by_field_name("source")
            if src_field is not None:
                frag = next((c for c in src_field.children if c.type == "string_fragment"), None)
                if frag is not None:
                    path = src[frag.start_byte:frag.end_byte].decode("utf8", "replace")
                    mods.append(path.replace("/", ".").replace("-", "_"))
        stack.extend(n.children)
    return mods


def _definitions_py(node, src: bytes, prefix: str = ""):
    """Yield (qualified_name, node) for functions, and methods qualified by class."""
    for c in node.children:
        target = c
        if c.type == "decorated_definition":
            target = c.child_by_field_name("definition") or c
        if target.type == "function_definition":
            nm = target.child_by_field_name("name")
            yield prefix + src[nm.start_byte:nm.end_byte].decode(), c
        elif target.type == "class_definition":
            nm = target.child_by_field_name("name")
            cname = src[nm.start_byte:nm.end_byte].decode()
            body = target.child_by_field_name("body")
            yield cname, c
            if body is not None:
                yield from _definitions_py(body, src, prefix=cname + ".")


def _definitions_ts(node, src: bytes, prefix: str = ""):
    """Same shape as _definitions_py: yield (qualified_name, node) for top-level
    functions and class methods. `export`/`export default` wraps the declaration
    in an export_statement -- unwrapped to find the real node, but the outer
    export_statement is what gets chunked, so 'export async function foo' stays
    intact in the displayed code."""
    for c in node.children:
        target = c
        if c.type == "export_statement":
            target = next((gc for gc in c.children if gc.type in ("function_declaration", "class_declaration")), c)
        if target.type in ("function_declaration", "function_signature"):
            nm = target.child_by_field_name("name")
            if nm is not None:
                yield prefix + src[nm.start_byte:nm.end_byte].decode(), c
        elif target.type == "class_declaration":
            nm = target.child_by_field_name("name")
            if nm is None:
                continue
            cname = src[nm.start_byte:nm.end_byte].decode()
            yield cname, c
            body = target.child_by_field_name("body")
            if body is not None:
                for gc in body.children:
                    if gc.type == "method_definition":
                        mname = gc.child_by_field_name("name")
                        if mname is not None:
                            yield cname + "." + src[mname.start_byte:mname.end_byte].decode(), gc


_LANG = {
    ".py": (_PARSER_PY, _imports_py, _definitions_py),
    ".ts": (_PARSER_TS, _imports_ts, _definitions_ts),
    ".tsx": (_PARSER_TS, _imports_ts, _definitions_ts),
}


def _build(repo: Path) -> Index:
    services = _discover_services(repo)
    chunks: list[Chunk] = []
    edges: set[tuple[str, str]] = set()
    for sid, sdir in services.items():
        for path in _source_files(sdir):
            parser, imports_fn, definitions_fn = _LANG[path.suffix]
            src = path.read_bytes()
            tree = parser.parse(src)
            rel = path.relative_to(repo).as_posix()
            text_lines = src.decode("utf8", "replace").splitlines()
            for mod in imports_fn(tree.root_node, src):
                for seg in mod.split("."):
                    if seg in services and seg != sid:
                        edges.add((sid, seg))
                        break
            for qname, node in definitions_fn(tree.root_node, src):
                s, e = node.start_point[0], node.end_point[0]
                lines = text_lines[s:e + 1]
                ch = Chunk(sid, rel, qname, s + 1, e + 1, lines)
                # Name and path weighted x3 so a query naming charge() finds charge().
                ch.tokens = Counter(tokenize("\n".join(lines)))
                for t in tokenize(qname + " " + rel):
                    ch.tokens[t] += 3
                chunks.append(ch)
    df: Counter = Counter()
    for ch in chunks:
        df.update(ch.tokens.keys())
    n = max(len(chunks), 1)
    idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
    return Index(list(services), sorted(edges), chunks, idf, _signature(repo))


def _signature(repo: Path) -> tuple:
    sig = []
    for ext in _SOURCE_EXTS:
        for p in repo.rglob(f"*{ext}"):
            if not any(part in _SKIP_DIRS for part in p.parts):
                st = p.stat()
                sig.append((str(p), st.st_mtime_ns, st.st_size))
    return tuple(sorted(sig))


class CodeIndexer:
    def __init__(self, repo_path: str):
        self.repo = Path(repo_path).resolve()
        if not self.repo.is_dir():
            raise RuntimeError(f"REPO_PATH does not exist or is not a directory: {self.repo}")
        self._lock = threading.Lock()
        self._index: Index | None = None

    def index(self) -> Index:
        """Return the index, re-parsing only when a source file changed on disk."""
        with self._lock:
            sig = _signature(self.repo)
            if self._index is None or self._index.signature != sig:
                self._index = _build(self.repo)
            return self._index

    # ---- dependency graph -------------------------------------------------
    def graph(self) -> tuple[list[str], list[tuple[str, str]]]:
        ix = self.index()
        return ix.services, ix.edges

    def layout(self) -> dict[str, tuple[int, int]]:
        """Layered top-to-bottom layout: row = longest path from a root. Fits any panel width."""
        services, edges = self.graph()
        incoming = defaultdict(list)
        for a, b in edges:
            incoming[b].append(a)
        depth: dict[str, int] = {}

        def d(n: str, seen=()) -> int:
            if n in depth:
                return depth[n]
            if n in seen:  # cycle guard
                return 0
            depth[n] = 0 if not incoming[n] else 1 + max(d(p, seen + (n,)) for p in incoming[n])
            return depth[n]

        cols: dict[int, list[str]] = defaultdict(list)
        for s in services:
            cols[d(s)].append(s)
        pos = {}
        for col, members in cols.items():
            for row, s in enumerate(sorted(members)):
                pos[s] = (12 + row * 200, 12 + col * 76)
        return pos

    def callers(self, service: str) -> set[str]:
        """Every service that transitively depends on `service`."""
        _, edges = self.graph()
        rev = defaultdict(list)
        for a, b in edges:
            rev[b].append(a)
        seen, q = set(), deque([service])
        while q:
            for p in rev[q.popleft()]:
                if p not in seen:
                    seen.add(p)
                    q.append(p)
        return seen

    def callees(self, service: str) -> set[str]:
        _, edges = self.graph()
        return {b for a, b in edges if a == service}

    def path_to(self, target: str) -> list[str]:
        """Shortest dependency path from an entry service (no callers) to `target`."""
        services, edges = self.graph()
        fwd = defaultdict(list)
        has_in = set()
        for a, b in edges:
            fwd[a].append(b)
            has_in.add(b)
        best: list[str] | None = None
        for entry in [s for s in services if s not in has_in]:
            prev = {entry: None}
            q = deque([entry])
            while q:
                n = q.popleft()
                if n == target:
                    path = []
                    while n is not None:
                        path.append(n)
                        n = prev[n]
                    path.reverse()
                    if best is None or len(path) < len(best):
                        best = path
                    break
                for m in fwd[n]:
                    if m not in prev:
                        prev[m] = n
                        q.append(m)
        return best or [target]

    # ---- retrieval --------------------------------------------------------
    def search(self, query: str, k: int = 6, boost: dict[str, float] | None = None) -> list[Chunk]:
        return [ch for _, _, ch in self.search_scored(query, k=k, boost=boost)]

    def search_scored(self, query: str, k: int = 6, boost: dict[str, float] | None = None) -> list[tuple[float, float, Chunk]]:
        """Ranks by the boosted score (boost is a retrieval-ranking heuristic --
        which chunk counts as the top hit is still entirely its call, unchanged).
        Each result also carries the raw, unboosted cosine similarity alongside
        it, for callers that need retrieval confidence rather than just ranking:
        boost is derived from the same anomaly/graph signal confidence scoring
        already counts elsewhere (dominance), so feeding the BOOSTED score into
        confidence too would double-count that signal. Returns
        (boosted_score, raw_cosine, chunk) tuples, sorted by boosted_score."""
        ix = self.index()
        q = Counter(tokenize(query))
        if not q or not ix.chunks:
            return []
        qvec = {t: (1 + math.log(c)) * ix.idf.get(t, 0.0) for t, c in q.items()}
        qnorm = math.sqrt(sum(v * v for v in qvec.values())) or 1.0
        scored = []
        for ch in ix.chunks:
            dot = sum(qvec[t] * (1 + math.log(ch.tokens[t])) * ix.idf[t] for t in qvec if ch.tokens.get(t))
            if not dot:
                continue
            cnorm = math.sqrt(sum(((1 + math.log(c)) * ix.idf[t]) ** 2 for t, c in ch.tokens.items())) or 1.0
            raw = dot / (qnorm * cnorm)
            boosted = raw * (boost or {}).get(ch.service, 1.0)
            scored.append((boosted, raw, ch))
        scored.sort(key=lambda x: -x[0])
        return scored[:k]
