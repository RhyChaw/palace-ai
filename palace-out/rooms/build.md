---
room: build
label: Build & CLI
covers: palace/__init__.py · palace/cli.py · palace/evals/__init__.py · palace/install/__init__.py · palace/install/claude.py · palace/memory/__init__.py · palace/memory/add.py · palace/memory/decay.py · palace/memory/init.py · palace/memory/learn.py · … (+14 more)
functions: 10
tokens: 722
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `load_patterns(mp: MemoryPaths)`
Defined in this room.
**Called from:** [palace/memory/learn.py:75](palace/memory/learn.py#L75) · [palace/memory/palace_md.py:111](palace/memory/palace_md.py#L111) · [palace/memory/query_context.py:27](palace/memory/query_context.py#L27) · [palace/memory/recall.py:75](palace/memory/recall.py#L75) · [palace/memory/reflect.py:70](palace/memory/reflect.py#L70) · …

### `ensure_memory(mp: MemoryPaths)`
Defined in this room.
**Called from:** [palace/memory/add.py:39](palace/memory/add.py#L39) · [palace/memory/learn.py:226](palace/memory/learn.py#L226) · [palace/memory/recall.py:69](palace/memory/recall.py#L69) · [palace/memory/reflect.py:62](palace/memory/reflect.py#L62) · [palace/memory/snapshot.py:22](palace/memory/snapshot.py#L22) · …

### `load_state(mp: MemoryPaths)`
Defined in this room.
**Called from:** [palace/memory/learn.py:159](palace/memory/learn.py#L159) · [palace/memory/palace_md.py:114](palace/memory/palace_md.py#L114) · [palace/memory/query_context.py:29](palace/memory/query_context.py#L29) · [palace/memory/recall.py:77](palace/memory/recall.py#L77) · [palace/memory/reflect.py:108](palace/memory/reflect.py#L108) · …

### `resolve_memory_paths(*, repo_path: Path | None = None, root: Path | None = None)`
Defined in this room.
**Called from:** [palace/memory/add.py:134](palace/memory/add.py#L134) · [palace/memory/learn.py:219](palace/memory/learn.py#L219) · [palace/memory/mem_cli.py:24](palace/memory/mem_cli.py#L24) · [palace/memory/mem_cli.py:37](palace/memory/mem_cli.py#L37) · [palace/memory/mem_cli.py:56](palace/memory/mem_cli.py#L56) · …

### `load_attempts(mp: MemoryPaths)`
Defined in this room.
**Called from:** [palace/memory/palace_md.py:105](palace/memory/palace_md.py#L105) · [palace/memory/recall.py:74](palace/memory/recall.py#L74) · [palace/memory/reflect.py:63](palace/memory/reflect.py#L63) · [palace/memory/reflect.py:192](palace/memory/reflect.py#L192) · [palace/memory/snapshot.py:41](palace/memory/snapshot.py#L41) · …

### `memory_paths(palace_out: Path)`
Defined in this room.
**Called from:** [palace/memory/learn.py:224](palace/memory/learn.py#L224) · [palace/memory/palace_md.py:103](palace/memory/palace_md.py#L103) · [palace/memory/query_context.py:23](palace/memory/query_context.py#L23) · [palace/memory/reflect.py:173](palace/memory/reflect.py#L173) · [palace/memory/snapshot.py:20](palace/memory/snapshot.py#L20) · …

### `utc_now_iso()`
Defined in this room.
**Called from:** [palace/memory/add.py:40](palace/memory/add.py#L40) · [palace/memory/decay.py:26](palace/memory/decay.py#L26) · [palace/memory/learn.py:242](palace/memory/learn.py#L242) · [palace/memory/palace_md.py:116](palace/memory/palace_md.py#L116) · [palace/memory/reflect.py:64](palace/memory/reflect.py#L64) · …

### `memory_exists(mp: MemoryPaths)`
Defined in this room.
**Called from:** [palace/memory/palace_md.py:105](palace/memory/palace_md.py#L105) · [palace/memory/palace_md.py:110](palace/memory/palace_md.py#L110) · [palace/memory/palace_md.py:126](palace/memory/palace_md.py#L126) · [palace/memory/query_context.py:24](palace/memory/query_context.py#L24) · [palace/memory/status.py:43](palace/memory/status.py#L43) · …

### `load_failures(mp: MemoryPaths)`
Defined in this room.
**Called from:** [palace/memory/learn.py:101](palace/memory/learn.py#L101) · [palace/memory/palace_md.py:113](palace/memory/palace_md.py#L113) · [palace/memory/query_context.py:28](palace/memory/query_context.py#L28) · [palace/memory/recall.py:76](palace/memory/recall.py#L76) · [palace/memory/snapshot.py:39](palace/memory/snapshot.py#L39) · …

### `write_json(path: Path, obj: Any)`
Defined in this room.
**Called from:** [palace/memory/init.py:19](palace/memory/init.py#L19) · [palace/memory/init.py:21](palace/memory/init.py#L21) · [palace/memory/init.py:23](palace/memory/init.py#L23) · [palace/memory/init.py:43](palace/memory/init.py#L43) · [palace/memory/init.py:47](palace/memory/init.py#L47) · …

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| palace/visualizer/serve.py | imports | 0.76 |
| palace/query/stats.py | imports | 0.75 |
| palace/visualizer/builder.py | imports | 0.74 |

## Also in this room

- `palace/visualizer/builder.py`
- `palace/memory/status.py`
- `palace/memory/decay.py`
- `palace/install/claude.py`
- `palace/memory/snapshot.py`
- `palace/query/stats.py`
- `palace/visualizer/serve.py`
- `palace/cli.py`
- `palace/__init__.py`
- `palace/evals/__init__.py`
- `palace/install/__init__.py`
- `palace/memory/__init__.py`
- `palace/query/__init__.py`
- `palace/visualizer/__init__.py`
