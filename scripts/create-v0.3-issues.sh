#!/usr/bin/env bash
# Create v0.3 roadmap issues. Requires: gh auth login
set -euo pipefail
cd "$(dirname "$0")/.."

gh issue create --title "CI: GitHub Actions workflow" --label "enhancement" --body "$(cat <<'EOF'
## Summary
Add a GitHub Actions CI workflow for palace-ai (target: v0.3).

## Scope
- Run on pull requests and pushes to `main`
- Install package in a venv and run `pytest` (e.g. `tests/test_memory.py` and future tests)
- Optional: `palace build tests/fixture --no-llm` smoke check
- Cache pip dependencies for faster runs

## Why
Catch regressions before release; only PyPI publish on tags exists today.

## Acceptance
- Green check on PRs
- Documented in README or CONTRIBUTING
EOF
)"

gh issue create --title "palace learn: update state.json without reflect" --label "enhancement" --body "$(cat <<'EOF'
## Summary
`palace learn` should incrementally update `memory/state.json` (incomplete domains, tech debt, conventions) without requiring a full `palace reflect` run.

## Current behavior
- `palace learn` appends to `attempts.jsonl` and updates patterns/failures
- `state.json` only gets `last_updated` touched; rich state comes from `palace reflect` + LLM

## Desired behavior
- On each successful/failed learn, merge lightweight state deltas (heuristic or small LLM call)
- `palace reflect` remains for cross-attempt re-derivation and confidence decay

## Acceptance
- `palace status` reflects recent learns without running reflect
- `--no-llm` path still updates basic state fields
EOF
)"

gh issue create --title "Web UI: view patterns and attempts" --label "enhancement" --body "$(cat <<'EOF'
## Summary
Browser UI to explore palace v2 memory alongside the existing graph visualizer.

## Scope
- List/filter `memory/attempts.jsonl` (outcome, task, timestamp)
- Browse `patterns.json` and `failures.json` with confidence and hit counts
- Show `state.json` game state (completed/incomplete domains, tech debt)
- Optional: link attempts → patterns; trigger reflect from UI (read-only by default)

## Notes
- Reuse or extend `palace serve` / `palace-out/visualizer/`
- Read-only; agents/humans still write memory via `palace learn` CLI

## Acceptance
- `palace serve` (or new command) opens memory + network views locally
EOF
)"

echo "Created v0.3 issues."
