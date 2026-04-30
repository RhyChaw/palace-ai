from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


@dataclass
class Node:
    id: str
    type: str = "file"
    room_id: str | None = None
    subtree_id: str | None = None
    label: str | None = None
    summary: str | None = None
    symbols: list[str] = field(default_factory=list)
    language: str | None = None
    size_tokens: int | None = None
    activation: float = 0.0
    hash: str | None = None


@dataclass
class Edge:
    from_: str
    to: str
    type: str
    weight: float
    evidence: str
    source: str

    def to_json(self) -> dict[str, Any]:
        return {
            "from": self.from_,
            "to": self.to,
            "type": self.type,
            "weight": float(self.weight),
            "evidence": self.evidence,
            "source": self.source,
        }


@dataclass
class Room:
    id: str
    label: str
    color: str
    files: list[str]
    subtrees: dict[str, list[str]] = field(default_factory=dict)
    cross_room_refs: list[dict[str, Any]] = field(default_factory=list)
    summary: str | None = None
    file: str | None = None
    token_count: int | None = None


def build_network_json(
    *,
    repo_name: str,
    nodes: Iterable[Node],
    edges: Iterable[Edge],
    rooms: Iterable[Room],
    god_files: list[dict[str, Any]] | None = None,
    surprising_edges: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    node_list = [asdict(n) for n in nodes]
    edge_list = [e.to_json() for e in edges]
    room_list = [asdict(r) for r in rooms]
    stats = {
        "nodes": len(node_list),
        "edges": len(edge_list),
        "rooms": len(room_list),
        "languages": sorted({n.get("language") for n in node_list if n.get("language")}),
    }
    return {
        "version": "1.0",
        "built_at": now,
        "repo": repo_name,
        "stats": stats,
        "nodes": node_list,
        "edges": edge_list,
        "rooms": room_list,
        "god_files": god_files or [],
        "surprising_edges": surprising_edges or [],
    }

