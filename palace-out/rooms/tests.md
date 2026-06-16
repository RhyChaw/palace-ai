---
room: tests
label: Tests
covers: tests/fixture/js_a.js · tests/fixture/js_b.js · tests/fixture/py_a.py · tests/fixture/py_b.py · tests/test_memory.py
functions: 7
tokens: 229
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `run()`
Defined in this room.
**Called from:** [palace/memory/learn.py:26](palace/memory/learn.py#L26) · [palace/memory/learn.py:33](palace/memory/learn.py#L33) · [palace/memory/llm.py:59](palace/memory/llm.py#L59) · [tests/test_memory.py:101](tests/test_memory.py#L101) · [tests/test_memory.py:112](tests/test_memory.py#L112)

### `greet(name)`
Defined in this room.
**Called from:** [tests/fixture/js_a.js:4](tests/fixture/js_a.js#L4)

### `add(a: int, b: int)`
Defined in this room.
**Called from:** [tests/fixture/py_a.py:5](tests/fixture/py_a.py#L5)

### `main()`
Defined in this room.
**Called from:** [palace/cli.py:247](palace/cli.py#L247)

### `test_learn_appends_attempt_and_pattern(tmp_path: Path)`
Defined in this room.
**Called from:** (none detected)

### `test_standalone_memory_without_palace_build(tmp_path: Path)`
Defined in this room.
**Called from:** (none detected)

### `test_mem_cli_reflect_and_recall(tmp_path: Path)`
Defined in this room.
**Called from:** (none detected)

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| tests/fixture/js_a.js | imports | 0.76 |
| tests/fixture/py_a.py | calls | 0.66 |
| tests/fixture/js_a.js | calls | 0.64 |
