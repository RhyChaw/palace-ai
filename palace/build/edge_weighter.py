from __future__ import annotations

SOURCE_BASE = {
    # Don't allow AST edges to saturate at 1.0 by default.
    "ast": 0.8,
    "git": 0.7,
    "llm": 0.6,
    "inferred": 0.4,
}


TYPE_MOD = {
    "imports": 1.0,
    "calls": 0.85,
    "implements": 0.80,
    "co-changes": 0.70,
    "shares-schema": 0.60,
    "configures": 0.55,
    "error-path": 0.50,
    "test-of": 0.40,
    "inferred": 0.30,
}


def final_weight(
    *,
    edge_type: str,
    source: str,
    from_degree: int,
    to_degree: int,
    max_degree: int,
    from_out_degree: int,
    max_out_degree: int,
    raw: float | None = None,
    llm_confidence: float | None = None,
) -> float:
    """
    Spread weights across 0..1 using:
    - source base confidence (AST still strong, but not automatically 1.0)
    - edge type modifier
    - hub penalty (edges touching "god files" downweighted)
    """
    base = SOURCE_BASE.get(source, 0.55)
    type_mod = TYPE_MOD.get(edge_type, 0.50)

    # Preserve additional raw signals where present
    if edge_type == "co-changes" and raw is not None:
        type_mod *= max(0.0, min(1.0, raw))
    if edge_type == "shares-schema" and llm_confidence is not None:
        type_mod *= max(0.0, min(1.0, llm_confidence))

    md = max(1, int(max_degree))
    hub = max(int(from_degree), int(to_degree))
    god_penalty = 1.0 - (0.3 * (hub / md))
    mo = max(1, int(max_out_degree))
    fanout_penalty = 1.0 - (0.5 * (int(from_out_degree) / mo))
    w = base * type_mod * god_penalty * fanout_penalty
    return min(max(float(w), 0.0), 1.0)

