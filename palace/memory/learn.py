from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Any

from palace.memory.init import (
    append_attempt,
    ensure_memory,
    load_failures,
    load_patterns,
    load_state,
    save_failures,
    save_patterns,
    save_state,
)
from palace.memory.llm import extract_failure_from_attempt, extract_pattern_from_attempt, slug_id
from palace.memory.palace_md import regenerate_palace_md
from palace.memory.paths import MemoryPaths, memory_paths, resolve_memory_paths
from palace.memory.schemas import VALID_OUTCOMES, utc_now_iso


def _git_modified_files(repo_path: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_path), "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode != 0:
            out = subprocess.run(
                ["git", "-C", str(repo_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
            )
        lines = [ln.strip() for ln in (out.stdout or "").splitlines() if ln.strip()]
        files: list[str] = []
        for ln in lines:
            if len(ln) > 3 and ln[2] == " ":
                files.append(ln[3:].strip())
            else:
                files.append(ln)
        return files
    except OSError:
        return []


def _merge_pattern(existing: dict[str, Any], extracted: dict[str, Any], *, now: str) -> dict[str, Any]:
    pid = str(extracted.get("id") or slug_id(str(extracted.get("name") or "pattern")))
    merged = dict(existing)
    merged["id"] = pid
    merged["name"] = extracted.get("name") or merged.get("name") or pid
    merged["domain"] = extracted.get("domain") or merged.get("domain") or "general"
    merged["rooms_involved"] = extracted.get("rooms_involved") or merged.get("rooms_involved") or []
    merged["description"] = extracted.get("description") or merged.get("description") or ""
    merged["implementation_sequence"] = (
        extracted.get("implementation_sequence") or merged.get("implementation_sequence") or []
    )
    merged["codebase_specific_notes"] = (
        extracted.get("codebase_specific_notes") or merged.get("codebase_specific_notes") or ""
    )
    merged["anti_patterns"] = extracted.get("anti_patterns") or merged.get("anti_patterns") or []
    merged["success_count"] = int(merged.get("success_count") or 0) + 1
    merged["failure_count"] = int(merged.get("failure_count") or 0)
    merged["confidence"] = min(0.99, float(merged.get("confidence") or 0.5) + 0.1)
    merged.setdefault("first_seen", now)
    merged["last_updated"] = now
    return merged


def _upsert_pattern(mp: MemoryPaths, extracted: dict[str, Any], *, now: str) -> str:
    data = load_patterns(mp)
    patterns: list[dict] = list(data.get("patterns") or [])
    pid = str(extracted.get("id") or slug_id(str(extracted.get("name") or "pattern")))
    found = False
    for i, p in enumerate(patterns):
        if p.get("id") == pid:
            patterns[i] = _merge_pattern(p, extracted, now=now)
            found = True
            break
    if not found:
        new_p = _merge_pattern(
            {
                "success_count": 0,
                "failure_count": 0,
                "confidence": 0.6,
            },
            extracted,
            now=now,
        )
        patterns.append(new_p)
    data["patterns"] = patterns
    save_patterns(mp, data)
    return pid


def _upsert_failure(mp: MemoryPaths, extracted: dict[str, Any], *, now: str) -> str:
    data = load_failures(mp)
    failures: list[dict] = list(data.get("failures") or [])
    key = (
        str(extracted.get("task_type") or ""),
        str(extracted.get("approach_attempted") or ""),
        str(extracted.get("failure_reason") or ""),
    )
    fid = slug_id("_".join(key))[:40] or str(uuid.uuid4())[:8]
    found = None
    for f in failures:
        if (
            f.get("task_type") == extracted.get("task_type")
            and f.get("approach_attempted") == extracted.get("approach_attempted")
            and f.get("failure_reason") == extracted.get("failure_reason")
        ):
            found = f
            break
    if found:
        found["times_hit"] = int(found.get("times_hit") or 0) + 1
        if extracted.get("resolution"):
            found["resolution"] = extracted["resolution"]
    else:
        failures.append(
            {
                "id": fid,
                "task_type": extracted.get("task_type") or "unknown",
                "approach_attempted": extracted.get("approach_attempted") or "",
                "failure_reason": extracted.get("failure_reason") or "",
                "rooms_involved": extracted.get("rooms_involved") or [],
                "resolution": extracted.get("resolution") or "",
                "times_hit": 1,
                "first_seen": now,
            }
        )
    data["failures"] = failures
    save_failures(mp, data)
    return fid


def _heuristic_pattern(task: str, notes: str, files_modified: list[str], *, now: str) -> dict[str, Any]:
    return {
        "id": slug_id(task),
        "name": task[:80],
        "domain": "general",
        "rooms_involved": [],
        "description": notes or f"Succeeded on: {task}",
        "implementation_sequence": [f"Modified: {f}" for f in files_modified[:6]],
        "codebase_specific_notes": notes,
        "anti_patterns": [],
        "success_count": 1,
        "failure_count": 0,
        "confidence": 0.5,
        "first_seen": now,
        "last_updated": now,
    }


def _touch_state(mp: MemoryPaths, *, now: str, task: str, outcome: str) -> None:
    state = load_state(mp)
    state["last_updated"] = now
    if outcome == "success" and task:
        debt = state.get("known_tech_debt")
        if isinstance(debt, list) and f"Completed: {task}" not in debt:
            pass
    save_state(mp, state)


def _interactive_learn(repo_path: Path) -> dict[str, Any]:
    task = input("What task did you work on? ").strip()
    outcome_raw = input("Did it succeed? (y/n/partial/abandoned): ").strip().lower()
    outcome_map = {"y": "success", "yes": "success", "n": "failure", "no": "failure", "p": "partial", "a": "abandoned"}
    outcome = outcome_map.get(outcome_raw, outcome_raw if outcome_raw in VALID_OUTCOMES else "partial")
    git_files = _git_modified_files(repo_path)
    if git_files:
        print("Git modified files:")
        for f in git_files[:20]:
            print(f"  {f}")
        extra = input("Additional files (space-separated, or Enter to use git list): ").strip()
        files = extra.split() if extra else git_files
    else:
        files_raw = input("Which files did you modify? (space-separated): ").strip()
        files = files_raw.split() if files_raw else []
    notes = input("Any notes for future agents? ").strip()
    approach = input("Brief approach (optional): ").strip()
    failure_reason = ""
    if outcome == "failure":
        failure_reason = input("Why did it fail? ").strip()
    return {
        "task": task,
        "outcome": outcome,
        "files_modified": files,
        "notes": notes,
        "approach": approach,
        "failure_reason": failure_reason or None,
    }


def run_learn(
    repo_path: Path,
    *,
    root: Path | None = None,
    task: str | None = None,
    outcome: str | None = None,
    files_modified: list[str] | None = None,
    notes: str | None = None,
    approach: str | None = None,
    failure_reason: str | None = None,
    rooms_consulted: list[str] | None = None,
    patterns_used: list[str] | None = None,
    session_id: str | None = None,
    token_cost: int | None = None,
    interactive: bool = False,
    use_llm: bool = True,
    model: str | None = None,
) -> None:
    repo_path = repo_path.resolve()
    standalone = root is not None
    if standalone:
        mp = resolve_memory_paths(root=root)
    else:
        palace_out = repo_path / "palace-out"
        if not palace_out.is_dir():
            raise SystemExit(f"No palace at {palace_out}. Run `palace build` first.")
        mp = memory_paths(palace_out)

    ensure_memory(mp)

    if interactive or not task:
        params = _interactive_learn(repo_path)
        task = params["task"]
        outcome = params["outcome"]
        files_modified = params["files_modified"]
        notes = params.get("notes") or ""
        approach = params.get("approach") or ""
        failure_reason = params.get("failure_reason")

    if not task:
        raise SystemExit("Task is required.")
    if not outcome or outcome not in VALID_OUTCOMES:
        raise SystemExit(f"Outcome must be one of: {', '.join(sorted(VALID_OUTCOMES))}")

    now = utc_now_iso()
    files_modified = list(files_modified or [])
    pattern_ids: list[str] = list(patterns_used or [])

    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": now,
        "task": task,
        "rooms_consulted": list(rooms_consulted or []),
        "approach": approach or "",
        "outcome": outcome,
        "files_modified": files_modified,
        "patterns_used": pattern_ids,
        "failure_reason": failure_reason,
        "agent_notes": notes or "",
        "session_id": session_id or "",
        "token_cost": token_cost,
    }
    append_attempt(mp, entry)

    if outcome == "success":
        if use_llm:
            try:
                extracted = extract_pattern_from_attempt(
                    task=task,
                    files_modified=files_modified,
                    notes=notes or "",
                    approach=approach or "",
                    model=model,
                )
                pid = _upsert_pattern(mp, extracted, now=now)
                pattern_ids.append(pid)
                print(f"Learned pattern: {pid}")
            except Exception as e:
                print(f"LLM pattern extraction skipped: {e}")
                pid = _upsert_pattern(mp, _heuristic_pattern(task, notes or "", files_modified, now=now), now=now)
                pattern_ids.append(pid)
        else:
            pid = _upsert_pattern(mp, _heuristic_pattern(task, notes or "", files_modified, now=now), now=now)
            pattern_ids.append(pid)
            print(f"Recorded pattern (heuristic): {pid}")

    elif outcome == "failure":
        extracted: dict[str, Any]
        if use_llm:
            try:
                extracted = extract_failure_from_attempt(
                    task=task,
                    approach=approach or "",
                    failure_reason=failure_reason or "",
                    notes=notes or "",
                    files_modified=files_modified,
                    model=model,
                )
            except Exception as e:
                print(f"LLM failure extraction skipped: {e}")
                extracted = {
                    "task_type": task[:60],
                    "approach_attempted": approach or "",
                    "failure_reason": failure_reason or notes or "unknown",
                    "resolution": "",
                }
        else:
            extracted = {
                "task_type": task[:60],
                "approach_attempted": approach or "",
                "failure_reason": failure_reason or notes or "unknown",
                "resolution": "",
            }
        fid = _upsert_failure(mp, extracted, now=now)
        print(f"Recorded failure mode: {fid}")

    _touch_state(mp, now=now, task=task, outcome=outcome)
    if not standalone:
        regenerate_palace_md(repo_path)
        print(f"Logged attempt ({outcome}). Updated PALACE.md.")
    else:
        print(f"Logged attempt ({outcome}).")
