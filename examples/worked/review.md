# worked/review.md

This directory captures **real `palace build` outputs** and an honest assessment of what palace-ai currently gets right and wrong.

## What I ran

- **Fixture repo**: `palace build ./tests/fixture --no-llm --no-git`
  - Output copied to `worked/fixture/palace-out/`
- **This repo (palace-ai)**: `palace build . --no-llm --no-git`
  - Output copied to `worked/self/palace-out/`
- **Real open-source repo benchmark**: `palace build worked/repos/requests --no-llm --no-git`
  - Output copied to `worked/requests/palace-out/`

## What the palace got right

- **Deterministic AST extraction + caching**: `palace-out/cache/extractions/{sha}.json` is keyed by SHA256 content hash, and rebuilds don’t re-extract unchanged files.
- **Real structural edges**:
  - `imports` edges resolve local JS relative imports and Python module imports when they map to in-repo files.
  - `calls` edges connect call sites to files exporting matching top-level symbols (best-effort, name-based).
- **A usable navigation loop exists**:
  - `palace query "<text>"` runs spreading activation over `network.json`.
  - The visualizer is a single `palace-out/visualizer/index.html` that can be served with `palace serve` or opened directly after generation.
- **Token reduction on a real repo without LLM**:
  - For `requests` (Python, many files), the palace artifacts are ~**14x smaller** than reading the full repo by the built-in approximate token counter.

## What’s still imperfect / known limitations

- **Call graph resolution is heuristic**:
  - Calls are matched to exported symbol names across files; collisions can create false edges (common names like `main`, `run`, `get`).
  - Member calls (`obj.method()`) are indexed as `method` and may incorrectly map to unrelated exports.
- **Imports are best-effort**:
  - Python import resolution handles `pkg.mod` → `pkg/mod.py` and `pkg/mod/__init__.py` but doesn’t emulate `sys.path`/packaging rules.
  - JS bare imports (packages) are intentionally ignored; only relative imports are resolved.
- **AST-only Room files are contract-shaped but selective**:
  - To keep Room files near the ~400 token budget, AST-only mode shows only the **top exported functions** (ranked by detected call frequency) with capped call-site lists.
  - Full detail still exists in `network.json` + source, but the Room file is intentionally “orientation-first”.
- **LLM phases are implemented but not exercised in this run**:
  - Semantic per-file summaries, room consolidation, and room writing use Anthropic when `ANTHROPIC_API_KEY` is present.
  - The worked outputs here were produced without an API key, so room overviews and cross-room references are less semantic.

## Files to inspect

- `worked/fixture/palace-out/network.json` — small, easy to eyeball edges
- `worked/self/palace-out/PALACE.md` — index file an agent reads first
- `worked/requests/palace-out/visualizer/index.html` — larger graph visual check

