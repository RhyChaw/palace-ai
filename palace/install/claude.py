from __future__ import annotations

import json
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

HOOK_SH = r"""#!/usr/bin/env bash
# palace-ai PreToolUse hook — remind Claude to use the memory palace before Grep/Glob.
set -euo pipefail

if [[ ! -f palace-out/PALACE.md ]]; then
  exit 0
fi

INPUT=$(cat)
python3 - "$INPUT" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
tool = payload.get("tool_name") or ""

if tool not in {"Grep", "Glob"}:
    sys.exit(0)

reason = (
    "palace-out exists. Read palace-out/PALACE.md, then run "
    '`palace query "<your task>"` to find relevant rooms before searching raw files.'
)

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )
)
PY
"""

PALACE_HOOK_MATCHER = "Grep|Glob"
PALACE_HOOK_COMMAND = "${CLAUDE_PROJECT_DIR}/.claude/hooks/palace-pretooluse.sh"
PALACE_HOOK_MARKER = "palace-pretooluse.sh"


def _palace_hook_entry() -> dict:
    return {
        "matcher": PALACE_HOOK_MATCHER,
        "hooks": [{"type": "command", "command": PALACE_HOOK_COMMAND}],
    }


def _merge_settings(existing: dict) -> dict:
    hooks = dict(existing.get("hooks") or {})
    pretool = list(hooks.get("PreToolUse") or [])
    if not any(
        PALACE_HOOK_MARKER in str(h.get("hooks"))
        for entry in pretool
        for h in (entry.get("hooks") or [])
    ):
        pretool.append(_palace_hook_entry())
    hooks["PreToolUse"] = pretool
    merged = dict(existing)
    merged["hooks"] = hooks
    return merged


def install_claude(repo_path: Path) -> None:
    repo_path = repo_path.resolve()
    repo_path.mkdir(parents=True, exist_ok=True)

    claude_md = repo_path / "CLAUDE.md"
    existing = claude_md.read_text("utf-8") if claude_md.exists() else ""
    if "## palace-ai memory palace" not in existing:
        updated = (existing.rstrip() + "\n\n" + CLAUDE_SECTION).lstrip("\n") + "\n"
        claude_md.write_text(updated, "utf-8")

    hook_path = repo_path / ".claude" / "hooks" / "palace-pretooluse.sh"
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(HOOK_SH, "utf-8")
    try:
        hook_path.chmod(0o755)
    except OSError:
        pass

    settings_path = repo_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        try:
            current = json.loads(settings_path.read_text("utf-8"))
            if not isinstance(current, dict):
                current = {}
        except json.JSONDecodeError:
            current = {}
    else:
        current = {}
    settings_path.write_text(json.dumps(_merge_settings(current), indent=2) + "\n", "utf-8")

    print("Installed Claude Code integration:")
    print(f"- Updated {claude_md}")
    print(f"- Wrote {hook_path}")
    print(f"- Registered PreToolUse hook in {settings_path}")
