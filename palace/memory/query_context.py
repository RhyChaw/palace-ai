from __future__ import annotations

from pathlib import Path

from palace.memory.init import load_failures, load_patterns, load_state, memory_exists


def _tokenize(q: str) -> set[str]:
    return {t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in q).split() if t}


def _relevance_score(query: str, text: str) -> float:
    toks = _tokenize(query)
    if not toks:
        return 0.0
    lower = text.lower()
    hits = sum(1 for t in toks if t in lower)
    return hits / len(toks)


def format_memory_context(repo_path: Path, query: str, *, max_patterns: int = 3, max_failures: int = 2) -> str:
    palace_out = repo_path.resolve() / "palace-out"
    if not memory_exists(palace_out):
        return ""

    patterns = load_patterns(palace_out).get("patterns") or []
    failures = load_failures(palace_out).get("failures") or []
    state = load_state(palace_out)

    scored_patterns = []
    for p in patterns:
        blob = " ".join(
            [
                str(p.get("name") or ""),
                str(p.get("domain") or ""),
                str(p.get("description") or ""),
                " ".join(p.get("implementation_sequence") or []),
                str(p.get("codebase_specific_notes") or ""),
            ]
        )
        score = _relevance_score(query, blob) * float(p.get("confidence") or 0.5)
        if score > 0:
            scored_patterns.append((score, p))
    scored_patterns.sort(key=lambda x: x[0], reverse=True)

    scored_failures = []
    for f in failures:
        blob = " ".join(
            [
                str(f.get("task_type") or ""),
                str(f.get("approach_attempted") or ""),
                str(f.get("failure_reason") or ""),
                str(f.get("resolution") or ""),
            ]
        )
        score = _relevance_score(query, blob)
        if score > 0:
            scored_failures.append((score, f))
    scored_failures.sort(key=lambda x: x[0], reverse=True)

    lines: list[str] = []

    if scored_patterns:
        lines.append("\nRelevant patterns from memory:")
        for _, p in scored_patterns[:max_patterns]:
            conf = float(p.get("confidence") or 0)
            name = p.get("name") or p.get("id")
            lines.append(f"→ {p.get('id')} ({name}, confidence: {conf:.2f})")
            note = p.get("codebase_specific_notes") or p.get("description") or ""
            if note:
                lines.append(f"  {note[:200]}")
            seq = p.get("implementation_sequence") or []
            if seq:
                lines.append(f"  See: {', '.join(str(s) for s in seq[:3])}")

    if scored_failures:
        lines.append("\nKnown failure modes:")
        for _, f in scored_failures[:max_failures]:
            reason = f.get("failure_reason") or f.get("task_type")
            hits = f.get("times_hit", 1)
            lines.append(f"→ {reason} (hit {hits}x)")
            if f.get("resolution"):
                lines.append(f"  Resolution: {f['resolution']}")

    state_lines: list[str] = []
    debt = state.get("known_tech_debt") or []
    for d in debt:
        if _relevance_score(query, str(d)) > 0:
            state_lines.append(f"→ {d}")
    incomplete = state.get("incomplete_domains") or []
    for item in incomplete:
        if not isinstance(item, dict):
            continue
        blob = f"{item.get('domain')} {item.get('what_is_missing')} {item.get('what_exists')}"
        if _relevance_score(query, blob) > 0:
            state_lines.append(f"→ {item.get('domain')}: {item.get('what_is_missing')}")
    decisions = state.get("architectural_decisions") or []
    for d in decisions:
        if _relevance_score(query, str(d)) > 0:
            state_lines.append(f"→ {d}")
    conventions = state.get("team_conventions") or []
    for c in conventions:
        if _relevance_score(query, str(c)) > 0:
            state_lines.append(f"→ {c}")

    if state_lines:
        lines.append("\nState context:")
        lines.extend(state_lines[:6])

    return "\n".join(lines) if lines else ""
