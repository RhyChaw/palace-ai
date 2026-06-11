from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from palace.memory.init import ensure_memory, load_attempts, load_failures, load_patterns, load_state, memory_exists
from palace.memory.paths import memory_paths, resolve_memory_paths


def _format_ago(iso: str | None) -> str:
    if not iso:
        return "never"
    try:
        ts = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        secs = int(delta.total_seconds())
        if secs < 60:
            return "just now"
        if secs < 3600:
            return f"{secs // 60} minutes ago"
        if secs < 86400:
            return f"{secs // 3600} hours ago"
        return f"{secs // 86400} days ago"
    except ValueError:
        return iso


def show_status(repo_path: Path, *, root: Path | None = None) -> None:
    if root is not None:
        mp = resolve_memory_paths(root=root)
        palace_label = str(mp.memory_dir)
    else:
        repo_path = repo_path.resolve()
        palace_out = repo_path / "palace-out"
        if not palace_out.is_dir():
            raise SystemExit(f"No palace at {palace_out}. Run `palace build` first.")
        mp = memory_paths(palace_out)
        palace_label = str(palace_out)

    if not memory_exists(mp):
        if root is not None:
            print(f"No memory at {mp.memory_dir}.")
            return
        print("Palace v1 (no memory/). Run `palace build` to scaffold v2 memory.")
        return

    ensure_memory(mp)
    attempts = load_attempts(mp)
    patterns = load_patterns(mp).get("patterns") or []
    failures = load_failures(mp).get("failures") or []
    state = load_state(mp)

    print("Palace v2 Status")
    print("────────────────")
    print(f"Memory: {palace_label}")
    print(f"Attempts logged: {len(attempts)}")
    print(f"Patterns learned: {len(patterns)}")
    print(f"Known failure modes: {len(failures)}")
    print(f"Last updated: {_format_ago(state.get('last_updated'))}")
    print()

    completed = state.get("completed_domains") or []
    if completed:
        print(f"Completed domains: {', '.join(completed)}")
    incomplete = state.get("incomplete_domains") or []
    if incomplete:
        print("Incomplete domains:")
        for item in incomplete:
            if isinstance(item, dict):
                domain = item.get("domain", "?")
                missing = item.get("what_is_missing", "")
                print(f"  → {domain}: {missing}")
            else:
                print(f"  → {item}")
    debt = state.get("known_tech_debt") or []
    if debt:
        print(f"\nActive tech debt: {len(debt)} item(s)")
        for d in debt[:5]:
            print(f"  • {d}")
    decisions = state.get("architectural_decisions") or []
    if decisions:
        print(f"Architectural decisions: {len(decisions)} documented")
