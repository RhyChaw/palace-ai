---
room: palace-visualizer
label: Palace Visualizer
covers: palace/cli.py · palace/install/claude.py · palace/utils/cache.py · palace/visualizer/builder.py · palace/visualizer/serve.py · worked/repos/requests/src/requests/help.py
functions: 10
tokens: 392
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `info()`
Defined in this room.
**Called from:** [worked/repos/requests/src/requests/help.py:127](worked/repos/requests/src/requests/help.py#L127) · [worked/repos/requests/tests/test_help.py:8](worked/repos/requests/tests/test_help.py#L8) · [worked/repos/requests/tests/test_help.py:8](worked/repos/requests/tests/test_help.py#L8) · [worked/repos/requests/tests/test_help.py:21](worked/repos/requests/tests/test_help.py#L21) · [worked/repos/requests/tests/test_help.py:21](worked/repos/requests/tests/test_help.py#L21) · …

### `main(argv: list[str] | None = None)`
Defined in this room.
**Called from:** [palace/cli.py:91](palace/cli.py#L91) · [palace/cli.py:91](palace/cli.py#L91) · [worked/repos/requests/src/requests/help.py:131](worked/repos/requests/src/requests/help.py#L131) · [worked/repos/requests/src/requests/help.py:131](worked/repos/requests/src/requests/help.py#L131)

### `main()`
Defined in this room.
**Called from:** [palace/cli.py:91](palace/cli.py#L91) · [palace/cli.py:91](palace/cli.py#L91) · [worked/repos/requests/src/requests/help.py:131](worked/repos/requests/src/requests/help.py#L131) · [worked/repos/requests/src/requests/help.py:131](worked/repos/requests/src/requests/help.py#L131)

### `build_visualizer(repo_path: Path)`
Defined in this room.
**Called from:** [palace/cli.py:64](palace/cli.py#L64) · [palace/visualizer/serve.py:15](palace/visualizer/serve.py#L15)

### `install_claude(repo_path: Path)`
Defined in this room.
**Called from:** [palace/cli.py:84](palace/cli.py#L84)

### `ensure_output_dirs(palace_out: Path)`
Defined in this room.
**Called from:** [palace/visualizer/builder.py:12](palace/visualizer/builder.py#L12)

### `serve_visualizer(repo_path: Path, *, port: int = 8765)`
Defined in this room.
**Called from:** [palace/cli.py:74](palace/cli.py#L74)

### `sha256_bytes(data: bytes)`
Defined in this room.
**Called from:** (none detected)

### `sha256_text(text: str)`
Defined in this room.
**Called from:** (none detected)

### `CachePaths`
Defined in this room.
**Called from:** (none detected)

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| palace/cli.py | imports | 1.00 |
| palace/cli.py | imports | 1.00 |
| palace/cli.py | imports | 1.00 |
