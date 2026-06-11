from __future__ import annotations

import json
from pathlib import Path

from palace.memory.init import ensure_memory, load_attempts, load_failures, load_patterns, load_state
from palace.memory.paths import memory_paths, resolve_memory_paths
from palace.memory.schemas import utc_now_iso


def run_snapshot(repo_path: Path, *, root: Path | None = None) -> Path:
    if root is not None:
        mp = resolve_memory_paths(root=root)
        palace_out = None
    else:
        repo_path = repo_path.resolve()
        palace_out = repo_path / "palace-out"
        if not palace_out.is_dir():
            raise SystemExit(f"No palace at {palace_out}. Run `palace build` first.")
        mp = memory_paths(palace_out)

    ensure_memory(mp)
    ts = utc_now_iso().replace(":", "-")
    snap_path = mp.snapshots_dir / f"{ts}.json"

    payload: dict = {"timestamp": utc_now_iso(), "memory_dir": str(mp.memory_dir)}
    if palace_out is not None:
        payload["palace_out"] = "palace-out"
        for name in ("PALACE.md", "network.json"):
            p = palace_out / name
            if p.exists():
                if name.endswith(".json"):
                    payload[name] = json.loads(p.read_text("utf-8"))
                else:
                    payload[name] = p.read_text("utf-8")

    mem: dict = {
        "patterns": load_patterns(mp),
        "failures": load_failures(mp),
        "state": load_state(mp),
        "attempts": load_attempts(mp),
    }
    payload["memory"] = mem

    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(payload, indent=2) + "\n", "utf-8")
    print(f"Snapshot saved: {snap_path}")
    return snap_path
