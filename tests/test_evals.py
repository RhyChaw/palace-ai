"""
CI smoke test for the retrieval-quality eval harness.

Builds palace over a copy of palace-ai's own source (dogfooding), runs both
arms on the labeled cases, and asserts that palace beats the naive baseline on
hit@k and token efficiency.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from palace.build.pipeline import build_palace
from palace.evals.harness import run_eval


_REPO_ROOT = Path(__file__).parent.parent
_CASES_PATH = _REPO_ROOT / "evals" / "cases.json"

# Thresholds — set conservatively so they catch genuine regressions without
# being brittle against minor score fluctuations.
_HIT_AT_K = 5
_MIN_PALACE_HIT = 0.8   # palace must hit ≥ 80% of labeled cases
_MIN_BASELINE_DELTA = 0.0  # palace hit@k ≥ baseline hit@k


@pytest.fixture(scope="module")
def eval_context(tmp_path_factory: pytest.TempPathFactory):
    """
    One-time setup: copy palace source into a clean tmp dir, build palace over
    it, and return (network_dict, repo_path).  Scoped to module so the build
    runs once for all tests in this file.
    """
    tmp = tmp_path_factory.mktemp("palace_eval")

    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "palace-out", ".venv")
    for item in ("palace", "tests", "pyproject.toml"):
        src = _REPO_ROOT / item
        if src.is_dir():
            shutil.copytree(src, tmp / item, ignore=ignore)
        elif src.exists():
            shutil.copy2(src, tmp / item)

    build_palace(tmp, use_git=False, use_llm=False, model=None)

    network = json.loads((tmp / "palace-out" / "network.json").read_text("utf-8"))
    return network, tmp


def test_palace_beats_baseline(eval_context):
    """Palace must match or exceed naive baseline on hit@k and use fewer tokens."""
    network, repo_path = eval_context
    cases = json.loads(_CASES_PATH.read_text("utf-8"))

    results = run_eval(cases, network=network, repo_path=repo_path, k=_HIT_AT_K)

    p_hit = results["palace"]["avg_hit_at_k"]
    b_hit = results["baseline"]["avg_hit_at_k"]
    p_tok = results["palace"]["avg_tokens"]
    b_tok = results["baseline"]["avg_tokens"]

    assert p_hit >= _MIN_PALACE_HIT, (
        f"Palace hit@{_HIT_AT_K} {p_hit:.3f} below minimum {_MIN_PALACE_HIT:.3f}\n"
        + _per_case_summary(results["per_case"])
    )
    assert p_hit >= b_hit - _MIN_BASELINE_DELTA, (
        f"Retrieval regression: palace hit@{_HIT_AT_K} {p_hit:.3f} < baseline {b_hit:.3f}\n"
        + _per_case_summary(results["per_case"])
    )
    assert p_tok < b_tok, (
        f"Token efficiency regression: palace avg tokens ({p_tok}) ≥ baseline ({b_tok})"
    )


def _per_case_summary(per_case: list[dict]) -> str:
    lines = ["", "Per-case breakdown:"]
    for i, c in enumerate(per_case, 1):
        b = c["baseline"]
        p = c["palace"]
        lines.append(
            f"  [{i:2d}] B={b['hit_at_k']:.2f} P={p['hit_at_k']:.2f}  {c['query'][:60]}"
        )
    return "\n".join(lines)
