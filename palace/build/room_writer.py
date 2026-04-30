from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic

from palace.utils.token_counter import approx_token_count


DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _md_link(file_id: str, line: int) -> str:
    return f"[{file_id}:{line}]({file_id}#L{line})"


def _read_ast_exports(palace_out: Path, file_hash: str) -> list[dict[str, Any]]:
    cache_path = palace_out / "cache" / "extractions" / f"{file_hash.replace(':', '_')}.json"
    if not cache_path.exists():
        return []
    try:
        obj = json.loads(cache_path.read_text("utf-8"))
    except Exception:
        return []
    ast = obj.get("ast") or {}
    exports = ast.get("exports") or []
    if not isinstance(exports, list):
        return []
    return [e for e in exports if isinstance(e, dict) and e.get("signature")]


async def _write_room_llm(
    *,
    model: str,
    room_id: str,
    room_label: str,
    covers: list[str],
    files_payload: list[dict[str, Any]],
    incoming_edges: list[dict[str, Any]],
) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    client = AsyncAnthropic(api_key=api_key)

    prompt = f"""Write a Room file for the memory palace. This room covers the following files:

{", ".join(covers)}

For each file you have: path, summary, exported symbols (exact signatures), and call sites (file:line).

Room file must follow this exact markdown format contract:
---
room: {room_id}
label: {room_label}
covers: <file list separated by " · ">
functions: <count>
tokens: <count>
---

## Overview

<single architecture paragraph; no bullet points; explain how the pieces work together>

## Functions

### `<signature>`
<1-2 sentence description>
**Called from:** [file:line](path#Lline) · ...

## Cross-room references

- <bullet lines with relative links to other room files if relevant>

## Strongest incoming edges

| From file | Edge type | Weight |
|---|---|---|
| ... | ... | 0.90 |

Constraints:
- Overview must explain architecture and flow; do not list files.
- Function headers are exact signatures.
- Called-from entries MUST include file:line links.
- Max 420 tokens total.

Here is the structured input:
files:
{json.dumps(files_payload)}

incoming_edges:
{json.dumps(incoming_edges)}
"""

    msg = await client.messages.create(
        model=model,
        max_tokens=1300,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    out = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            out += block.text
        else:
            out += str(block)
    return out.strip() + "\n"


def _room_md_fallback(
    *,
    room_id: str,
    room_label: str,
    covers: list[str],
    functions: list[dict[str, Any]],
    incoming_edges: list[dict[str, Any]],
) -> str:
    # Deterministic, AST-only fallback that still respects the contract.
    if len(covers) <= 12:
        cover_str = " · ".join(covers)
    else:
        cover_str = " · ".join(covers[:10]) + f" · … (+{len(covers) - 10} more)"

    # Keep room files small: include the most-referenced functions first.
    # (The full detail remains in network.json + source.)
    def _fn_rank(fn: dict[str, Any]) -> int:
        return len(fn.get("called_from") or [])

    functions = sorted(functions, key=_fn_rank, reverse=True)
    fn_cap = 10
    functions = functions[:fn_cap]
    fn_count = len(functions)

    overview = (
        "This room groups a set of files that are structurally connected (imports/calls). "
        "In AST-only mode, summaries are brief and semantic edges may be missing; use the function list and "
        "call-site links below to navigate directly."
    )

    lines = []
    lines.append("---")
    lines.append(f"room: {room_id}")
    lines.append(f"label: {room_label}")
    lines.append(f"covers: {cover_str}")
    lines.append(f"functions: {fn_count}")
    lines.append("tokens: 0")
    lines.append("---\n")
    lines.append("## Overview\n")
    lines.append(overview + "\n")
    lines.append("## Functions\n")
    for fn in functions:
        sig = fn["signature"]
        lines.append(f"### `{sig}`")
        desc = fn.get("desc") or "Defined in this room."
        lines.append(desc)
        called = fn.get("called_from") or []
        if called:
            called = called[:5]
            suffix = " · …" if len(fn.get("called_from") or []) > len(called) else ""
            lines.append("**Called from:** " + " · ".join(_md_link(c["file"], c["line"]) for c in called) + suffix)
        else:
            lines.append("**Called from:** (none detected)")
        lines.append("")

    lines.append("## Cross-room references\n")
    lines.append("- (none in AST-only mode)\n")

    lines.append("## Strongest incoming edges\n")
    lines.append("")
    lines.append("| From file | Edge type | Weight |")
    lines.append("|---|---|---|")
    for e in incoming_edges[:3]:
        lines.append(f"| {e.get('from')} | {e.get('type')} | {float(e.get('weight') or 0):.2f} |")
    if not incoming_edges:
        lines.append("| (none) | (none) | 0.00 |")

    md = "\n".join(lines).rstrip() + "\n"
    # backfill token count and ensure it's not wildly over budget
    md = md.replace("tokens: 0", f"tokens: {approx_token_count(md)}")
    return md


def write_rooms_and_palace(
    *,
    repo_path: Path,
    model: str | None,
    use_llm: bool,
    network: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """
    Writes:
    - palace-out/rooms/{room_id}.md
    - palace-out/PALACE.md

    Returns updated rooms list (with file paths + token counts) and PALACE.md content.
    """
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    rooms_dir = palace_out / "rooms"
    rooms_dir.mkdir(parents=True, exist_ok=True)

    nodes = network.get("nodes", [])
    edges = network.get("edges", [])
    rooms = network.get("rooms", [])

    nodes_by_id = {n["id"]: n for n in nodes if n.get("id")}

    # Build callsite index: function name -> list[{file,line}]
    callsites: dict[str, list[dict[str, Any]]] = {}
    for e in edges:
        if e.get("type") != "calls":
            continue
        ev = str(e.get("evidence") or "")
        m = re.match(r"(.+?) called at (.+?):(\d+)", ev)
        if not m:
            continue
        fn = m.group(1).strip()
        caller = m.group(2).strip()
        line = int(m.group(3))
        callsites.setdefault(fn, []).append({"file": caller, "line": line})

    # Prepare per-room payloads
    incoming_by_room: dict[str, list[dict[str, Any]]] = {r["id"]: [] for r in rooms if r.get("id")}
    for e in edges:
        to = e.get("to")
        if to not in nodes_by_id:
            continue
        rid = nodes_by_id[to].get("room_id")
        if rid in incoming_by_room:
            incoming_by_room[rid].append(e)
    for rid in incoming_by_room:
        incoming_by_room[rid].sort(key=lambda x: float(x.get("weight") or 0), reverse=True)

    async def _llm_all() -> dict[str, str]:
        m = model or DEFAULT_MODEL
        outs: dict[str, str] = {}
        for r in rooms:
            rid = r["id"]
            covers = r.get("files") or []
            files_payload: list[dict[str, Any]] = []
            for fid in covers:
                n = nodes_by_id.get(fid, {})
                exports = _read_ast_exports(palace_out, str(n.get("hash") or ""))
                # attach call sites to each exported symbol
                exports_with_calls = []
                for ex in exports:
                    name = ex.get("name")
                    exports_with_calls.append(
                        {
                            "name": name,
                            "signature": ex.get("signature"),
                            "line": ex.get("line"),
                            "called_from": callsites.get(str(name), []),
                        }
                    )
                files_payload.append(
                    {
                        "path": fid,
                        "summary": n.get("summary"),
                        "exports": exports_with_calls,
                    }
                )
            outs[rid] = await _write_room_llm(
                model=m,
                room_id=rid,
                room_label=str(r.get("label") or rid),
                covers=covers,
                files_payload=files_payload,
                incoming_edges=incoming_by_room.get(rid, [])[:10],
            )
        return outs

    room_md_by_id: dict[str, str] = {}
    if use_llm:
        try:
            room_md_by_id = asyncio.run(_llm_all())
        except Exception as e:
            print(f"Room writer LLM skipped: {e}")
            room_md_by_id = {}

    updated_rooms: list[dict[str, Any]] = []
    for r in rooms:
        rid = r["id"]
        covers = list(r.get("files") or [])

        # fallback function list based on AST exports cache (exact signatures)
        functions = []
        for fid in covers:
            n = nodes_by_id.get(fid, {})
            exports = _read_ast_exports(palace_out, str(n.get("hash") or ""))
            for ex in exports:
                name = str(ex.get("name") or "")
                sig = str(ex.get("signature") or name)
                called_from = callsites.get(name, [])
                functions.append({"signature": sig, "called_from": called_from})

        md = room_md_by_id.get(rid)
        if not md:
            md = _room_md_fallback(
                room_id=rid,
                room_label=str(r.get("label") or rid),
                covers=covers,
                functions=functions,
                incoming_edges=incoming_by_room.get(rid, [])[:3],
            )

        room_path = rooms_dir / f"{rid}.md"
        room_path.write_text(md, "utf-8")

        updated = dict(r)
        updated["file"] = f"palace-out/rooms/{rid}.md"
        updated["token_count"] = approx_token_count(md)
        updated_rooms.append(updated)

    # PALACE.md (agent-first, concise)
    palace_lines = []
    palace_lines.append("# PALACE.md\n")
    palace_lines.append(
        "This repository has a **memory palace**: rooms you can read to orient quickly, plus a typed network you can query.\n"
    )
    palace_lines.append("## Rooms\n")
    palace_lines.append("| room_id | label | files | summary |")
    palace_lines.append("|---|---:|---:|---|")
    for r in updated_rooms:
        palace_lines.append(
            f"| {r['id']} | {r.get('label','')} | {len(r.get('files') or [])} | {r.get('summary') or ''} |"
        )
    palace_lines.append("\n## Navigation\n")
    palace_lines.append("1. Read this file (`palace-out/PALACE.md`)\n2. Run `palace query \"<task>\"`\n3. Open the top room files in `palace-out/rooms/`\n")

    palace_md = "\n".join(palace_lines).rstrip() + "\n"
    (palace_out / "PALACE.md").write_text(palace_md, "utf-8")
    return updated_rooms, palace_md

