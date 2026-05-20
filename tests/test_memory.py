from __future__ import annotations

import json
from pathlib import Path

from palace.memory.init import ensure_memory, load_attempts, load_patterns, memory_exists
from palace.memory.learn import run_learn
from palace.memory.palace_md import regenerate_palace_md


def test_learn_appends_attempt_and_pattern(tmp_path: Path) -> None:
    palace_out = tmp_path / "palace-out"
    palace_out.mkdir()
    (palace_out / "network.json").write_text(
        json.dumps({"repo": "test", "rooms": [], "nodes": [], "edges": []}),
        encoding="utf-8",
    )
    ensure_memory(palace_out)

    run_learn(
        tmp_path,
        task="fix imports",
        outcome="success",
        files_modified=["a.py"],
        notes="use relative imports",
        use_llm=False,
    )

    assert memory_exists(palace_out)
    attempts = load_attempts(palace_out)
    assert len(attempts) == 1
    assert attempts[0]["outcome"] == "success"
    patterns = load_patterns(palace_out).get("patterns") or []
    assert len(patterns) == 1
    md = regenerate_palace_md(tmp_path)
    assert "What We Know Works" in md
    assert "fix imports" in md or "fix_imports" in md
