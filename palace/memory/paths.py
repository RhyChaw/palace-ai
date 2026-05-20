from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryPaths:
    palace_out: Path

    @property
    def memory_dir(self) -> Path:
        return self.palace_out / "memory"

    @property
    def attempts_path(self) -> Path:
        return self.memory_dir / "attempts.jsonl"

    @property
    def patterns_path(self) -> Path:
        return self.memory_dir / "patterns.json"

    @property
    def failures_path(self) -> Path:
        return self.memory_dir / "failures.json"

    @property
    def state_path(self) -> Path:
        return self.memory_dir / "state.json"

    @property
    def snapshots_dir(self) -> Path:
        return self.palace_out / "snapshots"


def memory_paths(palace_out: Path) -> MemoryPaths:
    return MemoryPaths(palace_out=palace_out)
