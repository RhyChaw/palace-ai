from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from palace.memory.add import add_event
from palace.memory.paths import resolve_memory_paths
from palace.memory.recall import recall_memory
from palace.memory.reflect import reflect_memory


def _emit_json(data: dict[str, Any], *, exit_code: int = 0) -> None:
    print(json.dumps(data, indent=2, default=str))
    if exit_code != 0:
        raise SystemExit(exit_code)


def _emit_error(message: str, *, code: int = 1) -> None:
    _emit_json({"ok": False, "error": message}, exit_code=code)


def cmd_recall(*, root: Path, query: str) -> None:
    mp = resolve_memory_paths(root=root)
    result = recall_memory(mp, query)
    if not result.get("ok"):
        _emit_error(str(result.get("error") or "recall failed"))
    _emit_json(result)


def cmd_reflect(
    *,
    root: Path,
    use_llm: bool = True,
    model: str | None = None,
) -> None:
    mp = resolve_memory_paths(root=root)
    try:
        result = reflect_memory(mp, use_llm=use_llm, model=model, write_report=False)
    except Exception as e:
        _emit_error(str(e))
    _emit_json(result)


def cmd_add(
    *,
    root: Path,
    task: str,
    outcome: str,
    notes: str | None = None,
    approach: str | None = None,
    failure_reason: str | None = None,
    use_llm: bool = False,
    model: str | None = None,
) -> None:
    mp = resolve_memory_paths(root=root)
    result = add_event(
        mp,
        task=task,
        outcome=outcome,
        notes=notes,
        approach=approach,
        failure_reason=failure_reason,
        use_llm=use_llm,
        model=model,
    )
    if not result.get("ok"):
        _emit_error(str(result.get("error") or "add failed"))
    _emit_json(result)
