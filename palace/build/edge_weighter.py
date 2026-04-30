from __future__ import annotations

from dataclasses import dataclass


SOURCE_BASE = {
    "ast": 1.0,
    "git": 0.8,
    "llm": 0.7,
    "inferred": 0.5,
}


TYPE_BASE_MULT = {
    "imports": 1.0,
    "calls": 0.9,
    "implements": 1.0,
    "configures": 0.75,
    "test-of": 0.5,
    "error-path": 0.5,
    "spawns": 0.5,
    "shares-schema": 0.75,
    "co-changes": 1.0,  # further modulated by raw score if present
    "inferred": 0.5,
}


def final_weight(*, edge_type: str, source: str, raw: float | None = None, llm_confidence: float | None = None) -> float:
    base = SOURCE_BASE.get(source, 0.6)
    base *= TYPE_BASE_MULT.get(edge_type, 0.75)
    if edge_type == "co-changes" and raw is not None:
        base *= max(0.0, min(1.0, raw))
    if edge_type == "shares-schema" and llm_confidence is not None:
        base *= max(0.0, min(1.0, llm_confidence))
    return min(max(base, 0.0), 1.0)

