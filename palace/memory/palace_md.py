from __future__ import annotations

import json
from pathlib import Path

from palace.memory.init import load_attempts, load_failures, load_patterns, load_state, memory_exists
from palace.memory.schemas import utc_now_iso


def _format_game_state(state: dict) -> str:
    lines: list[str] = []
    completed = state.get("completed_domains") or []
    if completed:
        lines.append(f"**Completed:** {', '.join(completed)}")
    incomplete = state.get("incomplete_domains") or []
    if incomplete:
        lines.append("**In progress / gaps:**")
        for item in incomplete:
            if isinstance(item, dict):
                lines.append(
                    f"- **{item.get('domain', '?')}**: exists — {item.get('what_exists', '?')}; "
                    f"missing — {item.get('what_is_missing', '?')}"
                )
                loc = item.get("likely_location")
                if loc:
                    lines.append(f"  Likely: {loc}")
            else:
                lines.append(f"- {item}")
    debt = state.get("known_tech_debt") or []
    if debt:
        lines.append("**Tech debt:**")
        for d in debt[:8]:
            lines.append(f"- {d}")
    decisions = state.get("architectural_decisions") or []
    if decisions:
        lines.append("**Architectural decisions:**")
        for d in decisions[:8]:
            lines.append(f"- {d}")
    conventions = state.get("team_conventions") or []
    if conventions:
        lines.append("**Conventions:**")
        for c in conventions[:8]:
            lines.append(f"- {c}")
    return "\n".join(lines) if lines else "_No game state recorded yet. Run `palace learn` and `palace reflect`._"


def _format_patterns(patterns: list[dict], *, top_n: int = 5) -> str:
    if not patterns:
        return "_No patterns yet. Log successes with `palace learn`._"
    ranked = sorted(patterns, key=lambda p: float(p.get("confidence") or 0), reverse=True)[:top_n]
    lines: list[str] = []
    for p in ranked:
        conf = float(p.get("confidence") or 0)
        lines.append(f"### {p.get('name') or p.get('id')} (confidence {conf:.2f})")
        if p.get("description"):
            lines.append(str(p["description"]))
        notes = p.get("codebase_specific_notes")
        if notes:
            lines.append(f"_{notes}_")
        anti = p.get("anti_patterns") or []
        if anti:
            lines.append("Avoid:")
            for a in anti[:4]:
                lines.append(f"- {a}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_failures(failures: list[dict]) -> str:
    if not failures:
        return "_No failure modes recorded yet._"
    lines: list[str] = []
    for f in sorted(failures, key=lambda x: int(x.get("times_hit") or 0), reverse=True)[:8]:
        hits = f.get("times_hit", 1)
        lines.append(f"- **{f.get('task_type', 'unknown')}** (hit {hits}x): {f.get('failure_reason', '')}")
        if f.get("resolution"):
            lines.append(f"  → Use instead: {f['resolution']}")
    return "\n".join(lines)


def _format_rooms(network: dict) -> str:
    rooms = network.get("rooms") or []
    if not rooms:
        return "_No rooms in network._"
    lines = ["| room_id | label | files | summary |", "|---|---:|---:|---|"]
    for r in rooms:
        lines.append(
            f"| {r.get('id', '')} | {r.get('label', '')} | {len(r.get('files') or [])} | {r.get('summary') or ''} |"
        )
    return "\n".join(lines)


def regenerate_palace_md(repo_path: Path) -> str:
    """Rebuild PALACE.md with v2 memory sections + v1 room index."""
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    network_path = palace_out / "network.json"
    network: dict = {}
    if network_path.exists():
        network = json.loads(network_path.read_text("utf-8"))

    repo_name = network.get("repo") or repo_path.name
    attempts_n = len(load_attempts(palace_out)) if memory_exists(palace_out) else 0
    patterns_n = 0
    patterns: list[dict] = []
    failures: list[dict] = []
    state: dict = {}
    if memory_exists(palace_out):
        patterns = load_patterns(palace_out).get("patterns") or []
        patterns_n = len(patterns)
        failures = load_failures(palace_out).get("failures") or []
        state = load_state(palace_out)

    generated = state.get("last_updated") or utc_now_iso()
    lines: list[str] = [
        f"# Palace — {repo_name}",
        f"Generated: {generated} | Attempts: {attempts_n} | Patterns: {patterns_n}",
        "",
        "This repository has a **memory palace**: rooms for orientation, a queryable network, "
        "and (v2) institutional memory from past agent attempts.",
        "",
    ]

    if memory_exists(palace_out):
        lines.extend(
            [
                "## Game State",
                "",
                _format_game_state(state),
                "",
                "## What We Know Works",
                "",
                _format_patterns(patterns),
                "",
                "## What To Avoid",
                "",
                _format_failures(failures),
                "",
            ]
        )

    lines.extend(
        [
            "## Room Index",
            "",
            _format_rooms(network),
            "",
            "## Navigation",
            "",
            "1. Read this file (`palace-out/PALACE.md`)",
            "2. Run `palace query \"<task>\"` for rooms + relevant patterns",
            "3. Open room files in `palace-out/rooms/`",
            "4. After completing a task, run `palace learn` to update institutional memory",
            "",
        ]
    )

    content = "\n".join(lines).rstrip() + "\n"
    (palace_out / "PALACE.md").write_text(content, "utf-8")
    return content
