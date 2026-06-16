from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from palace.query.activator import activate
from palace.utils.token_counter import approx_token_count


# Files/dirs that palace's build pipeline skips; naive uses the same set so the
# corpus is identical for both arms and hit@k is directly comparable.
_EXCLUDE_DIRS = {
    ".git",
    "palace-out",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",  # matches palace's DEFAULT_IGNORES
    ".next",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
}
_SOURCE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".rs", ".java", ".rb", ".cs",
}


def _tokenize(q: str) -> list[str]:
    return [t for t in re.sub(r"[^a-z0-9]", " ", q.lower()).split() if len(t) > 1]


def _iter_source_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        try:
            parts = p.relative_to(root).parts
        except ValueError:
            continue
        if any(part in _EXCLUDE_DIRS for part in parts):
            continue
        if p.suffix in _SOURCE_EXTS:
            result.append(p)
    return sorted(result)


def _score_text(tokens: list[str], text: str) -> float:
    if not tokens:
        return 0.0
    lower = text.lower()
    return sum(1 for t in tokens if t in lower) / len(tokens)


def run_naive_arm(
    query: str,
    repo_path: Path,
    *,
    k: int = 5,
) -> tuple[list[str], int]:
    """
    Naive baseline: keyword/substring search over file paths + raw contents.

    Returns (top-k relative-path strings, total token cost of returned files).
    """
    tokens = _tokenize(query)
    scored: list[tuple[float, str, int]] = []
    for p in _iter_source_files(repo_path):
        rel = str(p.relative_to(repo_path)).replace("\\", "/")
        content = p.read_text("utf-8", errors="replace")
        score = _score_text(tokens, rel + " " + content)
        if score > 0:
            scored.append((score, rel, approx_token_count(content)))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]
    return [r for _, r, _ in top], sum(tc for _, _, tc in top)


def run_palace_arm(
    query: str,
    network: dict,
    repo_path: Path,
    *,
    k: int = 5,
    threshold: float = 0.0,
) -> tuple[list[str], int]:
    """
    Palace arm: activation spreading over the network graph.

    Returns (top-k node IDs by activation score, token cost of top-2 room markdowns).
    Token cost uses room markdown files, not raw source — this is the key efficiency claim.
    """
    room_act, node_act = activate(network, query, threshold=threshold, depth=3)
    top_nodes = sorted(
        [(nid, a) for nid, a in node_act.items() if a > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:k]
    top_node_ids = [nid for nid, _ in top_nodes]

    top_rooms = sorted(room_act.items(), key=lambda x: x[1], reverse=True)[:2]
    token_cost = 0
    rooms_dir = repo_path / "palace-out" / "rooms"
    for room_id, _ in top_rooms:
        md = rooms_dir / f"{room_id}.md"
        if md.exists():
            token_cost += approx_token_count(md.read_text("utf-8", errors="replace"))

    return top_node_ids, token_cost


def hit_at_k(returned: list[str], expected: list[str], k: int) -> float:
    """Fraction of expected items found in the top-k of returned."""
    if not expected:
        return 0.0
    found = set(returned[:k])
    return sum(1 for e in expected if e in found) / len(expected)


def run_eval(
    cases: list[dict],
    *,
    network: dict,
    repo_path: Path,
    k: int = 5,
) -> dict[str, Any]:
    """
    Run both arms on every case and return aggregated metrics.

    Result shape::

        {
            "k": 5,
            "n_cases": 10,
            "baseline": {"avg_hit_at_k": 0.9, "avg_tokens": 1800},
            "palace":   {"avg_hit_at_k": 1.0, "avg_tokens": 620},
            "per_case": [...],
        }
    """
    per_case: list[dict] = []
    b_hits: list[float] = []
    p_hits: list[float] = []
    b_toks: list[int] = []
    p_toks: list[int] = []

    for case in cases:
        query: str = case["query"]
        expected: list[str] = case["expected"]

        naive_ids, naive_cost = run_naive_arm(query, repo_path, k=k)
        palace_ids, palace_cost = run_palace_arm(query, network, repo_path, k=k)

        b_hit = hit_at_k(naive_ids, expected, k)
        p_hit = hit_at_k(palace_ids, expected, k)

        b_hits.append(b_hit)
        p_hits.append(p_hit)
        b_toks.append(naive_cost)
        p_toks.append(palace_cost)

        per_case.append({
            "query": query,
            "expected": expected,
            "baseline": {"returned": naive_ids, "hit_at_k": b_hit, "tokens": naive_cost},
            "palace": {"returned": palace_ids, "hit_at_k": p_hit, "tokens": palace_cost},
        })

    n = len(cases)
    return {
        "k": k,
        "n_cases": n,
        "baseline": {
            "avg_hit_at_k": sum(b_hits) / n if n else 0.0,
            "avg_tokens": int(sum(b_toks) / n) if n else 0,
        },
        "palace": {
            "avg_hit_at_k": sum(p_hits) / n if n else 0.0,
            "avg_tokens": int(sum(p_toks) / n) if n else 0,
        },
        "per_case": per_case,
    }
