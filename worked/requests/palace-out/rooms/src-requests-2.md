---
room: src-requests-2
label: Src Requests
covers: src/requests/_internal_utils.py · src/requests/api.py · src/requests/auth.py · src/requests/hooks.py · src/requests/models.py · src/requests/sessions.py
functions: 10
tokens: 656
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `get(url, params=None, **kwargs)`
Defined in this room.
**Called from:** [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:134](src/requests/auth.py#L134) · …

### `get(self, url, **kwargs)`
Defined in this room.
**Called from:** [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:134](src/requests/auth.py#L134) · …

### `send(self, request, **kwargs)`
Defined in this room.
**Called from:** [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/sessions.py:265](src/requests/sessions.py#L265) · [src/requests/sessions.py:265](src/requests/sessions.py#L265) · …

### `__init__(self, username, password)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self, username, password)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(
        self,
        method=None,
        url=None,
        headers=None,
        files=None,
        data=None,
        params=None,
        auth=None,
        cookies=None,
        hooks=None,
        json=None,
    )`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `Request`
Defined in this room.
**Called from:** [src/requests/sessions.py:565](src/requests/sessions.py#L565) · [tests/test_adapters.py:7](tests/test_adapters.py#L7) · [tests/test_requests.py:116](tests/test_requests.py#L116) · [tests/test_requests.py:126](tests/test_requests.py#L126) · [tests/test_requests.py:131](tests/test_requests.py#L131) · …

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| src/requests/adapters.py | calls | 0.90 |
| src/requests/adapters.py | calls | 0.90 |
| src/requests/adapters.py | calls | 0.90 |
