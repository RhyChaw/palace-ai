from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from palace.memory.init import append_attempt, ensure_memory
from palace.memory.learn import _touch_state, _upsert_failure, _upsert_pattern, _heuristic_pattern
from palace.memory.llm import extract_failure_from_attempt, extract_pattern_from_attempt
from palace.memory.paths import MemoryPaths, resolve_memory_paths
from palace.memory.schemas import VALID_OUTCOMES, utc_now_iso


def add_event(
    mp: MemoryPaths,
    *,
    task: str,
    outcome: str,
    notes: str | None = None,
    approach: str | None = None,
    failure_reason: str | None = None,
    files_modified: list[str] | None = None,
    rooms_consulted: list[str] | None = None,
    patterns_used: list[str] | None = None,
    session_id: str | None = None,
    token_cost: int | None = None,
    use_llm: bool = False,
    model: str | None = None,
) -> dict[str, Any]:
    """Append an event to memory (standalone-safe; no palace build required)."""
    if not task:
        return {"ok": False, "error": "task is required"}
    if outcome not in VALID_OUTCOMES:
        return {
            "ok": False,
            "error": f"outcome must be one of: {', '.join(sorted(VALID_OUTCOMES))}",
        }

    ensure_memory(mp)
    now = utc_now_iso()
    files_modified = list(files_modified or [])
    pattern_ids: list[str] = list(patterns_used or [])

    event_id = str(uuid.uuid4())
    entry: dict[str, Any] = {
        "id": event_id,
        "timestamp": now,
        "task": task,
        "rooms_consulted": list(rooms_consulted or []),
        "approach": approach or "",
        "outcome": outcome,
        "files_modified": files_modified,
        "patterns_used": pattern_ids,
        "failure_reason": failure_reason,
        "agent_notes": notes or "",
        "session_id": session_id or "",
        "token_cost": token_cost,
    }
    append_attempt(mp, entry)

    pattern_id: str | None = None
    failure_id: str | None = None

    if outcome == "success":
        if use_llm:
            try:
                extracted = extract_pattern_from_attempt(
                    task=task,
                    files_modified=files_modified,
                    notes=notes or "",
                    approach=approach or "",
                    model=model,
                )
                pattern_id = _upsert_pattern(mp, extracted, now=now)
            except Exception as e:
                pattern_id = _upsert_pattern(
                    mp, _heuristic_pattern(task, notes or "", files_modified, now=now), now=now
                )
                return {
                    "ok": True,
                    "event_id": event_id,
                    "outcome": outcome,
                    "pattern_id": pattern_id,
                    "llm_warning": str(e),
                }
        else:
            pattern_id = _upsert_pattern(
                mp, _heuristic_pattern(task, notes or "", files_modified, now=now), now=now
            )
    elif outcome == "failure":
        if use_llm:
            try:
                extracted = extract_failure_from_attempt(
                    task=task,
                    approach=approach or "",
                    failure_reason=failure_reason or "",
                    notes=notes or "",
                    files_modified=files_modified,
                    model=model,
                )
            except Exception:
                extracted = {
                    "task_type": task[:60],
                    "approach_attempted": approach or "",
                    "failure_reason": failure_reason or notes or "unknown",
                    "resolution": "",
                }
        else:
            extracted = {
                "task_type": task[:60],
                "approach_attempted": approach or "",
                "failure_reason": failure_reason or notes or "unknown",
                "resolution": "",
            }
        failure_id = _upsert_failure(mp, extracted, now=now)

    _touch_state(mp, now=now, task=task, outcome=outcome)

    result: dict[str, Any] = {"ok": True, "event_id": event_id, "outcome": outcome}
    if pattern_id:
        result["pattern_id"] = pattern_id
    if failure_id:
        result["failure_id"] = failure_id
    return result


def add_event_at_root(
    root: Path,
    *,
    task: str,
    outcome: str,
    **kwargs: Any,
) -> dict[str, Any]:
    mp = resolve_memory_paths(root=root)
    return add_event(mp, task=task, outcome=outcome, **kwargs)
