from __future__ import annotations

from pathlib import Path
from typing import Any

from palace.memory.decay import apply_confidence_decay
from palace.memory.init import (
    ensure_memory,
    load_attempts,
    load_patterns,
    load_state,
    save_patterns,
    save_state,
)
from palace.memory.llm import analyze_state_from_attempts, reflect_patterns_from_attempts, slug_id
from palace.memory.palace_md import regenerate_palace_md
from palace.memory.paths import MemoryPaths, memory_paths, resolve_memory_paths
from palace.memory.schemas import utc_now_iso


def _attempts_summary(attempts: list[dict], *, max_entries: int = 40) -> str:
    lines: list[str] = []
    for a in attempts[-max_entries:]:
        lines.append(
            f"- [{a.get('outcome')}] {a.get('task')} | files: {', '.join(a.get('files_modified') or [])[:120]} | notes: {(a.get('agent_notes') or '')[:200]}"
        )
    return "\n".join(lines) if lines else "(no attempts yet)"


def _merge_reflected_patterns(existing: list[dict], new_patterns: list[dict], *, now: str) -> list[dict]:
    by_id = {p.get("id"): dict(p) for p in existing if p.get("id")}
    for np in new_patterns:
        pid = str(np.get("id") or slug_id(str(np.get("name") or "pattern")))
        if pid in by_id:
            cur = by_id[pid]
            cur["description"] = np.get("description") or cur.get("description")
            cur["implementation_sequence"] = np.get("implementation_sequence") or cur.get("implementation_sequence")
            cur["codebase_specific_notes"] = np.get("codebase_specific_notes") or cur.get("codebase_specific_notes")
            cur["anti_patterns"] = np.get("anti_patterns") or cur.get("anti_patterns")
            cur["last_updated"] = now
            cur["confidence"] = min(0.99, float(cur.get("confidence") or 0.5) + 0.05)
        else:
            np = dict(np)
            np["id"] = pid
            np.setdefault("success_count", 0)
            np.setdefault("failure_count", 0)
            np.setdefault("confidence", 0.65)
            np.setdefault("first_seen", now)
            np["last_updated"] = now
            by_id[pid] = np
    return sorted(by_id.values(), key=lambda p: float(p.get("confidence") or 0), reverse=True)


def reflect_memory(
    mp: MemoryPaths,
    *,
    use_llm: bool = True,
    model: str | None = None,
    write_report: bool = False,
) -> dict[str, Any]:
    """Analyze attempts and refresh patterns/state. Works without a built palace."""
    ensure_memory(mp)
    attempts = load_attempts(mp)
    now = utc_now_iso()

    result: dict[str, Any] = {
        "ok": True,
        "attempts_count": len(attempts),
        "patterns_reflected": 0,
        "patterns_total": len(load_patterns(mp).get("patterns") or []),
        "state_updated": False,
        "last_updated": now,
        "llm_used": use_llm,
    }

    if not attempts:
        result["message"] = "no attempts"
        return result

    summary = _attempts_summary(attempts)
    warnings: list[str] = []

    if use_llm:
        try:
            new_patterns = reflect_patterns_from_attempts(attempts_summary=summary, model=model)
            pdata = load_patterns(mp)
            merged = _merge_reflected_patterns(list(pdata.get("patterns") or []), new_patterns, now=now)
            pdata["patterns"] = apply_confidence_decay(merged)
            save_patterns(mp, pdata)
            result["patterns_reflected"] = len(new_patterns)
            result["patterns_total"] = len(pdata["patterns"])
        except Exception as e:
            warnings.append(f"pattern reflection: {e}")
            pdata = load_patterns(mp)
            if pdata.get("patterns"):
                pdata["patterns"] = apply_confidence_decay(list(pdata["patterns"]))
                save_patterns(mp, pdata)
                result["patterns_total"] = len(pdata["patterns"])

        try:
            state_update = analyze_state_from_attempts(attempts_summary=summary, model=model)
            state_update["last_updated"] = now
            save_state(mp, state_update)
            result["state_updated"] = True
            result["state"] = state_update
        except Exception as e:
            warnings.append(f"state analysis: {e}")
            state = load_state(mp)
            state["last_updated"] = now
            save_state(mp, state)
    else:
        pdata = load_patterns(mp)
        if pdata.get("patterns"):
            pdata["patterns"] = apply_confidence_decay(list(pdata["patterns"]))
            save_patterns(mp, pdata)
            result["patterns_total"] = len(pdata["patterns"])
        state = load_state(mp)
        state["last_updated"] = now
        save_state(mp, state)

    if warnings:
        result["warnings"] = warnings

    if write_report:
        report_lines = [
            "# Palace Reflect Report",
            "",
            f"Generated: {now}",
            f"Attempts analyzed: {len(attempts)}",
            "",
            "## Recent attempts",
            "",
            summary,
            "",
        ]
        report_path = mp.memory_dir / "reflect_report.md"
        report_path.write_text("\n".join(report_lines).rstrip() + "\n", "utf-8")
        result["report_path"] = str(report_path)

    return result


def run_reflect(
    repo_path: Path,
    *,
    root: Path | None = None,
    use_llm: bool = True,
    model: str | None = None,
) -> None:
    if root is not None:
        mp = resolve_memory_paths(root=root)
        result = reflect_memory(mp, use_llm=use_llm, model=model, write_report=True)
        if result.get("message") == "no attempts":
            print("No attempts logged yet. Run `palace learn` after completing tasks.")
            return
        if result.get("patterns_reflected"):
            print(f"Reflected {result['patterns_reflected']} pattern(s) from attempts.")
        if result.get("state_updated"):
            print("Updated state.json from reflection.")
        elif not use_llm:
            print("Reflect without LLM: state/patterns unchanged (attempts are ground truth).")
        for w in result.get("warnings") or []:
            print(f"Skipped: {w}")
        if result.get("report_path"):
            print(f"Wrote {result['report_path']}")
        return

    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    if not palace_out.is_dir():
        raise SystemExit(f"No palace at {palace_out}. Run `palace build` first.")

    mp = memory_paths(palace_out)
    result = reflect_memory(mp, use_llm=use_llm, model=model, write_report=True)

    if result.get("message") == "no attempts":
        print("No attempts logged yet. Run `palace learn` after completing tasks.")
        return

    if result.get("patterns_reflected"):
        print(f"Reflected {result['patterns_reflected']} pattern(s) from attempts.")
    if result.get("state_updated"):
        print("Updated state.json from reflection.")
    elif not use_llm:
        print("Reflect without LLM: state/patterns unchanged (attempts are ground truth).")
    for w in result.get("warnings") or []:
        print(f"Skipped: {w}")

    report_path = palace_out / "reflect_report.md"
    if result.get("report_path"):
        # also write legacy location for repo layout
        summary = _attempts_summary(load_attempts(mp))
        report_lines = [
            "# Palace Reflect Report",
            "",
            f"Generated: {result['last_updated']}",
            f"Attempts analyzed: {result['attempts_count']}",
            "",
            "## Recent attempts",
            "",
            summary,
            "",
        ]
        report_path.write_text("\n".join(report_lines).rstrip() + "\n", "utf-8")
        print(f"Wrote {report_path}")

    regenerate_palace_md(repo_path)
    print("Regenerated PALACE.md.")
