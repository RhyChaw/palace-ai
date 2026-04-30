from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from palace.build.pipeline import build_palace
from palace.install.claude import install_claude
from palace.query.activator import run_query
from palace.visualizer.builder import build_visualizer


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="palace", description="Build and query a repository memory palace.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build palace-out/ for a repository")
    p_build.add_argument("path", nargs="?", default=".", help="Repo path (default: .)")
    p_build.add_argument("--rooms", default="auto", help="auto or an integer (future)")
    p_build.add_argument("--no-git", action="store_true", help="Skip git co-change analysis")
    p_build.add_argument("--no-llm", action="store_true", help="AST-only mode (no LLM calls)")
    p_build.add_argument("--model", default=None, help="Anthropic model name")

    p_update = sub.add_parser("update", help="Incremental rebuild (same as build, uses cache)")
    p_update.add_argument("path", nargs="?", default=".", help="Repo path (default: .)")
    p_update.add_argument("--no-git", action="store_true")
    p_update.add_argument("--no-llm", action="store_true")
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
    p_install_claude = p_install_sub.add_parser("claude", help="Write CLAUDE.md section + hook")
    p_install_claude.add_argument("--path", default=".", help="Repo path (default: .)")

    args = parser.parse_args(argv)

    if args.cmd in {"build", "update"}:
        build_palace(
            Path(args.path),
            use_git=not args.no_git,
            use_llm=not args.no_llm,
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

    raise SystemExit(2)


if __name__ == "__main__":
    main()

