from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryPaths:
    """On-disk layout for v2 memory files."""

    memory_dir: Path
    snapshots_dir: Path

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


def memory_paths(palace_out: Path) -> MemoryPaths:
    """Memory under ``{palace_out}/memory`` (repo-integrated layout)."""
    po = palace_out.resolve()
    return MemoryPaths(memory_dir=po / "memory", snapshots_dir=po / "snapshots")


def memory_paths_at_root(root: Path) -> MemoryPaths:
    """``root`` is the memory directory itself (standalone layout)."""
    r = root.expanduser().resolve()
    return MemoryPaths(memory_dir=r, snapshots_dir=r / "snapshots")


def resolve_memory_paths(*, repo_path: Path | None = None, root: Path | None = None) -> MemoryPaths:
    """
    Resolve memory file locations.

    - ``root``: standalone memory directory (e.g. ``~/.daimon/memory``).
    - otherwise: ``{repo_path}/palace-out/memory`` (default repo layout).
    """
    if root is not None:
        return memory_paths_at_root(root)
    rp = (repo_path or Path(".")).resolve()
    return memory_paths(rp / "palace-out")
