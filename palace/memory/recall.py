from __future__ import annotations

from typing import Any

from palace.memory.init import ensure_memory, load_attempts, load_failures, load_patterns, load_state
from palace.memory.paths import MemoryPaths


def _tokenize(q: str) -> set[str]:
    return {t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in q).split() if t}


def _relevance_score(query: str, text: str) -> float:
    toks = _tokenize(query)
    if not toks:
        return 0.0
    lower = text.lower()
    hits = sum(1 for t in toks if t in lower)
    return hits / len(toks)


def _score_event(query: str, event: dict[str, Any]) -> float:
    blob = " ".join(
        [
            str(event.get("task") or ""),
            str(event.get("agent_notes") or ""),
            str(event.get("approach") or ""),
            str(event.get("failure_reason") or ""),
        ]
    )
    return _relevance_score(query, blob)


def _score_pattern(query: str, pattern: dict[str, Any]) -> float:
    blob = " ".join(
        [
            str(pattern.get("name") or ""),
            str(pattern.get("domain") or ""),
            str(pattern.get("description") or ""),
            " ".join(str(s) for s in (pattern.get("implementation_sequence") or [])),
            str(pattern.get("codebase_specific_notes") or ""),
        ]
    )
    return _relevance_score(query, blob) * float(pattern.get("confidence") or 0.5)


def _score_failure(query: str, failure: dict[str, Any]) -> float:
    blob = " ".join(
        [
            str(failure.get("task_type") or ""),
            str(failure.get("approach_attempted") or ""),
            str(failure.get("failure_reason") or ""),
            str(failure.get("resolution") or ""),
        ]
    )
    return _relevance_score(query, blob)


def recall_memory(
    mp: MemoryPaths,
    query: str,
    *,
    max_events: int = 10,
    max_patterns: int = 5,
    max_failures: int = 3,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Keyword recall over events and derived patterns/failures."""
    ensure_memory(mp)
    q = query.strip()
    if not q:
        return {"ok": False, "error": "query is required"}

    events = load_attempts(mp)
    patterns = load_patterns(mp).get("patterns") or []
    failures = load_failures(mp).get("failures") or []
    state = load_state(mp)

    scored_events = [
        (score, event)
        for event in events
        if (score := _score_event(q, event)) > min_score
    ]
    scored_events.sort(key=lambda x: x[0], reverse=True)

    scored_patterns = [
        (score, pattern)
        for pattern in patterns
        if (score := _score_pattern(q, pattern)) > min_score
    ]
    scored_patterns.sort(key=lambda x: x[0], reverse=True)

    scored_failures = [
        (score, failure)
        for failure in failures
        if (score := _score_failure(q, failure)) > min_score
    ]
    scored_failures.sort(key=lambda x: x[0], reverse=True)

    return {
        "ok": True,
        "query": q,
        "events": [
            {**event, "_score": round(score, 4)} for score, event in scored_events[:max_events]
        ],
        "patterns": [
            {**pattern, "_score": round(score, 4)} for score, pattern in scored_patterns[:max_patterns]
        ],
        "failures": [
            {**failure, "_score": round(score, 4)} for score, failure in scored_failures[:max_failures]
        ],
        "state": state,
        "counts": {
            "events": len(events),
            "patterns": len(patterns),
            "failures": len(failures),
        },
    }
