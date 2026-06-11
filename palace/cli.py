from __future__ import annotations

import argparse
from pathlib import Path

from palace.build.pipeline import build_palace
from palace.install.claude import install_claude
from palace.memory.learn import run_learn
from palace.memory.mem_cli import cmd_add, cmd_recall, cmd_reflect
from palace.memory.reflect import run_reflect
from palace.memory.snapshot import run_snapshot
from palace.memory.status import show_status
from palace.query.activator import run_query
from palace.visualizer.builder import build_visualizer


def _add_memory_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=None,
        help="Standalone memory directory (default: {path}/palace-out/memory)",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="palace", description="Build and query a repository memory palace.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build palace-out/ for a repository")
    p_build.add_argument("path", nargs="?", default=".", help="Repo path (default: .)")
    p_build.add_argument("--rooms", default="auto", help="auto or an integer (future)")
    p_build.add_argument("--no-git", action="store_true", help="Skip git co-change analysis")
    p_build.add_argument(
        "--no-llm",
        action="store_true",
        help="AST-only mode, no LLM calls (default; flag kept for explicitness)",
    )
    p_build.add_argument("--llm", action="store_true", help="Enable LLM enrichment (requires ANTHROPIC_API_KEY)")
    p_build.add_argument("--model", default=None, help="Anthropic model name")

    p_update = sub.add_parser("update", help="Incremental rebuild (same as build, uses cache)")
    p_update.add_argument("path", nargs="?", default=".", help="Repo path (default: .)")
    p_update.add_argument("--no-git", action="store_true")
    p_update.add_argument("--no-llm", action="store_true", help="AST-only mode (default)")
    p_update.add_argument("--llm", action="store_true", help="Enable LLM enrichment")
    p_update.add_argument("--model", default=None)

    p_query = sub.add_parser("query", help="Query the palace network")
    p_query.add_argument("text", help="Query text in quotes")
    p_query.add_argument("--threshold", type=float, default=0.15)
    p_query.add_argument("--depth", type=int, default=3)
    p_query.add_argument("--path", default=".", help="Repo path (default: .)")

    p_serve = sub.add_parser("serve", help="Serve the visualizer via http.server and open browser")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--path", default=".", help="Repo path (default: .)")

    p_visualize = sub.add_parser("visualize", help="Rebuild visualizer only")
    p_visualize.add_argument("--path", default=".", help="Repo path (default: .)")

    p_stats = sub.add_parser("stats", help="Show token reduction stats")
    p_stats.add_argument("--path", default=".", help="Repo path (default: .)")

    p_install = sub.add_parser("install", help="Install agent integrations")
    p_install_sub = p_install.add_subparsers(dest="install_target", required=True)
    p_install_claude = p_install_sub.add_parser("claude", help="Write CLAUDE.md + Claude Code PreToolUse hook")
    p_install_claude.add_argument("--path", default=".", help="Repo path (default: .)")

    p_learn = sub.add_parser("learn", help="Log a completed task and update palace memory (v2)")
    p_learn.add_argument("--path", default=".", help="Repo path (default: .)")
    _add_memory_root_arg(p_learn)
    p_learn.add_argument("--task", default=None, help="Task description")
    p_learn.add_argument(
        "--outcome",
        choices=["success", "failure", "partial", "abandoned"],
        default=None,
        help="Task outcome",
    )
    p_learn.add_argument("--files-modified", nargs="*", default=None, help="Modified file paths")
    p_learn.add_argument("--notes", default=None, help="Notes for future agents")
    p_learn.add_argument("--approach", default=None, help="Approach taken")
    p_learn.add_argument("--failure-reason", default=None, help="Why it failed (failure outcome)")
    p_learn.add_argument("--rooms-consulted", nargs="*", default=None, help="Room ids consulted")
    p_learn.add_argument("--interactive", action="store_true", help="Prompt for task details")
    p_learn.add_argument("--no-llm", action="store_true", help="Heuristic extraction only (no API calls)")
    p_learn.add_argument("--llm", action="store_true", help="Use LLM for pattern/failure extraction")
    p_learn.add_argument("--model", default=None, help="Anthropic model for memory extraction")

    p_reflect = sub.add_parser("reflect", help="Analyze all attempts and refresh patterns/state (v2)")
    p_reflect.add_argument("--path", default=".", help="Repo path (default: .)")
    _add_memory_root_arg(p_reflect)
    p_reflect.add_argument("--no-llm", action="store_true", help="Skip LLM analysis")
    p_reflect.add_argument("--llm", action="store_true", help="Use LLM (default when API key set)")
    p_reflect.add_argument("--model", default=None)

    p_status = sub.add_parser("status", help="Show palace memory game state (v2)")
    p_status.add_argument("--path", default=".", help="Repo path (default: .)")
    _add_memory_root_arg(p_status)

    p_snapshot = sub.add_parser("snapshot", help="Save a point-in-time palace backup (v2)")
    p_snapshot.add_argument("--path", default=".", help="Repo path (default: .)")
    _add_memory_root_arg(p_snapshot)

    p_mem = sub.add_parser("mem", help="Standalone repo-independent memory service (JSON)")
    p_mem_sub = p_mem.add_subparsers(dest="mem_cmd", required=True)

    p_mem_recall = p_mem_sub.add_parser("recall", help="Recall events/patterns by keyword (JSON)")
    p_mem_recall.add_argument("--root", required=True, help="Memory directory (e.g. ~/.daimon/memory)")
    p_mem_recall.add_argument("--query", required=True, help="Query text")
    p_mem_recall.add_argument("--json", action="store_true", help="Emit JSON (required for machine-readable output)")

    p_mem_reflect = p_mem_sub.add_parser("reflect", help="Reflect on stored events (JSON)")
    p_mem_reflect.add_argument("--root", required=True, help="Memory directory")
    p_mem_reflect.add_argument("--json", action="store_true", help="Emit JSON (required for machine-readable output)")
    p_mem_reflect.add_argument("--no-llm", action="store_true", help="Skip LLM analysis")
    p_mem_reflect.add_argument("--llm", action="store_true", help="Use LLM (default when API key set)")
    p_mem_reflect.add_argument("--model", default=None)

    p_mem_add = p_mem_sub.add_parser("add", help="Append an event (JSON)")
    p_mem_add.add_argument("--root", required=True, help="Memory directory")
    p_mem_add.add_argument("--json", action="store_true", help="Emit JSON (required for machine-readable output)")
    p_mem_add.add_argument("--task", required=True, help="Task description")
    p_mem_add.add_argument(
        "--outcome",
        required=True,
        choices=["success", "failure", "partial", "abandoned"],
        help="Task outcome",
    )
    p_mem_add.add_argument("--notes", default=None, help="Agent notes")
    p_mem_add.add_argument("--approach", default=None, help="Approach taken")
    p_mem_add.add_argument("--failure-reason", default=None, help="Why it failed")
    p_mem_add.add_argument("--no-llm", action="store_true", help="Skip LLM pattern/failure extraction")
    p_mem_add.add_argument("--llm", action="store_true", help="Use LLM extraction")
    p_mem_add.add_argument("--model", default=None)

    args = parser.parse_args(argv)

    if args.cmd in {"build", "update"}:
        if args.llm and args.no_llm:
            raise SystemExit("Use only one of --llm or --no-llm.")
        use_llm = bool(args.llm)
        build_palace(
            Path(args.path),
            use_git=not args.no_git,
            use_llm=use_llm,
            model=args.model,
        )
        return

    if args.cmd == "visualize":
        build_visualizer(Path(args.path))
        return

    if args.cmd == "query":
        run_query(Path(args.path), args.text, threshold=args.threshold, depth=args.depth)
        return

    if args.cmd == "serve":
        from palace.visualizer.serve import serve_visualizer

        serve_visualizer(Path(args.path), port=args.port)
        return

    if args.cmd == "stats":
        from palace.query.stats import show_stats

        show_stats(Path(args.path))
        return

    if args.cmd == "install" and args.install_target == "claude":
        install_claude(Path(args.path))
        return

    if args.cmd == "learn":
        if args.llm and args.no_llm:
            raise SystemExit("Use only one of --llm or --no-llm.")
        use_llm = not args.no_llm
        if args.llm:
            use_llm = True
        run_learn(
            Path(args.path),
            root=Path(args.root) if args.root else None,
            task=args.task,
            outcome=args.outcome,
            files_modified=args.files_modified,
            notes=args.notes,
            approach=args.approach,
            failure_reason=args.failure_reason,
            rooms_consulted=args.rooms_consulted,
            interactive=args.interactive,
            use_llm=use_llm,
            model=args.model,
        )
        return

    if args.cmd == "reflect":
        use_llm = not args.no_llm
        if args.llm:
            use_llm = True
        run_reflect(
            Path(args.path),
            root=Path(args.root) if args.root else None,
            use_llm=use_llm,
            model=args.model,
        )
        return

    if args.cmd == "status":
        show_status(Path(args.path), root=Path(args.root) if args.root else None)
        return

    if args.cmd == "snapshot":
        run_snapshot(Path(args.path), root=Path(args.root) if args.root else None)
        return

    if args.cmd == "mem":
        if not getattr(args, "json", False):
            raise SystemExit("mem commands require --json for machine-readable output.")
        root = Path(args.root)
        if args.mem_cmd == "recall":
            cmd_recall(root=root, query=args.query)
            return
        if args.mem_cmd == "reflect":
            use_llm = not args.no_llm
            if args.llm:
                use_llm = True
            cmd_reflect(root=root, use_llm=use_llm, model=args.model)
            return
        if args.mem_cmd == "add":
            use_llm = bool(args.llm) and not args.no_llm
            cmd_add(
                root=root,
                task=args.task,
                outcome=args.outcome,
                notes=args.notes,
                approach=args.approach,
                failure_reason=args.failure_reason,
                use_llm=use_llm,
                model=args.model,
            )
            return

    raise SystemExit(2)


if __name__ == "__main__":
    main()
