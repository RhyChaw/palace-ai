from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


TYPE_MULTIPLIER: dict[str, float] = {
    "imports": 1.0,
    "calls": 1.0,
    "implements": 1.0,
    "co-changes": 0.75,
    "shares-schema": 0.75,
    "configures": 0.75,
    "error-path": 0.5,
    "spawns": 0.5,
    "test-of": 0.5,
    "inferred": 0.5,
}


def _decay(hop: int) -> float:
    return [1.0, 0.55, 0.25][hop]


def _tokenize(q: str) -> list[str]:
    return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in q).split() if t]


def _score_node(query: str, node: dict) -> float:
    """
    Seed score: lightweight lexical scoring.
    - label exact/contains
    - summary contains
    - symbol name contains
    """
    toks = _tokenize(query)
    if not toks:
        return 0.0
    node_id = (node.get("id") or "").lower()
    label = (node.get("label") or "").lower()
    summary = (node.get("summary") or "").lower()
    symbols = [str(s).lower() for s in (node.get("symbols") or [])]

    score = 0.0
    for t in toks:
        # Path match is very informative in codebases (fastapi/security/*, auth/*, etc.)
        if t in node_id:
            score += 0.5
        if t == label:
            score += 1.0
        elif t in label:
            score += 0.6
        if t in summary:
            score += 0.35
        if any(t in s for s in symbols):
            score += 0.5

    # squish into 0..1
    return float(1.0 - math.exp(-score))


def activate(network: dict, query: str, *, threshold: float = 0.15, depth: int = 3) -> tuple[dict[str, float], dict[str, float]]:
    nodes = {n["id"]: dict(n) for n in network.get("nodes", []) if n.get("id")}
    edges = list(network.get("edges", []))

    activations: dict[str, float] = {nid: 0.0 for nid in nodes}
    for nid, node in nodes.items():
        activations[nid] = _score_node(query, node)

    # 3 hops max by spec; allow smaller via flag
    depth = max(0, min(depth, 3))
    for hop in range(depth):
        next_act = dict(activations)
        decay = _decay(hop)
        for e in edges:
            src = e.get("from")
            dst = e.get("to")
            if src not in activations or dst not in activations:
                continue
            src_act = activations[src]
            if src_act < 0.05:
                continue
            w = float(e.get("weight") or 0.0)
            mult = TYPE_MULTIPLIER.get(str(e.get("type")), 0.75)
            spread = src_act * w * mult * decay
            if spread > next_act[dst]:
                next_act[dst] = spread
        activations = next_act

    # room activations = max node activation in room
    room_act: dict[str, float] = {}
    for nid, act in activations.items():
        room = nodes[nid].get("room_id") or "other"
        room_act[room] = max(room_act.get(room, 0.0), act)

    room_act = {r: a for r, a in room_act.items() if a >= threshold}
    return room_act, activations


def run_query(repo_path: Path, query: str, *, threshold: float = 0.15, depth: int = 3) -> None:
    network_path = repo_path.resolve() / "palace-out" / "network.json"
    if not network_path.exists():
        raise SystemExit(f"network.json not found at {network_path}. Run `palace build` first.")
    network = json.loads(network_path.read_text("utf-8"))

    room_act, node_act = activate(network, query, threshold=threshold, depth=depth)
    rooms_by_id = {r["id"]: r for r in network.get("rooms", []) if r.get("id")}

    print(f'Query: "{query}"')
    print(f"Activated rooms (above threshold {threshold:.2f}):\n")
    if not room_act:
        print("  (none)\n")
        return

    ranked_rooms = sorted(room_act.items(), key=lambda kv: kv[1], reverse=True)
    for room_id, act in ranked_rooms:
        room = rooms_by_id.get(room_id, {"id": room_id, "file": f"palace-out/rooms/{room_id}.md"})
        print(f"  [{act:.2f}] {room_id:<12} {room.get('file')}")

        # top nodes in this room
        node_items = []
        for n in network.get("nodes", []):
            if (n.get("room_id") or "other") != room_id:
                continue
            nid = n.get("id")
            if nid in node_act:
                node_items.append((nid, node_act[nid]))
        node_items.sort(key=lambda kv: kv[1], reverse=True)
        top = ", ".join([f"{nid} ({a:.2f})" for nid, a in node_items[:2]])
        if top:
            print(f"         Top nodes: {top}")
        print()

    top2 = [r for r, _ in ranked_rooms[:2]]
    if top2:
        print(f"Suggested: read {', '.join([f'{r}.md' for r in top2])} first.")

