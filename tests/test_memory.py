from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from palace.memory.add import add_event
from palace.memory.init import ensure_memory, load_attempts, load_patterns, memory_exists
from palace.memory.learn import run_learn
from palace.memory.palace_md import regenerate_palace_md
from palace.memory.paths import memory_paths, memory_paths_at_root
from palace.memory.recall import recall_memory
from palace.memory.reflect import reflect_memory


def test_learn_appends_attempt_and_pattern(tmp_path: Path) -> None:
    palace_out = tmp_path / "palace-out"
    palace_out.mkdir()
    (palace_out / "network.json").write_text(
        json.dumps({"repo": "test", "rooms": [], "nodes": [], "edges": []}),
        encoding="utf-8",
    )
    mp = memory_paths(palace_out)
    ensure_memory(mp)

    run_learn(
        tmp_path,
        task="fix imports",
        outcome="success",
        files_modified=["a.py"],
        notes="use relative imports",
        use_llm=False,
    )

    assert memory_exists(mp)
    attempts = load_attempts(mp)
    assert len(attempts) == 1
    assert attempts[0]["outcome"] == "success"
    patterns = load_patterns(mp).get("patterns") or []
    assert len(patterns) == 1
    md = regenerate_palace_md(tmp_path)
    assert "What We Know Works" in md
    assert "fix imports" in md or "fix_imports" in md


def test_standalone_memory_without_palace_build(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    mp = memory_paths_at_root(root)

    result = reflect_memory(mp, use_llm=False)
    assert result["ok"] is True
    assert result["attempts_count"] == 0

    add_event(
        mp,
        task="reply to client email about invoice",
        outcome="success",
        notes="used template from last month",
        use_llm=False,
    )
    add_event(
        mp,
        task="schedule dentist appointment",
        outcome="partial",
        notes="left voicemail",
        use_llm=False,
    )

    recall = recall_memory(mp, "invoice")
    assert recall["ok"] is True
    assert len(recall["events"]) == 1
    assert "invoice" in recall["events"][0]["task"].lower()


def test_mem_cli_reflect_and_recall(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    mp = memory_paths_at_root(root)
    ensure_memory(mp)
    with mp.attempts_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "id": "evt-1",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "task": "send follow-up email to vendor",
                    "outcome": "success",
                    "agent_notes": "kept subject line short",
                    "approach": "",
                    "files_modified": [],
                    "patterns_used": [],
                    "failure_reason": None,
                    "rooms_consulted": [],
                    "session_id": "",
                    "token_cost": None,
                }
            )
            + "\n"
        )

    reflect_proc = subprocess.run(
        [sys.executable, "-m", "palace.cli", "mem", "reflect", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert reflect_proc.returncode == 0, reflect_proc.stderr
    reflect_data = json.loads(reflect_proc.stdout)
    assert reflect_data["ok"] is True
    assert reflect_data["attempts_count"] == 1

    recall_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "palace.cli",
            "mem",
            "recall",
            "--root",
            str(root),
            "--query",
            "email",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert recall_proc.returncode == 0, recall_proc.stderr
    recall_data = json.loads(recall_proc.stdout)
    assert recall_data["ok"] is True
    assert len(recall_data["events"]) >= 1
    assert "email" in recall_data["events"][0]["task"].lower()
