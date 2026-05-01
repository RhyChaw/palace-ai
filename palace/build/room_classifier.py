from __future__ import annotations

import asyncio
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from anthropic import AsyncAnthropic


DEFAULT_MODEL = "claude-sonnet-4-6"


def _env_model() -> str | None:
    m = (os.environ.get("PALACE_MODEL") or "").strip()
    return m or None


PALETTE = [
    "#534AB7",
    "#22C55E",
    "#60A5FA",
    "#F59E0B",
    "#F472B6",
    "#2DD4BF",
    "#A78BFA",
    "#FB7185",
    "#94A3B8",
    "#10B981",
    "#F97316",
    "#38BDF8",
]


@dataclass
class ClassifiedRoom:
    id: str
    label: str
    color: str
    files: list[str]
    subtrees: dict[str, list[str]]
    summary: str | None = None
    cross_room_refs: list[dict[str, Any]] | None = None


_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    m = _JSON_OBJ_RE.search(text)
    if not m:
        raise ValueError("No JSON object found in model output")
    return json.loads(m.group(0))


def _is_test_file(file_id: str) -> bool:
    low = file_id.lower()
    return (
        "test" in low
        or low.startswith("tests/")
        or low.endswith("_test.py")
        or low.endswith(".spec.js")
        or low.endswith(".test.js")
    )


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "room"


ARCH_PATTERNS: dict[str, list[str]] = {
    "auth": ["auth", "jwt", "oauth", "session", "permission", "login", "credential"],
    "api": ["route", "router", "endpoint", "handler", "controller", "view", "api", "rest"],
    "data": ["model", "schema", "db", "database", "migrate", "orm", "query", "store", "repo"],
    "config": ["config", "setting", "env", "constant", "conf"],
    "utils": ["util", "helper", "common", "shared", "mixin", "lib", "tool"],
    "visualizer": ["visual", "render", "graph", "chart", "html", "template", "ui"],
    "build": ["cli", "build", "install", "setup", "main", "index", "init", "__init__"],
    "jobs": ["job", "task", "worker", "queue", "scheduler", "cron", "async"],
}


def _arch_room(paths: list[str], symbols: list[str]) -> str | None:
    """Return the best architectural room id for a community, or None."""
    scores: dict[str, int] = {}
    for room, keywords in ARCH_PATTERNS.items():
        path_score = 0
        sym_score = 0
        for p in paths:
            parts = [part.lower() for part in Path(p).parts]
            path_score += sum(any(kw in part for part in parts) for kw in keywords)
        sym_score = sum(any(kw in str(s).lower() for s in symbols) for kw in keywords)
        scores[room] = (path_score * 3) + sym_score

    best, count = max(scores.items(), key=lambda x: x[1])
    return best if count > 0 else None


def _summarise_community(files: list[dict[str, Any]]) -> str:
    """Build a deterministic summary from AST data alone."""
    all_symbols: list[str] = []
    for f in files:
        all_symbols += list(f.get("symbols", []) or [])

    counts = Counter(all_symbols)
    top = [s for s, _ in counts.most_common(6) if not str(s).startswith("_")][:5]

    langs = list({f.get("language", "") for f in files if f.get("language")})
    lang_str = langs[0] if len(langs) == 1 else ", ".join(sorted(langs))
    sym_str = f"exports: {', '.join(top)}" if top else "no public symbols detected"
    return f"{len(files)} file{'s' if len(files) != 1 else ''} · {lang_str} · {sym_str}"


def _palette_color(idx: int) -> str:
    return PALETTE[idx % len(PALETTE)]


def _subtrees_by_connectivity(files: list[str], import_edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    g = nx.Graph()
    g.add_nodes_from(files)
    for a, b in import_edges:
        if a in g and b in g:
            g.add_edge(a, b)
    comps = list(nx.connected_components(g))
    comps.sort(key=lambda c: (-len(c), sorted(c)[0] if c else ""))
    out: dict[str, list[str]] = {}
    for i, comp in enumerate(comps, start=1):
        out[f"ST_{i}"] = sorted(comp)
    return out


async def classify_rooms_llm(
    *,
    model: str | None,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    client = AsyncAnthropic(api_key=api_key)
    m = model or _env_model() or DEFAULT_MODEL

    # keep prompt compact: only id + room suggestions + imports graph
    files = []
    for n in nodes:
        files.append(
            {
                "id": n.get("id"),
                "language": n.get("language"),
                "room_suggestion": n.get("room_suggestion") or n.get("room_id"),
                "summary": n.get("summary"),
            }
        )
    imports = [e for e in edges if e.get("type") == "imports"]

    prompt = f"""You are assigning files in a codebase into architectural Rooms for a "memory palace".

Input:
- files: list of files with (id, language, room_suggestion, summary)
- imports: list of import edges (from -> to)

Return JSON only with this shape:
{{
  "rooms": [
    {{
      "id": "auth",
      "label": "Authentication layer",
      "color": "#534AB7",
      "files": ["path/a.js", "path/b.js"],
      "subtrees": {{"ST_MIDDLEWARE": ["..."]}},
      "summary": "1 sentence room summary"
    }}
  ],
  "file_to_room": {{"path/a.js": "auth"}}
}}

Constraints:
- Every file must appear in exactly one room.
- Use 6-14 rooms for medium repos; fewer for small repos.
- Colors must be distinct hex strings.
- Subtrees should be tight clusters (based on imports) within a room.

files:
{json.dumps(files)}

imports:
{json.dumps([{"from": e.get("from"), "to": e.get("to")} for e in imports])}
"""
    msg = await client.messages.create(
        model=m,
        max_tokens=1800,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    out = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            out += block.text
        else:
            out += str(block)
    return _parse_json_object(out)


def classify_rooms(
    *,
    repo_path: Path,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    model: str | None,
    use_llm: bool,
) -> tuple[dict[str, str], list[ClassifiedRoom]]:
    file_ids = [n["id"] for n in nodes if n.get("id")]

    if use_llm:
        try:
            obj = asyncio.run(classify_rooms_llm(model=model, nodes=nodes, edges=edges))
            file_to_room = {k: v for k, v in (obj.get("file_to_room") or {}).items() if k in set(file_ids)}
            rooms_in = obj.get("rooms") or []
            rooms: list[ClassifiedRoom] = []
            for r in rooms_in:
                if not isinstance(r, dict) or not r.get("id"):
                    continue
                rid = str(r["id"])
                files = [f for f in (r.get("files") or []) if f in set(file_ids)]
                rooms.append(
                    ClassifiedRoom(
                        id=rid,
                        label=str(r.get("label") or rid),
                        color=str(r.get("color") or _palette_color(len(rooms))),
                        files=files,
                        subtrees={k: [f for f in v if f in set(file_ids)] for k, v in (r.get("subtrees") or {}).items()},
                        summary=str(r.get("summary") or "").strip() or None,
                        cross_room_refs=r.get("cross_room_refs"),
                    )
                )
            if file_to_room and rooms:
                # backfill missing file assignments
                assigned = set(file_to_room.keys())
                for fid in file_ids:
                    if fid not in assigned:
                        file_to_room[fid] = rooms[-1].id
                return file_to_room, rooms
        except Exception as e:
            print(f"Room classifier LLM skipped: {e}")

    # Heuristic fallback: partition import/call graph into communities (keeps rooms small)
    node_by_id: dict[str, dict[str, Any]] = {n["id"]: n for n in nodes if n.get("id")}
    all_ids = sorted(set(file_ids))
    test_files = sorted([f for f in all_ids if _is_test_file(f)])
    non_tests = [f for f in all_ids if f not in set(test_files)]

    g = nx.Graph()
    g.add_nodes_from(non_tests)
    import_edges = [(e.get("from"), e.get("to")) for e in edges if e.get("type") in {"imports", "calls"}]
    for a, b in import_edges:
        if a in g and b in g:
            g.add_edge(a, b)

    # If graph is too sparse, just use connected components
    communities = []
    if g.number_of_edges() == 0:
        communities = [set(c) for c in nx.connected_components(g)]
    else:
        try:
            comms = nx.algorithms.community.greedy_modularity_communities(g)
            communities = [set(c) for c in comms]
        except Exception:
            communities = [set(c) for c in nx.connected_components(g)]

    communities.sort(key=lambda c: (-len(c), sorted(c)[0] if c else ""))

    # Cap room count by merging tiny communities
    MAX_ROOMS = 12
    while len(communities) > MAX_ROOMS:
        small = communities.pop()  # smallest
        communities[-1].update(small)

    # Step E — name communities architecturally
    rooms_acc: dict[str, dict[str, Any]] = {}
    unmatched: list[tuple[list[str], list[dict[str, Any]]]] = []

    for comm in communities:
        paths = sorted(comm)
        file_nodes = [node_by_id[fid] for fid in paths if fid in node_by_id]
        symbols = [s for f in file_nodes for s in (f.get("symbols", []) or [])]

        rid = _arch_room(paths, symbols)
        if rid is None:
            unmatched.append((paths, file_nodes))
            continue

        rooms_acc.setdefault(rid, {"files": [], "file_nodes": []})
        rooms_acc[rid]["files"] += paths
        rooms_acc[rid]["file_nodes"] += file_nodes

    # Step F — merge unmatched communities into utils (not numbered suffixes)
    for paths, file_nodes in unmatched:
        rooms_acc.setdefault("utils", {"files": [], "file_nodes": []})
        rooms_acc["utils"]["files"] += paths
        rooms_acc["utils"]["file_nodes"] += file_nodes

    # Step G — build final room objects with summaries
    LABELS = {
        "auth": "Authentication",
        "api": "API Layer",
        "data": "Data Layer",
        "config": "Configuration",
        "utils": "Utilities",
        "visualizer": "Visualizer",
        "build": "Build & CLI",
        "jobs": "Background Jobs",
        "tests": "Tests",
    }
    COLORS = {
        "auth": "#7F77DD",
        "api": "#1D9E75",
        "data": "#378ADD",
        "config": "#EF9F27",
        "utils": "#888",
        "visualizer": "#D4537E",
        "build": "#534AB7",
        "jobs": "#D85A30",
        "tests": "#999",
    }

    final_rooms: list[ClassifiedRoom] = []
    file_to_room: dict[str, str] = {}

    for rid, data in rooms_acc.items():
        files = sorted(set(data["files"]))
        for fid in files:
            file_to_room[fid] = rid

        subtrees = _subtrees_by_connectivity(files, [(a, b) for a, b in import_edges if a and b])
        summary = _summarise_community(list(data["file_nodes"]))
        final_rooms.append(
            ClassifiedRoom(
                id=rid,
                label=LABELS.get(rid, rid.replace("-", " ").title()),
                color=COLORS.get(rid, "#888"),
                files=files,
                subtrees=subtrees,
                summary=summary,
                cross_room_refs=[],
            )
        )

    # always add tests room if it exists
    if test_files:
        rid = "tests"
        for fid in test_files:
            file_to_room[fid] = rid
        test_nodes = [node_by_id[fid] for fid in test_files if fid in node_by_id]
        final_rooms.append(
            ClassifiedRoom(
                id=rid,
                label="Tests",
                color=COLORS["tests"],
                files=test_files,
                subtrees=_subtrees_by_connectivity(test_files, [(a, b) for a, b in import_edges if a and b]),
                summary=_summarise_community(test_nodes),
                cross_room_refs=[],
            )
        )

    # Backfill any stragglers (should be none, but keep stable behavior)
    for fid in all_ids:
        file_to_room.setdefault(fid, "utils")

    final_rooms.sort(key=lambda r: (r.id != "build", r.id != "auth", r.id))
    return file_to_room, final_rooms

