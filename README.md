# palace-ai

> AI agents navigate code the way humans remember — by association, not search.

<img width="1512" height="827" alt="palace-ai visualizer" src="https://github.com/user-attachments/assets/bc764e78-b8d3-44a6-96a3-52482fc94829" />

```bash
pip install palace-ai
palace build .
palace query "auth flow"
```

**Build a traversable memory palace for any repository.**  
palace-ai turns a codebase into rooms and typed relationships so agents orient **before** opening raw files.

**AST-only by default** — no API key. Use `--llm` plus `ANTHROPIC_API_KEY` for richer room summaries.

---

## What it does

Instead of dumping tens of thousands of tokens of source into context, an agent can read:

1. **`palace-out/PALACE.md`** — map of rooms
2. **One room file** — structure, exports, call hints
3. **Only the source files it actually needs**

On medium-to-large repos, navigation via the palace is often **10–42× smaller** in tokens than reading the full tree (run `palace stats` after a build).

---

## Quick start

```bash
pip install palace-ai
palace build .
palace query "your topic"
palace serve                    # optional: graph visualizer
palace install claude           # Claude Code: CLAUDE.md + PreToolUse hook
```

**Explicit AST-only** (same as default):

```bash
palace build . --no-llm
```

**LLM-enriched rooms:**

```bash
export ANTHROPIC_API_KEY=sk-...
palace build . --llm
```

---

## Repo layout

| Path | Purpose |
|------|---------|
| `palace/` | Python package |
| `palace-out/` | **Small checked-in sample** (from `tests/fixture`) |
| `examples/worked/` | Larger pre-built palaces (e.g. requests) for demos |
| `tests/fixture/` | Tiny JS/Python fixtures for local builds |

---

## 2-minute demo

**After clone** — sample palace is at `./palace-out/`:

```bash
pip install palace-ai
git clone https://github.com/RhyChaw/palace-ai.git && cd palace-ai
palace query "build" --threshold 0.05
palace serve
```

**Larger graph** — pre-built **requests** palace:

```bash
git clone https://github.com/RhyChaw/palace-ai.git && cd palace-ai
palace query "auth flow" --path examples/worked/requests
palace serve --path examples/worked/requests
```

---

## License

MIT — see [LICENSE](LICENSE).
