from __future__ import annotations

import re


_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\\d+|\\S", re.MULTILINE)


def approx_token_count(text: str) -> int:
    """
    Rough token estimate without external tokenizers.
    Stable across runs; good enough for relative ratios.
    """
    return len(_TOKEN_RE.findall(text))

