# palace-ai — PLAN.md

> **Mission:** Give AI agents the same associative memory humans use. Not retrieval. Not search. Activation — the way "rajma chawal" floods your mind with culture, comfort, ingredients, and season all at once. palace-ai turns any repository into a navigable memory palace: rooms an agent can orient itself in, a typed associative network it can traverse, and a visualizer that shows every connection by strength.

---

## Table of Contents

1. [The Core Idea](#1-the-core-idea)
2. [How It Works — Mental Model](#2-how-it-works--mental-model)
3. [Architecture Overview](#3-architecture-overview)
4. [Data Structures](#4-data-structures)
5. [Output File Structure](#5-output-file-structure)
6. [The Room File Format](#6-the-room-file-format)
7. [The Associative Network](#7-the-associative-network)
8. [The Visualizer](#8-the-visualizer)
9. [The Indexer — Build Pipeline](#9-the-indexer--build-pipeline)
10. [CLI Interface](#10-cli-interface)
11. [Agent Interface](#11-agent-interface)
12. [Tech Stack](#12-tech-stack)
13. [Repo Structure](#13-repo-structure)
14. [Implementation Phases](#14-implementation-phases)
15. [Edge Type Taxonomy](#15-edge-type-taxonomy)
16. [Token Budget Analysis](#16-token-budget-analysis)
17. [Design Decisions and Tradeoffs](#17-design-decisions-and-tradeoffs)

---

## 1. The Core Idea

Every existing memory system for AI agents is built around *retrieval* — you store something, you look it up later. RAG, vector databases, knowledge graphs: all retrieval. The mental model is a library. You go to the shelf, you get the book.

Human memory does not work like this. Human memory works by *activation cascades*. When you hear "rajma chawal," you don't retrieve a record. Your brain simultaneously fires: Indian cuisine, comfort food, winter, home, Mom's cooking, kidney beans, ghee, Sunday afternoon. The word arrives and a whole landscape lights up in parallel. The paths are typed — this is a *feels-like* connection, that is a *culture-of* connection, this one is an *ingredient-of* connection. The paths have weights — some fire strongly, some faintly.

palace-ai builds exactly this for code repositories. Every file is a node. Every relationship between files has a typed edge with a strength. An agent that has a palace doesn't search — it fires a query against the network and reads whichever rooms light up above a threshold. It sees the whole landscape of a codebase in the same way a human expert does: not as folders, but as a web of meaning.

**The three-layer design:**

```
Layer 3 — Rooms (palace/rooms/*.md)
         The agent reads ONE file to understand an entire architectural section.
         Function headers, call-site links, cross-room references. ~400 tokens each.
         The agent never needs to open source files to orient itself.

Layer 2 — Associative Network (palace-out/network.json)
         Typed edges between every file node. The agent fires a query,
         activation spreads, top-K rooms are identified. This is the navigation layer.

Layer 1 — Source files (your actual code)
         Only opened when the agent has already identified exactly which
         lines it needs. Maximum 2-3 files per task.
```

---

## 2. How It Works — Mental Model

### For the human developer

You run `palace build .` on your repo. palace-ai reads every file, builds the associative network, writes Room files, and generates the visualizer. You commit `palace-out/` to git. Every teammate, every AI agent, starts with the full map.

### For the AI agent

The agent's workflow becomes:

```
1. Read PALACE.md              (~200 tokens) — see all rooms and the network summary
2. Fire query against network  (~50 tokens)  — identify top-K activated rooms
3. Read relevant Room files    (~400 tokens each, usually 1-3) — full orientation
4. Open specific source links  (only if writing/editing code)
```

Total tokens to orient on a large codebase: ~1,200. Compare to reading raw files: 50,000+.

### For the visualizer

A browser-based force-directed graph. Every file is a node. Edges are drawn only where strength > threshold. Edge color encodes type. Edge opacity and thickness encode strength. You can click any node and watch activation spread through the network — exactly like the associative cascade — to understand what a file's blast radius is before touching it.

---

## 3. Architecture Overview

```
palace-ai/
│
├── BUILD PIPELINE (the indexer)
│   ├── Phase 1: AST Extractor      — tree-sitter, zero LLM, extracts structure
│   ├── Phase 2: Edge Builder       — builds typed edges from AST + git history
│   ├── Phase 3: Room Classifier    — LLM assigns files to rooms, names rooms
│   ├── Phase 4: Room Writer        — LLM writes the Room .md files
│   ├── Phase 5: Network Serialiser — writes network.json
│   └── Phase 6: Visualiser Builder — writes the HTML/JS visualizer
│
├── QUERY ENGINE
│   ├── Activation Spreader        — spreading activation over network.json
│   ├── Room Selector              — picks top-K rooms above threshold
│   └── Context Assembler          — assembles agent context from Room files
│
├── CLI
│   ├── palace build [path]
│   ├── palace query "[concept]"
│   ├── palace serve              — opens visualizer in browser
│   └── palace update [path]      — incremental rebuild on changed files
│
└── OUTPUT (palace-out/)
    ├── PALACE.md                 — the index; agents read this first
    ├── rooms/                    — one .md file per room
    ├── network.json              — the full associative network
    ├── visualizer/index.html     — the repo visualizer
    └── cache/                    — SHA256 hashes for incremental builds
```

---

## 4. Data Structures

### 4.1 Node

Every source file becomes a node. Directories and virtual concepts can also be nodes (type: `dir` or `concept`).

```json
{
  "id": "src/middleware/auth.js",
  "type": "file",
  "room_id": "auth",
  "subtree_id": "ST_MIDDLEWARE",
  "label": "auth middleware",
  "summary": "Validates JWT tokens, attaches req.user, handles refresh on expiry.",
  "symbols": ["verifyToken", "checkPermissions", "refreshIfExpiring", "issueToken"],
  "language": "javascript",
  "size_tokens": 340,
  "activation": 0.0,
  "hash": "sha256:a3f9..."
}
```

**Fields:**
- `id` — relative file path (unique key)
- `type` — `file` | `dir` | `concept` | `test`
- `room_id` — which Room this file belongs to (primary)
- `subtree_id` — finer grouping within the room
- `label` — short human-readable name
- `summary` — 20–50 token description (used in Room files and activation scoring)
- `symbols` — exported functions, classes, constants
- `language` — detected language
- `size_tokens` — approximate token count of the file
- `activation` — runtime field, starts at 0, set during spreading activation
- `hash` — SHA256 of file content, used for incremental builds

### 4.2 Edge

```json
{
  "from": "src/middleware/auth.js",
  "to": "src/routes/api.js",
  "type": "called-by",
  "weight": 0.85,
  "evidence": "verifyToken called at routes/api.js:8",
  "source": "ast"
}
```

**Fields:**
- `from` / `to` — node IDs
- `type` — one of the edge types in Section 15
- `weight` — float 0.0–1.0. Determines edge visibility in visualizer and activation spread strength
- `evidence` — plain-English explanation of why this edge exists (for agent context)
- `source` — `ast` | `llm` | `git` | `inferred` (how the edge was discovered)

### 4.3 Room

```json
{
  "id": "auth",
  "label": "Authentication layer",
  "color": "#534AB7",
  "files": ["src/middleware/auth.js", "src/services/oauth.js", "src/controllers/auth.js"],
  "subtrees": {
    "ST_MIDDLEWARE": ["src/middleware/auth.js"],
    "ST_OAUTH": ["src/services/oauth.js"],
    "ST_CONTROLLER": ["src/controllers/auth.js"]
  },
  "cross_room_refs": [
    {"room": "api-layer", "reason": "req.user consumed by all API routes"},
    {"room": "config", "reason": "JWT_SECRET sourced from config room"}
  ],
  "summary": "Stateless JWT auth with OAuth delegation. All tokens issued through a single signing path.",
  "file": "palace-out/rooms/auth.md",
  "token_count": 380
}
```

### 4.4 PALACE.md Index

The PALACE.md is what an agent reads first. It contains:

1. One-paragraph description of the entire codebase
2. A table of all rooms: `room_id | label | file count | summary`
3. The network summary: most-connected nodes ("god files"), surprising cross-room edges
4. Agent instructions: how to navigate, how to query, edge type glossary

---

## 5. Output File Structure

```
palace-out/
├── PALACE.md                     ← agents read this first (~200 tokens)
├── network.json                  ← full node+edge graph
├── rooms/
│   ├── auth.md                   ← ~380 tokens
│   ├── api-layer.md
│   ├── data-layer.md
│   ├── config.md
│   ├── error-handling.md
│   └── ...
├── visualizer/
│   ├── index.html                ← self-contained, no server needed
│   └── (all JS/CSS inlined)
└── cache/
    ├── manifest.json             ← file hashes for incremental builds
    └── extractions/              ← cached LLM extraction results per file
```

**Commit everything except `cache/manifest.json`** (mtime-based, invalid after git clone).

---

## 6. The Room File Format

This is the core artifact. An agent reads this file and needs zero additional context to understand the entire architectural section it covers.

```markdown
---
room: auth
label: Authentication layer
covers: src/middleware/auth.js · src/services/oauth.js · src/controllers/auth.js
functions: 5
tokens: 380
---

## Overview

The auth layer sits between every inbound HTTP request and the application core.
Requests pass through `verifyToken` first, then `checkPermissions`, before reaching
any route handler. Sessions are stateless (JWT-only). Token refresh is lazy:
`refreshIfExpiring` fires only when a valid token is within 5 min of expiry.
The OAuth flow delegates to passport.js via `initOAuthStrategy` but token issuance
runs through `issueToken` so all tokens share one signing path.

## Functions

### `verifyToken(req, res, next)`
Validates JWT signature and expiry. Attaches decoded payload to `req.user`.
**Called from:** [middleware/index.js:14](src/middleware/index.js#L14) · [routes/api.js:8](src/routes/api.js#L8) · [routes/admin.js:6](src/routes/admin.js#L6)

### `checkPermissions(roles) → middleware`
Returns a middleware that enforces role-based access. Reads `req.user` set by verifyToken.
**Called from:** [routes/admin.js:22](src/routes/admin.js#L22) · [routes/billing.js:11](src/routes/billing.js#L11)

### `issueToken(userId, roles, opts?)`
Signs and returns a JWT. `opts.expiresIn` defaults to `1h`.
**Called from:** [controllers/auth.js:45](src/controllers/auth.js#L45) · [controllers/auth.js:88](src/controllers/auth.js#L88) · [services/oauth.js:61](src/services/oauth.js#L61)

### `refreshIfExpiring(req, res, next)`
Middleware. If token expiry < 5 min, re-issues silently and sets `X-Token-Refreshed` header.
**Called from:** [middleware/index.js:18](src/middleware/index.js#L18)

### `initOAuthStrategy(passport, config)`
Registers Google + GitHub strategies. Callback always delegates to `issueToken`.
**Called from:** [app.js:32](src/app.js#L32)

## Cross-room references

- `verifyToken` result (`req.user`) consumed by → [api-layer room](palace-out/rooms/api-layer.md)
- `checkPermissions` failure path flows to → [error-handling room](palace-out/rooms/error-handling.md)
- Token secret config sourced from → [config room](palace-out/rooms/config.md) (`JWT_SECRET`)

## Strongest incoming edges

| From file | Edge type | Weight |
|---|---|---|
| src/routes/api.js | called-by | 0.95 |
| src/routes/admin.js | called-by | 0.90 |
| src/app.js | imports | 0.85 |
```

**Key design rules for Room files:**
- The overview must explain the *architecture*, not list the files. An agent should be able to write a design doc from this paragraph alone.
- Function headers are exact signatures, not summaries. An agent can grep for these.
- Every "called from" reference includes file + line number so the agent can jump directly.
- Cross-room references use relative links so they work in any viewer.
- The strongest incoming edges table tells an agent what would break if this room changed.

---

## 7. The Associative Network

### network.json schema

```json
{
  "version": "1.0",
  "built_at": "2026-04-30T12:00:00Z",
  "repo": "my-project",
  "stats": {
    "nodes": 84,
    "edges": 312,
    "rooms": 9,
    "languages": ["javascript", "typescript"]
  },
  "nodes": [...],
  "edges": [...],
  "rooms": [...],
  "god_files": [
    {
      "id": "src/app.js",
      "degree": 24,
      "reason": "Entry point. Imports from 18 rooms. Changes here affect everything."
    }
  ],
  "surprising_edges": [
    {
      "from": "src/services/email.js",
      "to": "src/middleware/auth.js",
      "type": "shares-schema",
      "weight": 0.72,
      "reason": "Both use the same User schema — changes to User fields affect both"
    }
  ]
}
```

### Spreading Activation Algorithm

When an agent fires a query `q`:

```python
def activate(query: str, network: Network, threshold: float = 0.15) -> list[Room]:
    # Step 1: Score every node against the query
    # Uses: label match, summary match, symbol name match
    seed_scores = score_nodes_against_query(query, network.nodes)
    
    # Step 2: Initialize activation from seeds
    for node, score in seed_scores.items():
        node.activation = score
    
    # Step 3: Spread activation through edges (3 hops max)
    for hop in range(3):
        for edge in network.edges:
            source_act = edge.from_node.activation
            if source_act < 0.05:
                continue
            spread = source_act * edge.weight * decay(hop)
            edge.to_node.activation = max(edge.to_node.activation, spread)
    
    # Step 4: Group activations by room, take room max
    room_activations = {}
    for node in network.nodes:
        room = node.room_id
        room_activations[room] = max(room_activations.get(room, 0), node.activation)
    
    # Step 5: Return rooms above threshold, sorted by activation
    return sorted(
        [r for r, a in room_activations.items() if a >= threshold],
        key=lambda r: room_activations[r],
        reverse=True
    )

def decay(hop: int) -> float:
    return [1.0, 0.55, 0.25][hop]
```

This gives the agent a ranked list of rooms to open. It reads the top 1–3. It ignores the rest.

---

## 8. The Visualizer

A self-contained `index.html` (no server, no build step needed). Open it in any browser.

### Visual design

- **Nodes** — circles. Size = degree (number of edges). Color = room color.
- **Edges** — drawn only if weight > 0.2 (configurable threshold slider). Color = edge type. Opacity = weight. Thickness = weight.
- **No edges** between unconnected or weakly connected files. The visual is clean by default.

### Color encoding

| Edge type | Color | Meaning |
|---|---|---|
| `imports` | Purple | Direct import/require |
| `calls` | Green | Function call |
| `implements` | Teal | Class extends/implements |
| `configures` | Blue | Provides config to |
| `test-of` | Gray | Test file for source |
| `error-path` | Coral | Handles errors from |
| `co-changes` | Amber | Changed together in git history |
| `shares-schema` | Pink | Same data model |

### Interactions

- **Click a node** → fires spreading activation. Related nodes glow. Unrelated nodes fade. The agent's navigation made visible.
- **Hover a node** → tooltip shows: file path, room, summary, top 3 edges.
- **Hover an edge** → tooltip shows: type, weight, evidence string.
- **Click a room badge** → highlights all files in that room, fades others.
- **Threshold slider** → controls minimum edge weight to display (0.0–1.0). At 1.0 only the strongest bonds show. At 0.0 everything shows.
- **Edge type filter** → checkboxes to show/hide edge types.
- **Search box** → fires activation from a text query, same algorithm as CLI.

### Implementation

Force-directed layout using D3.js `forceSimulation`. Nodes are pinned to room clusters (using `forceX`/`forceY` biases toward room centroids) but have freedom to move within the cluster. This creates a visual grouping by room while still showing cross-room edges clearly.

```javascript
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(edges).id(d => d.id).strength(d => d.weight * 0.3))
  .force("charge", d3.forceManyBody().strength(-120))
  .force("roomX", d3.forceX(d => roomCentroids[d.room_id].x).strength(0.08))
  .force("roomY", d3.forceY(d => roomCentroids[d.room_id].y).strength(0.08))
  .force("collision", d3.forceCollide(d => d.r + 4));
```

The entire visualizer is generated as a single self-contained `index.html` with `network.json` inlined as a JS variable. No server needed. Git-committable. Works offline.

---

## 9. The Indexer — Build Pipeline

### Phase 1: AST Extraction (zero LLM, fast)

For each source file, run tree-sitter to extract:
- Exported symbols (functions, classes, constants)
- Import/require statements → produces `imports` edges
- Function call sites → produces `calls` edges
- Class inheritance → produces `implements` edges
- File size in approximate tokens

Languages supported via tree-sitter: Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Swift, PHP, Lua.

Output: `cache/extractions/{file_hash}.json` per file. Fully deterministic. Re-runs only on changed files.

### Phase 2: Git History Analysis (zero LLM, optional)

For repos with git history, analyze co-change patterns:
- Files that change together in commits → `co-changes` edges
- Weight = co-change frequency / total commits (normalized)
- This surfaces non-obvious couplings that AST cannot detect

```bash
git log --name-only --format='' | ... 
# For every commit, record which files changed together
# Jaccard similarity of change sets → edge weight
```

### Phase 3: LLM Semantic Pass

Run one LLM call per file (batched, parallel) to extract:
- A 20–50 token summary of what the file does
- Semantic `shares-schema` and `inferred` edges the AST cannot see
- Room assignment suggestion (which architectural category this file belongs to)

Prompt template per file:
```
You are analyzing a source file for a memory palace index.

File: {path}
Content: {content}

Return JSON only:
{
  "summary": "20-50 token description of what this file does",
  "room_suggestion": "one of: [auth, api-layer, data-layer, config, error-handling, utils, tests, jobs, ui, other]",
  "semantic_edges": [
    {"to": "other/file/path.js", "type": "shares-schema", "weight": 0.7, "evidence": "..."}
  ]
}
```

Results are cached by file hash. Re-runs only on changed files.

### Phase 4: Room Assignment

After all per-file passes, run one room-level LLM call to:
1. Confirm or adjust room assignments (may override per-file suggestions for consistency)
2. Assign `room_id`, `label`, and `color` to each room
3. Detect subtrees within rooms (tight clusters within a room)

Input: list of all files + their room suggestions + import graph
Output: final room assignment for every file

### Phase 5: Room File Generation

For each room, run one LLM call to write the Room `.md` file.

Prompt:
```
Write a Room file for the memory palace. This room covers the following files:

{for each file: path, summary, exported symbols, call sites}

The Room file must:
1. Open with an architecture overview paragraph (no bullet points)
   - Explain HOW these files work together, not just what each does
   - Name the key functions and their roles in the flow
2. List each function with exact signature and all call sites (file:line)
3. List cross-room references (what this room needs from others, what others need from this)
4. List the 3 strongest incoming edges

Format exactly as shown in the Room file spec. Max 420 tokens total.
```

### Phase 6: Edge Weighting

Combine all edge sources and compute final weights:

```python
def final_weight(edge):
    base = {
        "ast": 1.0,     # direct import/call — certain
        "git": 0.8,     # co-change history — strong signal
        "llm": 0.7,     # semantic inference — confident
        "inferred": 0.5 # weak inference — shown faded
    }[edge.source]
    
    # Modifiers
    if edge.type == "imports":   base *= 1.0   # direct dependency
    if edge.type == "calls":     base *= 0.9   # call = strong coupling
    if edge.type == "co-changes": base *= edge.raw_cochange_score
    if edge.type == "shares-schema": base *= edge.llm_confidence
    
    return min(base, 1.0)
```

Edges with `final_weight < 0.2` are stored in network.json but not drawn in the visualizer by default.

---

## 10. CLI Interface

```bash
# Build the palace for the current directory
palace build .

# Build with options
palace build ./src --rooms auto        # auto-detect rooms (default)
palace build ./src --rooms 6           # force exactly 6 rooms
palace build ./src --no-git            # skip git history analysis
palace build ./src --no-llm            # AST-only, no LLM (fast, less semantic)
palace build ./src --model claude-sonnet-4-20250514  # specify model

# Incremental update (only re-processes changed files)
palace update .

# Query the network from terminal
palace query "rate limiting"           # shows activated rooms + top nodes
palace query "auth flow" --depth 2     # activation spread depth
palace query "what touches the User model"

# Open the visualizer in browser
palace serve
palace serve --port 3000

# Show stats
palace stats

# Install as AI assistant context
palace install claude                  # writes CLAUDE.md + PreToolUse hook
palace install cursor                  # writes .cursor/rules/palace.mdc
palace install opencode                # writes AGENTS.md

# Rebuild just the visualizer (no re-extraction)
palace visualize

# Export formats
palace export --neo4j                  # generates cypher.txt
palace export --graphml                # for Gephi / yEd
palace export --obsidian               # Obsidian vault with room notes
```

---

## 11. Agent Interface

### For Claude Code / any AI coding assistant

After `palace install claude`, every session starts with:

**CLAUDE.md injection:**
```markdown
## palace-ai memory palace

This repo has a memory palace. Before answering any architecture question or 
touching any file, read `palace-out/PALACE.md` to orient yourself.

Navigation:
1. Read `palace-out/PALACE.md` — see all rooms (~200 tokens)
2. Run `palace query "<your question>"` to find relevant rooms
3. Read the relevant room file(s) in `palace-out/rooms/`
4. Only then open source files — and only the specific ones linked in the room file

Never grep through raw source files when the palace exists.
```

**PreToolUse hook** (fires before every Glob/Grep/Read):
```
palace-ai: Memory palace exists. Read palace-out/PALACE.md before searching raw files.
Relevant rooms for your current task can be found with: palace query "<task description>"
```

### palace query output format (agent-readable)

```
Query: "rate limiting"
Activated rooms (above threshold 0.15):

  [0.94] auth          palace-out/rooms/auth.md
         Top nodes: middleware/auth.js (0.94), controllers/auth.js (0.81)

  [0.72] api-layer     palace-out/rooms/api-layer.md  
         Top nodes: routes/index.js (0.72), app.js (0.65)

  [0.31] config        palace-out/rooms/config.md
         Top nodes: config/env.js (0.31)

Suggested: read auth.md and api-layer.md first.
```

---

## 12. Tech Stack

| Component | Technology | Reason |
|---|---|---|
| CLI | Python 3.10+ | Same as graphify, easy install via pip |
| AST extraction | tree-sitter (Python bindings) | 25 languages, deterministic, fast |
| Git analysis | GitPython | Pure Python, no subprocess needed |
| LLM calls | Anthropic SDK (claude-sonnet-4-20250514) | Batched, parallel, cached |
| Network data | NetworkX | Room clustering, shortest paths |
| Visualizer | D3.js v7 (CDN) | Force layout, inlined into HTML |
| Package | PyPI as `palace-ai` | `pip install palace-ai` |
| Caching | SHA256 + JSON files | No database dependency |

**No database. No server. No embeddings. No vector index.**

The network.json is the only persistent state. The visualizer is a static HTML file. The whole palace fits in a git repo alongside the code it indexes.

---

## 13. Repo Structure

```
palace-ai/                          ← the tool repo (what gets published to PyPI)
├── palace/
│   ├── __init__.py
│   ├── cli.py                      ← entry point, argument parsing
│   ├── build/
│   │   ├── __init__.py
│   │   ├── ast_extractor.py        ← tree-sitter AST pass
│   │   ├── git_analyzer.py         ← co-change analysis
│   │   ├── llm_extractor.py        ← LLM semantic pass (batched)
│   │   ├── room_classifier.py      ← room assignment
│   │   ├── room_writer.py          ← Room .md generation
│   │   ├── edge_weighter.py        ← final weight computation
│   │   └── network_serializer.py   ← writes network.json
│   ├── query/
│   │   ├── __init__.py
│   │   ├── activator.py            ← spreading activation algorithm
│   │   └── context_assembler.py    ← assembles agent context string
│   ├── visualizer/
│   │   ├── __init__.py
│   │   ├── builder.py              ← generates index.html
│   │   └── template.html           ← the visualizer template (D3 + inline CSS)
│   ├── install/
│   │   ├── __init__.py
│   │   ├── claude.py
│   │   ├── cursor.py
│   │   └── opencode.py
│   └── utils/
│       ├── cache.py
│       ├── token_counter.py
│       └── language_detect.py
├── tests/
├── worked/                         ← example inputs + outputs (like graphify)
├── docs/
├── pyproject.toml
├── README.md
└── PLAN.md                         ← this file
```

---

## 14. Implementation Phases

### Phase 0 — Scaffold (Day 1)
- [ ] Init Python package with CLI entry point (`palace` command)
- [ ] `palace build` command parses args, walks directory, finds source files
- [ ] Output `palace-out/` directory structure
- [ ] SHA256 cache system (manifest.json)
- [ ] Language detection

### Phase 1 — AST Extraction (Days 2–3)
- [ ] tree-sitter integration for JS/TS/Python (start with these 3)
- [ ] Extract: imports, exports, function definitions, class definitions, call sites
- [ ] Build raw `imports` and `calls` edges from AST data
- [ ] Per-file extraction cached by hash
- [ ] Add remaining languages iteratively

### Phase 2 — LLM Semantic Pass (Days 4–5)
- [ ] Batched LLM calls (parallel, max 10 concurrent)
- [ ] Per-file: summary, room suggestion, semantic edges
- [ ] Results cached by file hash
- [ ] Graceful degradation: if LLM unavailable, AST-only mode

### Phase 3 — Room Assignment (Day 6)
- [ ] Room consolidation LLM call (one call for whole repo)
- [ ] Room assignment written to network.json
- [ ] Room colors auto-assigned (distinct, visually distinguishable)

### Phase 4 — Room File Generation (Day 7)
- [ ] Room .md writer (one LLM call per room)
- [ ] Template enforcement (overview + functions + cross-refs + strongest edges)
- [ ] PALACE.md index generation

### Phase 5 — Visualizer (Days 8–9)
- [ ] D3 force layout with room clustering
- [ ] Node rendering (size by degree, color by room)
- [ ] Edge rendering (color by type, opacity by weight, threshold filter)
- [ ] Click → spreading activation animation
- [ ] Hover tooltips
- [ ] Edge type filter checkboxes
- [ ] Threshold slider
- [ ] Search/query input (fires activation)
- [ ] Self-contained HTML generation (network.json inlined)

### Phase 6 — Query Engine (Day 10)
- [ ] `palace query` CLI command
- [ ] Spreading activation over network.json
- [ ] Agent-readable output format
- [ ] `palace serve` (Python http.server + auto-open browser)

### Phase 7 — Git Integration (Day 11)
- [ ] Co-change analysis via GitPython
- [ ] `co-changes` edges added to network
- [ ] `--no-git` flag for repos without history

### Phase 8 — Install Hooks (Day 12)
- [ ] `palace install claude` — CLAUDE.md + PreToolUse hook
- [ ] `palace install cursor` — .cursor/rules/palace.mdc
- [ ] `palace update` — incremental rebuild
- [ ] `palace stats` — token reduction report

### Phase 9 — Polish + Release (Days 13–14)
- [ ] PyPI packaging (`palace-ai`)
- [ ] README.md with worked example
- [ ] `worked/` directory with a real repo example + token benchmark
- [ ] `palace install` auto-detects platform

---

## 15. Edge Type Taxonomy

These are the typed edge types palace-ai creates. Each type has a defined color in the visualizer and a specific role in the spreading activation.

| Type | Direction | Color | Source | Description |
|---|---|---|---|---|
| `imports` | A → B | Purple | AST | A directly imports/requires B |
| `calls` | A → B | Green | AST | A calls a function exported by B |
| `implements` | A → B | Teal | AST | A extends/implements B |
| `configures` | A → B | Blue | AST+LLM | A provides configuration consumed by B |
| `test-of` | A → B | Gray | AST+naming | A is the test file for B |
| `error-path` | A → B | Coral | LLM | A's error output is handled by B |
| `spawns` | A → B | Amber | AST+LLM | A creates instances of B |
| `shares-schema` | A — B | Pink | LLM | A and B use the same data model |
| `co-changes` | A — B | Amber | Git | A and B change together frequently |
| `inferred` | A — B | Gray (dashed) | LLM | Semantic similarity, lower confidence |

**Activation spread weights by type:**

Strong spreaders (weight multiplier 1.0x): `imports`, `calls`, `implements`
Medium spreaders (0.75x): `co-changes`, `shares-schema`, `configures`
Weak spreaders (0.5x): `error-path`, `spawns`, `test-of`, `inferred`

The logic: if you're touching an auth file and you want to know what else might be affected, direct imports and calls are the strongest signal. Co-change history and shared schemas are meaningful but less certain. Test files and error handlers are relevant but less likely to need simultaneous editing.

---

## 16. Token Budget Analysis

| Operation | Tokens consumed | Tokens agent needs to read |
|---|---|---|
| Raw repo (50 files, ~400 tokens/file) | 20,000 tokens to read everything | 20,000 |
| PALACE.md index only | — | ~200 |
| One Room file | — | ~400 |
| Typical task (2 rooms + 2 source files) | — | ~1,600 |
| **Reduction ratio** | | **~12x for small repos** |
| Large repo (200 files) | 80,000 tokens | ~2,000 |
| **Reduction ratio (large)** | | **~40x** |

Token reduction compounds with repo size because the palace scales sub-linearly — more files doesn't mean proportionally more rooms. A 200-file repo might still have 10–12 rooms.

**Build cost** (one-time, cached): approximately 150 tokens per file for LLM extraction, plus 400 tokens per room for Room file generation. For a 50-file repo: ~8,500 tokens to build the palace. Every subsequent query: ~1,600 tokens. Break-even after the second agent session.

---

## 17. Design Decisions and Tradeoffs

### Why markdown Room files instead of just querying network.json?

An agent reading network.json directly would need to parse JSON, navigate edges, reconstruct context — multiple reasoning steps before understanding anything. The Room .md file is pre-computed human-readable orientation. The agent reads one file and knows everything it needs to know about a section. JSON is for the machine (spreading activation); .md is for the agent (orientation).

### Why typed edges instead of just weights?

A weight of 0.8 tells you the connection is strong. A type of `co-changes` tells you *why* it's strong — not because these files import each other, but because they always change together in git history. That's completely different information. The agent can reason about it: "these files don't call each other but they always change together — there's probably a shared data contract I need to be careful about." Semantic edges without types are just similarity scores. Typed edges are knowledge.

### Why not use embeddings/vector search?

Vector search gives you "files semantically similar to this query." Spreading activation gives you "files that would be affected by, or relevant to, this concept, following the actual dependency and relationship structure of the codebase." For code navigation, the second is dramatically more useful. You don't want the 5 files most similar to "rate limiting" — you want the 5 files you'd need to touch to *implement* rate limiting, which means following the call graph, the config relationships, the shared schemas.

### Why is the visualizer self-contained HTML?

No server to run. Works on CI. Works offline. Opens on double-click. Can be committed to git and viewed on GitHub Pages. The entire tool produces artifacts you can use anywhere without running anything.

### Why rooms instead of just the raw network?

An agent given a 300-node network graph and told to find the relevant files for a task will take 10+ reasoning steps and still make mistakes. An agent given a 10-item room list, a 2-sentence room summary per item, and a spreading activation result that says "open auth.md and api-layer.md" will complete the orientation in 3 steps with high accuracy. The rooms are the compression that makes the network usable.

### Relationship to graphify

graphify builds a knowledge graph optimized for *understanding what a codebase contains* — concepts, relationships, architectural decisions, design rationale. palace-ai builds a navigation index optimized for *agent task execution* — which files do I touch, in what order, given that I know nothing about this codebase. They are complementary. graphify answers "what is this codebase about." palace-ai answers "where do I go to do X."

---

## Quick Start (for the implementing agent)

```bash
# 1. Scaffold
mkdir palace-ai && cd palace-ai
git init
# Create the package structure from Section 13

# 2. Start with cli.py + build/ast_extractor.py
# Get `palace build .` working with AST-only output first
# Verify it produces palace-out/network.json with import edges

# 3. Add LLM extraction
# Add build/llm_extractor.py
# Verify it adds summaries and semantic edges to network.json

# 4. Add Room files
# Add build/room_writer.py
# Verify palace-out/rooms/*.md are generated correctly

# 5. Add visualizer
# Add visualizer/builder.py + template.html
# Verify palace serve opens a working D3 graph

# 6. Run on a real repo to benchmark
# Use the graphify repo itself or a small Express.js app
# Record token counts, compare to reading raw files

# 7. Package and publish
# pyproject.toml, README.md, worked/ example
# pip install palace-ai should work
```

---

*palace-ai — built for agents, by the architecture of human memory.*
