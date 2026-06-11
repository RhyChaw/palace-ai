from __future__ import annotations

import json

from palace.memory.paths import MemoryPaths
from palace.memory.schemas import empty_failures, empty_patterns, empty_state
from palace.utils.cache import load_json, write_json


def ensure_memory(mp: MemoryPaths) -> None:
    """Create v2 memory scaffolding (empty derived files + attempts log)."""
    mp.memory_dir.mkdir(parents=True, exist_ok=True)
    mp.snapshots_dir.mkdir(parents=True, exist_ok=True)

    if not mp.attempts_path.exists():
        mp.attempts_path.write_text("", "utf-8")

    if not mp.patterns_path.exists():
        write_json(mp.patterns_path, empty_patterns())
    if not mp.failures_path.exists():
        write_json(mp.failures_path, empty_failures())
    if not mp.state_path.exists():
        write_json(mp.state_path, empty_state())


def memory_exists(mp: MemoryPaths) -> bool:
    return mp.memory_dir.is_dir()


def load_patterns(mp: MemoryPaths) -> dict:
    return load_json(mp.patterns_path, default=empty_patterns())


def load_failures(mp: MemoryPaths) -> dict:
    return load_json(mp.failures_path, default=empty_failures())


def load_state(mp: MemoryPaths) -> dict:
    return load_json(mp.state_path, default=empty_state())


def save_patterns(mp: MemoryPaths, obj: dict) -> None:
    write_json(mp.patterns_path, obj)


def save_failures(mp: MemoryPaths, obj: dict) -> None:
    write_json(mp.failures_path, obj)


def save_state(mp: MemoryPaths, obj: dict) -> None:
    write_json(mp.state_path, obj)


def load_attempts(mp: MemoryPaths) -> list[dict]:
    if not mp.attempts_path.exists():
        return []
    entries: list[dict] = []
    for line in mp.attempts_path.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def append_attempt(mp: MemoryPaths, entry: dict) -> None:
    mp.memory_dir.mkdir(parents=True, exist_ok=True)
    with mp.attempts_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

