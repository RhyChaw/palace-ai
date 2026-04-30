from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic


DEFAULT_MODEL = "claude-sonnet-4-20250514"


@dataclass(frozen=True)
class LlmExtraction:
    summary: str
    room_suggestion: str
    semantic_edges: list[dict[str, Any]]

    def to_json(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "room_suggestion": self.room_suggestion,
            "semantic_edges": self.semantic_edges,
        }


_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    m = _JSON_OBJ_RE.search(text)
    if not m:
        raise ValueError("No JSON object found in model output")
    return json.loads(m.group(0))


async def _extract_one(
    client: AsyncAnthropic,
    *,
    model: str,
    path: str,
    content: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, dict[str, Any]]:
    prompt = f"""You are analyzing a source file for a memory palace index.

File: {path}
Content:
{content}

Return JSON only:
{{
  "summary": "20-50 token description of what this file does",
  "room_suggestion": "one of: [auth, api-layer, data-layer, config, error-handling, utils, tests, jobs, ui, other]",
  "semantic_edges": [
    {{"to": "other/file/path.js", "type": "shares-schema", "weight": 0.7, "evidence": "..."}}
  ]
}}
"""
    async with semaphore:
        msg = await client.messages.create(
            model=model,
            max_tokens=600,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )

    # anthropic message content can be list of blocks
    out = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            out += block.text
        else:
            out += str(block)

    obj = _parse_json_object(out)
    return path, obj


async def extract_semantics_parallel(
    *,
    files: list[tuple[str, str]],
    model: str | None = None,
    max_concurrency: int = 10,
) -> dict[str, dict[str, Any]]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = AsyncAnthropic(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrency)
    m = model or DEFAULT_MODEL

    tasks = [
        _extract_one(client, model=m, path=path, content=content, semaphore=semaphore) for path, content in files
    ]
    results = await asyncio.gather(*tasks)
    return {path: obj for path, obj in results}


def extract_semantics(
    *,
    files: list[tuple[str, str]],
    model: str | None = None,
    max_concurrency: int = 10,
) -> dict[str, dict[str, Any]]:
    return asyncio.run(extract_semantics_parallel(files=files, model=model, max_concurrency=max_concurrency))

