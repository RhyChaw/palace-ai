from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic


DEFAULT_MODEL = "claude-sonnet-4-6"


def _env_model() -> str | None:
    m = (os.environ.get("PALACE_MODEL") or "").strip()
    return m or None


def _env_concurrency(default: int) -> int:
    raw = (os.environ.get("PALACE_LLM_CONCURRENCY") or "").strip()
    if not raw:
        return default
    try:
        v = int(raw)
    except ValueError:
        return default
    return max(1, min(25, v))


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
    # Keep prompts bounded; huge files can blow rate limits and latency.
    # (We only need a coarse summary + a few semantic edges.)
    if len(content) > 20_000:
        content = content[:20_000] + "\n\n…(truncated)\n"

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
        delay = 2.0
        last: Exception | None = None
        for _attempt in range(1, 11):
            try:
                msg = await client.messages.create(
                    model=model,
                    max_tokens=600,
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
    max_concurrency = _env_concurrency(max_concurrency)
    semaphore = asyncio.Semaphore(max_concurrency)
    m = model or _env_model() or DEFAULT_MODEL

    tasks = [
        _extract_one(client, model=m, path=path, content=content, semaphore=semaphore) for path, content in files
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out: dict[str, dict[str, Any]] = {}
    for r in results:
        if isinstance(r, Exception):
            continue
        path, obj = r
        out[path] = obj
    return out


def extract_semantics(
    *,
    files: list[tuple[str, str]],
    model: str | None = None,
    max_concurrency: int = 10,
) -> dict[str, dict[str, Any]]:
    return asyncio.run(extract_semantics_parallel(files=files, model=model, max_concurrency=max_concurrency))

