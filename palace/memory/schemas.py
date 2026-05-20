from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def empty_patterns() -> dict[str, Any]:
    return {"patterns": []}


def empty_failures() -> dict[str, Any]:
    return {"failures": []}


def empty_state() -> dict[str, Any]:
    return {
        "last_updated": None,
        "completed_domains": [],
        "incomplete_domains": [],
        "known_tech_debt": [],
        "architectural_decisions": [],
        "team_conventions": [],
    }


VALID_OUTCOMES = frozenset({"success", "failure", "partial", "abandoned"})
