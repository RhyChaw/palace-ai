from __future__ import annotations

from pathlib import Path


CLAUDE_SECTION = """## palace-ai memory palace

This repo has a memory palace. Before answering any architecture question or
touching any file, read `palace-out/PALACE.md` to orient yourself.

Navigation:
1. Read `palace-out/PALACE.md` — see all rooms (~200 tokens)
2. Run `palace query "<your question>"` to find relevant rooms
3. Read the relevant room file(s) in `palace-out/rooms/`
4. Only then open source files — and only the specific ones linked in the room file

Never grep through raw source files when the palace exists.
"""


HOOK_SH = """#!/usr/bin/env bash
set -euo pipefail

echo "palace-ai: Memory palace exists. Read palace-out/PALACE.md before searching raw files."
echo "Relevant rooms for your current task can be found with: palace query \\"$1\\""
"""


def install_claude(repo_path: Path) -> None:
    repo_path = repo_path.resolve()

    claude_md = repo_path / "CLAUDE.md"
    existing = claude_md.read_text("utf-8") if claude_md.exists() else ""
    if "## palace-ai memory palace" not in existing:
        updated = (existing.rstrip() + "\n\n" + CLAUDE_SECTION).lstrip("\n") + "\n"
        claude_md.write_text(updated, "utf-8")

    hook_path = repo_path / ".claude" / "hooks" / "pre-tool-use.sh"
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(HOOK_SH, "utf-8")
    try:
        hook_path.chmod(0o755)
    except Exception:
        pass

    print("Installed Claude integration:")
    print(f"- Updated {claude_md}")
    print(f"- Wrote {hook_path}")

