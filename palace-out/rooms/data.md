---
room: data
label: Data Layer
covers: palace/memory/mem_cli.py · palace/memory/paths.py · palace/memory/query_context.py · palace/memory/recall.py · palace/query/activator.py
functions: 10
tokens: 557
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `_relevance_score(query: str, text: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:42](palace/memory/query_context.py#L42) · [palace/memory/query_context.py:57](palace/memory/query_context.py#L57) · [palace/memory/query_context.py:89](palace/memory/query_context.py#L89) · [palace/memory/query_context.py:96](palace/memory/query_context.py#L96) · [palace/memory/query_context.py:100](palace/memory/query_context.py#L100) · …

### `_relevance_score(query: str, text: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:42](palace/memory/query_context.py#L42) · [palace/memory/query_context.py:57](palace/memory/query_context.py#L57) · [palace/memory/query_context.py:89](palace/memory/query_context.py#L89) · [palace/memory/query_context.py:96](palace/memory/query_context.py#L96) · [palace/memory/query_context.py:100](palace/memory/query_context.py#L100) · …

### `resolve_memory_paths(*, repo_path: Path | None = None, root: Path | None = None)`
Defined in this room.
**Called from:** [palace/memory/add.py:134](palace/memory/add.py#L134) · [palace/memory/learn.py:219](palace/memory/learn.py#L219) · [palace/memory/mem_cli.py:24](palace/memory/mem_cli.py#L24) · [palace/memory/mem_cli.py:37](palace/memory/mem_cli.py#L37) · [palace/memory/mem_cli.py:56](palace/memory/mem_cli.py#L56) · …

### `memory_paths(palace_out: Path)`
Defined in this room.
**Called from:** [palace/memory/learn.py:224](palace/memory/learn.py#L224) · [palace/memory/palace_md.py:103](palace/memory/palace_md.py#L103) · [palace/memory/query_context.py:23](palace/memory/query_context.py#L23) · [palace/memory/reflect.py:173](palace/memory/reflect.py#L173) · [palace/memory/snapshot.py:20](palace/memory/snapshot.py#L20) · …

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/recall.py:14](palace/memory/recall.py#L14) · [palace/memory/recall.py:14](palace/memory/recall.py#L14) · [palace/query/activator.py:40](palace/query/activator.py#L40) · …

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/recall.py:14](palace/memory/recall.py#L14) · [palace/memory/recall.py:14](palace/memory/recall.py#L14) · [palace/query/activator.py:40](palace/query/activator.py#L40) · …

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/recall.py:14](palace/memory/recall.py#L14) · [palace/memory/recall.py:14](palace/memory/recall.py#L14) · [palace/query/activator.py:40](palace/query/activator.py#L40) · …

### `memory_paths_at_root(root: Path)`
Defined in this room.
**Called from:** [tests/test_memory.py:49](tests/test_memory.py#L49) · [tests/test_memory.py:78](tests/test_memory.py#L78)

### `recall_memory(`
Defined in this room.
**Called from:** [palace/memory/mem_cli.py:25](palace/memory/mem_cli.py#L25) · [tests/test_memory.py:70](tests/test_memory.py#L70)

### `format_memory_context(repo_path: Path, query: str, *, max_patterns: int = 3, max_failures: int = 2)`
Defined in this room.
**Called from:** [palace/query/activator.py:140](palace/query/activator.py#L140)

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| palace/query/activator.py | imports | 0.69 |
| palace/memory/__init__.py | imports | 0.64 |
| palace/memory/__init__.py | imports | 0.63 |
