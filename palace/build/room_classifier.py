from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from anthropic import AsyncAnthropic


DEFAULT_MODEL = "claude-sonnet-4-20250514"


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


def _room_name_from_paths(paths: list[str]) -> tuple[str, str]:
    # Pick a stable prefix-based identifier for a community
    if not paths:
        return "other", "Other"
    parts = [p.split("/") for p in paths if p]
    # choose most common first segment, then second
    first = {}
    second = {}
    for segs in parts:
        if segs:
            first[segs[0]] = first.get(segs[0], 0) + 1
        if len(segs) > 1:
            second[segs[1]] = second.get(segs[1], 0) + 1
    top1 = max(first.items(), key=lambda kv: kv[1])[0] if first else "other"
    top2 = max(second.items(), key=lambda kv: kv[1])[0] if second else ""
    base = top1 if not top2 else f"{top1}-{top2}"
    rid = _slug(base)
    label = base.replace("-", " ").title()
    return rid, label


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
    m = model or DEFAULT_MODEL

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
    all_files = sorted(set(file_ids))
    tests = [f for f in all_files if _is_test_file(f)]
    non_tests = [f for f in all_files if f not in set(tests)]

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

    file_to_room: dict[str, str] = {}
    rooms: list[ClassifiedRoom] = []
    used_ids: set[str] = set()
    for idx, comm in enumerate(communities):
        paths = sorted(comm)
        rid, label = _room_name_from_paths(paths)
        if rid in used_ids:
            rid = f"{rid}-{idx+1}"
        used_ids.add(rid)
        for f in paths:
            file_to_room[f] = rid
        subtrees = _subtrees_by_connectivity(paths, [(a, b) for a, b in import_edges if a and b])
        rooms.append(
            ClassifiedRoom(
                id=rid,
                label=label,
                color=_palette_color(idx),
                files=paths,
                subtrees=subtrees,
                summary=None,
                cross_room_refs=[],
            )
        )

    if tests:
        rid = "tests"
        file_to_room.update({f: rid for f in tests})
        rooms.append(
            ClassifiedRoom(
                id=rid,
                label="Tests",
                color=_palette_color(len(rooms)),
                files=sorted(tests),
                subtrees=_subtrees_by_connectivity(sorted(tests), [(a, b) for a, b in import_edges if a and b]),
                summary=None,
                cross_room_refs=[],
            )
        )

    # Backfill any stragglers
    for fid in all_files:
        file_to_room.setdefault(fid, "other")
    if "other" in file_to_room.values() and all_files:
        rooms.append(
            ClassifiedRoom(
                id="other",
                label="Other",
                color=_palette_color(len(rooms)),
                files=sorted([f for f, r in file_to_room.items() if r == "other"]),
                subtrees={},
                summary=None,
                cross_room_refs=[],
            )
        )

    return file_to_room, rooms

