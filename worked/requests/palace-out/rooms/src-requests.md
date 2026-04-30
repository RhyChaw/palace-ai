---
room: src-requests
label: Src Requests
covers: src/requests/adapters.py · src/requests/cookies.py · src/requests/exceptions.py · src/requests/help.py · src/requests/status_codes.py · src/requests/structures.py · src/requests/utils.py
functions: 10
tokens: 684
---

## Overview

This room groups a set of files that are structurally connected (imports/calls). In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and call-site links below to navigate directly.

## Functions

### `get(self, name, default=None, domain=None, path=None)`
Defined in this room.
**Called from:** [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:134](src/requests/auth.py#L134) · …

### `get(self, key, default=None)`
Defined in this room.
**Called from:** [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:133](src/requests/auth.py#L133) · [src/requests/auth.py:134](src/requests/auth.py#L134) · …

### `send(
        self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    )`
Defined in this room.
**Called from:** [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/sessions.py:265](src/requests/sessions.py#L265) · [src/requests/sessions.py:265](src/requests/sessions.py#L265) · …

### `send(
        self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    )`
Defined in this room.
**Called from:** [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/auth.py:276](src/requests/auth.py#L276) · [src/requests/sessions.py:265](src/requests/sessions.py#L265) · [src/requests/sessions.py:265](src/requests/sessions.py#L265) · …

### `__init__(self)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(
        self,
        pool_connections=DEFAULT_POOLSIZE,
        pool_maxsize=DEFAULT_POOLSIZE,
        max_retries=DEFAULT_RETRIES,
        pool_block=DEFAULT_POOLBLOCK,
    )`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self, request)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self, headers)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self, *args, **kwargs)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

### `__init__(self, *args, **kwargs)`
Defined in this room.
**Called from:** [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · [src/requests/adapters.py:118](src/requests/adapters.py#L118) · …

## Cross-room references

- (none in AST-only mode)

## Strongest incoming edges


| From file | Edge type | Weight |
|---|---|---|
| src/requests/adapters.py | calls | 0.90 |
| src/requests/adapters.py | calls | 0.90 |
| src/requests/adapters.py | calls | 0.90 |
