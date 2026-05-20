from __future__ import annotations

import json
from pathlib import Path

from palace.memory.init import ensure_memory
from palace.memory.paths import memory_paths
from palace.memory.schemas import utc_now_iso


def run_snapshot(repo_path: Path) -> Path:
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    if not palace_out.is_dir():
        raise SystemExit(f"No palace at {palace_out}. Run `palace build` first.")

    ensure_memory(palace_out)
    mp = memory_paths(palace_out)
    ts = utc_now_iso().replace(":", "-")
    snap_path = mp.snapshots_dir / f"{ts}.json"

    payload: dict = {"timestamp": utc_now_iso(), "palace_out": "palace-out"}
    for name in ("PALACE.md", "network.json"):
        p = palace_out / name
        if p.exists():
            if name.endswith(".json"):
                payload[name] = json.loads(p.read_text("utf-8"))
            else:
                payload[name] = p.read_text("utf-8")

    mem: dict = {}
    for key, path in (
        ("patterns", mp.patterns_path),
        ("failures", mp.failures_path),
        ("state", mp.state_path),
    ):
        if path.exists():
            mem[key] = json.loads(path.read_text("utf-8"))
    if mp.attempts_path.exists():
        mem["attempts"] = [
            json.loads(ln) for ln in mp.attempts_path.read_text("utf-8").splitlines() if ln.strip()
        ]
    payload["memory"] = mem

    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(payload, indent=2) + "\n", "utf-8")
    print(f"Snapshot saved: {snap_path}")
    return snap_path
