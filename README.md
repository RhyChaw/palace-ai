# palace-ai

> AI agents navigate code the way humans remember — by association, not search.

![visualizer](worked/requests/palace-out/visualizer/screenshot.png)

```bash
pip install palace-ai
palace build .
palace serve
```

**42x token reduction.** Zero API key required.

---

## What it does

palace-ai turns any repo into a memory palace — a navigable network of rooms an
agent can traverse to find exactly what it needs without reading raw source files.

Instead of loading 50,000 tokens of source code, an agent reads:
1. `PALACE.md` — all rooms, 200 tokens
2. The relevant room file — architecture + function signatures + call sites, ~400 tokens
3. Only the specific source file it needs to edit

**Result: 10-42x fewer tokens. Faster agents. Less hallucination.**

---

## How it works

Every file is a node. Every relationship is a typed, weighted edge.
When an agent queries the palace, activation spreads through the network —
the same way "rajma chawal" floods your mind with culture, comfort, ingredients, season.
The rooms that light up are the ones worth reading.

---

## Quick start

```bash
pip install palace-ai
palace build .           # builds the palace (AST-only, no API key)
palace serve             # opens the visualizer
palace query "auth flow" # finds relevant rooms
palace install claude    # hooks into Claude Code
```

## LLM mode (semantic room files)

```bash
export ANTHROPIC_API_KEY=sk-...
palace build .           # adds architectural overviews to room files
```

---

*Built for agents. Inspired by how humans actually remember things.*

