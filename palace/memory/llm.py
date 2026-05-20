from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from anthropic import AsyncAnthropic

from palace.build.llm_extractor import _parse_json_object

DEFAULT_MEMORY_MODEL = "claude-haiku-4-5-20251001"


def _memory_model(model: str | None) -> str:
    return (model or os.environ.get("PALACE_MEMORY_MODEL") or DEFAULT_MEMORY_MODEL).strip()


async def _call_json_prompt(*, prompt: str, model: str | None, max_tokens: int = 1200) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = AsyncAnthropic(api_key=api_key)
    m = _memory_model(model)
    delay = 2.0
    last: Exception | None = None
    for _ in range(10):
        try:
            msg = await client.messages.create(
                model=m,
                max_tokens=max_tokens,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except Exception as e:
            last = e
            msg_text = str(e).lower()
            if "rate_limit" in msg_text or "429" in msg_text or "overloaded" in msg_text:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise
    else:
        raise last  # type: ignore[misc]

    out = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            out += block.text
        else:
            out += str(block)
    return _parse_json_object(out)


def call_json_prompt(*, prompt: str, model: str | None = None, max_tokens: int = 1200) -> dict[str, Any]:
    return asyncio.run(_call_json_prompt(prompt=prompt, model=model, max_tokens=max_tokens))


def extract_pattern_from_attempt(
    *,
    task: str,
    files_modified: list[str],
    notes: str,
    approach: str,
    model: str | None = None,
) -> dict[str, Any]:
    prompt = f"""Given this successful agent attempt on a codebase:
Task: {task}
Approach: {approach or "(not specified)"}
Files modified: {", ".join(files_modified) or "(none listed)"}
Agent notes: {notes or "(none)"}

Extract a reusable pattern. Return JSON only:
{{
  "id": "snake_case_id",
  "name": "Human-readable pattern name",
  "domain": "short domain like auth or api",
  "rooms_involved": ["room_id", "..."],
  "description": "What approach worked",
  "implementation_sequence": ["step 1", "step 2"],
  "codebase_specific_notes": "What is unique to this project",
  "anti_patterns": ["what to avoid"]
}}
"""
    return call_json_prompt(prompt=prompt, model=model)


def extract_failure_from_attempt(
    *,
    task: str,
    approach: str,
    failure_reason: str,
    notes: str,
    files_modified: list[str],
    model: str | None = None,
) -> dict[str, Any]:
    prompt = f"""Given this failed agent attempt on a codebase:
Task: {task}
Approach attempted: {approach or "(not specified)"}
Failure reason: {failure_reason or notes or "(unknown)"}
Files touched: {", ".join(files_modified) or "(none)"}
Agent notes: {notes or "(none)"}

Extract a failure mode others should avoid. Return JSON only:
{{
  "task_type": "short category",
  "approach_attempted": "what was tried",
  "failure_reason": "why it failed",
  "rooms_involved": ["room_id", "..."],
  "resolution": "what to do instead, if known"
}}
"""
    return call_json_prompt(prompt=prompt, model=model)


def analyze_state_from_attempts(
    *,
    attempts_summary: str,
    model: str | None = None,
) -> dict[str, Any]:
    prompt = f"""Given these agent attempts on a codebase:
{attempts_summary}

Identify the current "game state" of the codebase. Return JSON only:
{{
  "completed_domains": ["domain names clearly done"],
  "incomplete_domains": [
    {{
      "domain": "name",
      "what_exists": "what is implemented",
      "what_is_missing": "gaps",
      "likely_location": "file paths"
    }}
  ],
  "known_tech_debt": ["items"],
  "architectural_decisions": ["how this project is structured"],
  "team_conventions": ["patterns that repeat"]
}}
"""
    return call_json_prompt(prompt=prompt, model=model, max_tokens=2000)


def reflect_patterns_from_attempts(
    *,
    attempts_summary: str,
    model: str | None = None,
) -> list[dict[str, Any]]:
    prompt = f"""Given these agent attempts on a codebase:
{attempts_summary}

Find cross-cutting patterns (generalizations across multiple attempts). Return JSON only:
{{
  "patterns": [
    {{
      "id": "snake_case_id",
      "name": "name",
      "domain": "domain",
      "rooms_involved": [],
      "description": "pattern",
      "implementation_sequence": [],
      "codebase_specific_notes": "",
      "anti_patterns": []
    }}
  ]
}}
"""
    obj = call_json_prompt(prompt=prompt, model=model, max_tokens=2500)
    patterns = obj.get("patterns")
    return patterns if isinstance(patterns, list) else []


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug_id(text: str) -> str:
    s = _SLUG_RE.sub("_", text.lower().strip())[:48].strip("_")
    return s or "pattern"
