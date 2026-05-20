from __future__ import annotations

from pathlib import Path

from palace.memory.decay import apply_confidence_decay
from palace.memory.init import (
    ensure_memory,
    load_attempts,
    load_patterns,
    save_patterns,
    save_state,
)
from palace.memory.llm import analyze_state_from_attempts, reflect_patterns_from_attempts, slug_id
from palace.memory.palace_md import regenerate_palace_md
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


def run_reflect(
    repo_path: Path,
    *,
    use_llm: bool = True,
    model: str | None = None,
) -> None:
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    if not palace_out.is_dir():
        raise SystemExit(f"No palace at {palace_out}. Run `palace build` first.")

    ensure_memory(palace_out)
    attempts = load_attempts(palace_out)
    if not attempts:
        print("No attempts logged yet. Run `palace learn` after completing tasks.")
        return

    now = utc_now_iso()
    summary = _attempts_summary(attempts)

    if use_llm:
        try:
            new_patterns = reflect_patterns_from_attempts(attempts_summary=summary, model=model)
            pdata = load_patterns(palace_out)
            merged = _merge_reflected_patterns(list(pdata.get("patterns") or []), new_patterns, now=now)
            pdata["patterns"] = apply_confidence_decay(merged)
            save_patterns(palace_out, pdata)
            print(f"Reflected {len(new_patterns)} pattern(s) from attempts.")
        except Exception as e:
            print(f"Pattern reflection skipped: {e}")

        try:
            state_update = analyze_state_from_attempts(attempts_summary=summary, model=model)
            state_update["last_updated"] = now
            save_state(palace_out, state_update)
            print("Updated state.json from reflection.")
        except Exception as e:
            print(f"State analysis skipped: {e}")
    else:
        print("Reflect without LLM: state/patterns unchanged (attempts are ground truth).")

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
    report_path = palace_out / "reflect_report.md"
    report_path.write_text("\n".join(report_lines).rstrip() + "\n", "utf-8")
    print(f"Wrote {report_path}")

    regenerate_palace_md(repo_path)
    print("Regenerated PALACE.md.")
