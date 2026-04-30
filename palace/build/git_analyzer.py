from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from git import Repo


@dataclass(frozen=True)
class CoChangeEdge:
    a: str
    b: str
    raw_score: float  # 0..1
    commits_together: int


def cochange_edges(repo_path: Path, *, file_ids: set[str], max_commits: int = 400) -> list[CoChangeEdge]:
    """
    Co-change analysis:
    For each commit, record touched source files.
    For each pair, score = commits_together / total_commits_considered.
    """
    repo = Repo(repo_path, search_parent_directories=True)
    commits = list(repo.iter_commits(max_count=max_commits))
    if not commits:
        return []

    total = 0
    pair_counts: Counter[tuple[str, str]] = Counter()
    for c in commits:
        try:
            files = [f for f in c.stats.files.keys()]
        except Exception:
            continue
        touched = sorted({f for f in files if f in file_ids})
        if len(touched) < 2:
            continue
        total += 1
        for i in range(len(touched)):
            for j in range(i + 1, len(touched)):
                a, b = touched[i], touched[j]
                pair_counts[(a, b)] += 1

    if total == 0:
        return []

    edges: list[CoChangeEdge] = []
    for (a, b), n in pair_counts.items():
        raw = n / total
        edges.append(CoChangeEdge(a=a, b=b, raw_score=raw, commits_together=n))
    edges.sort(key=lambda e: e.raw_score, reverse=True)
    return edges

