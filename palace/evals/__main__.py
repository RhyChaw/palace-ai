from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from palace.evals.harness import run_eval


def _find_cases(cases_arg: str | None, repo_path: Path) -> list[dict]:
    candidates = [
        Path(cases_arg) if cases_arg else None,
        repo_path / "evals" / "cases.json",
        Path(__file__).parent.parent.parent / "evals" / "cases.json",
    ]
    for p in candidates:
        if p is not None and p.exists():
            return json.loads(p.read_text("utf-8"))
    raise SystemExit(
        "cases.json not found. Pass --cases <path> or run from the palace-ai repo root."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="palace eval",
        description="Retrieval-quality eval: palace structured recall vs naive keyword search.",
    )
    parser.add_argument("--path", default=".", help="Repo root with palace-out/ (default: .)")
    parser.add_argument("--cases", default=None, help="Path to cases.json (default: evals/cases.json)")
    parser.add_argument("--k", type=int, default=5, help="Primary top-k (default: 5); hit@1 and hit@3 always shown")
    args = parser.parse_args(argv)

    repo_path = Path(args.path).resolve()
    network_path = repo_path / "palace-out" / "network.json"
    if not network_path.exists():
        sys.exit(
            f"palace-out/network.json not found at {repo_path}.\n"
            "Run first:  palace build --no-llm"
        )

    network = json.loads(network_path.read_text("utf-8"))
    cases = _find_cases(args.cases, repo_path)
    k = args.k

    # Always run all three k values for an honest multi-precision picture
    ks_to_run = sorted({1, 3, k})
    all_results = {kk: run_eval(cases, network=network, repo_path=repo_path, k=kk) for kk in ks_to_run}
    results = all_results[k]

    n = results["n_cases"]
    print(f"\nRetrieval eval — {n} cases, palace-ai source corpus\n")

    # Multi-k summary table
    header = f"{'arm':<12}" + "".join(f"  hit@{kk:<4}" for kk in ks_to_run) + "  avg tokens"
    print(header)
    print("-" * len(header))
    for arm in ("baseline", "palace"):
        row = f"{arm:<12}"
        for kk in ks_to_run:
            row += f"  {all_results[kk][arm]['avg_hit_at_k']:.3f}   "
        tok = results[arm]["avg_tokens"]
        row += f" {tok}"
        print(row)

    # Per-case detail at primary k
    print(f"\nPer-case detail (hit@{k}):\n")
    hdr = f"{'#':<4} {'query':<52} {'B h@k':>6} {'P h@k':>6} {'B tok':>7} {'P tok':>7}"
    print(hdr)
    print("-" * len(hdr))
    for i, case in enumerate(results["per_case"], 1):
        q = case["query"][:50]
        b = case["baseline"]
        p = case["palace"]
        marker = " *" if p["hit_at_k"] > b["hit_at_k"] else ""
        print(
            f"{i:<4} {q:<52} {b['hit_at_k']:>6.2f} {p['hit_at_k']:>6.2f}"
            f" {b['tokens']:>7} {p['tokens']:>7}{marker}"
        )
    print("  (* palace wins the case)")

    print()
    b_avg = results["baseline"]["avg_hit_at_k"]
    p_avg = results["palace"]["avg_hit_at_k"]
    b_tok = results["baseline"]["avg_tokens"]
    p_tok = results["palace"]["avg_tokens"]

    hits_ok = p_avg >= b_avg
    tok_ok = p_tok < b_tok

    symbol = "✓" if hits_ok else "✗"
    print(f"{symbol} Palace hit@{k} {p_avg:.3f}  vs  baseline {b_avg:.3f}")

    if tok_ok and p_tok > 0:
        ratio = b_tok / p_tok
        print(f"✓ Palace context {ratio:.1f}× smaller ({p_tok} vs {b_tok} avg tokens)")
    else:
        print(f"✗ Palace tokens ({p_tok}) ≥ baseline ({b_tok})")

    sys.exit(0 if (hits_ok and tok_ok) else 1)


if __name__ == "__main__":
    main()
