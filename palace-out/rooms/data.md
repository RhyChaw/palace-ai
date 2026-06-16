---
room: data
label: Data Layer
covers: palace/evals/__main__.py · palace/evals/harness.py · palace/memory/mem_cli.py · palace/memory/query_context.py · palace/memory/recall.py · palace/query/activator.py
functions: 10
tokens: 544
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · …

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · …

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · …

### `_tokenize(q: str)`
Defined in this room.
**Called from:** [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/evals/harness.py:71](palace/evals/harness.py#L71) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · [palace/memory/query_context.py:14](palace/memory/query_context.py#L14) · …

### `_relevance_score(query: str, text: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:42](palace/memory/query_context.py#L42) · [palace/memory/query_context.py:57](palace/memory/query_context.py#L57) · [palace/memory/query_context.py:89](palace/memory/query_context.py#L89) · [palace/memory/query_context.py:96](palace/memory/query_context.py#L96) · [palace/memory/query_context.py:100](palace/memory/query_context.py#L100) · …

### `_relevance_score(query: str, text: str)`
Defined in this room.
**Called from:** [palace/memory/query_context.py:42](palace/memory/query_context.py#L42) · [palace/memory/query_context.py:57](palace/memory/query_context.py#L57) · [palace/memory/query_context.py:89](palace/memory/query_context.py#L89) · [palace/memory/query_context.py:96](palace/memory/query_context.py#L96) · [palace/memory/query_context.py:100](palace/memory/query_context.py#L100) · …

### `main(argv: list[str] | None = None)`
Defined in this room.
**Called from:** [palace/cli.py:261](palace/cli.py#L261) · [palace/cli.py:261](palace/cli.py#L261) · [palace/evals/__main__.py:96](palace/evals/__main__.py#L96) · [palace/evals/__main__.py:96](palace/evals/__main__.py#L96)

### `recall_memory(`
Defined in this room.
**Called from:** [palace/memory/mem_cli.py:25](palace/memory/mem_cli.py#L25) · [tests/test_memory.py:70](tests/test_memory.py#L70)

### `run_eval(`
Defined in this room.
**Called from:** [palace/evals/__main__.py:47](palace/evals/__main__.py#L47) · [tests/test_evals.py:58](tests/test_evals.py#L58)

### `format_memory_context(repo_path: Path, query: str, *, max_patterns: int = 3, max_failures: int = 2)`
Defined in this room.
**Called from:** [palace/query/activator.py:140](palace/query/activator.py#L140)

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| tests/test_evals.py | imports | 0.73 |
| palace/evals/__main__.py | imports | 0.71 |
| palace/query/activator.py | imports | 0.67 |
