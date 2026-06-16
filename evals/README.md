# Retrieval-quality eval harness

Measures whether palace's structured retrieval beats a naive keyword baseline.
Palace's thesis is that its graph-structured memory returns the *right* context
in fewer tokens — this harness makes that claim falsifiable.

## What it measures

Two retrieval arms run against the same labeled cases:

| Arm | Method | Context returned |
|-----|--------|-----------------|
| **baseline** | Substring/keyword search over raw file names + contents | Top-k raw file contents |
| **palace** | Activation spreading over the network graph (`activate()`) | Top-2 room markdowns |

Metrics per arm:

- **hit@k** — fraction of expected node IDs found in the top-k results (k=5 default)
- **recall** — same as hit@k for single-expected-node cases
- **avg tokens** — average token cost of the returned context across all cases

The token comparison is the core claim: palace finds the same (or more) relevant
nodes while returning *structured, compressed* room context instead of dumping
raw files.

## Corpus

Palace is built over its own source tree (`palace-ai/`) using AST-only mode
(no LLM, no git, fully deterministic).  This is dogfooding: palace must locate
its own internals correctly or the eval fails.

## Cases

`evals/cases.json` contains 10 labeled queries.  Each case targets a node
where the query is *non-obvious* — the expected answer can't be found by simple
filename matching, but emerges from symbol names, co-occurrence, or graph
propagation.  Each case has a `_why` field documenting the trap for the baseline.

## How to run

Prerequisites: `palace build` must have already run on the repo root.

```bash
# Quickest — uses the existing palace-out/
palace eval

# Or via python module
python -m palace.evals

# Custom options
palace eval --path /path/to/repo --cases evals/cases.json --k 5
```

**Build first if palace-out/ is missing or stale:**

```bash
palace build --no-llm --no-git   # ~1s on palace-ai itself
palace eval
```

## CI smoke test

`tests/test_evals.py` runs automatically in pytest.  It:

1. Copies the palace source into a tmp dir
2. Builds palace fresh (`--no-llm --no-git`)
3. Runs both arms on all 10 cases
4. Asserts palace hit@5 ≥ 0.80 and ≥ baseline, and palace avg tokens < baseline

A retrieval regression (new code that breaks graph scoring or node labeling)
will fail this test before it lands.

```bash
pytest tests/test_evals.py -v
```

## Adding cases

Edit `evals/cases.json`.  Each entry:

```json
{
  "_why": "explanation of why this is non-obvious for naive search",
  "query":    "natural language question",
  "expected": ["palace/relative/path/to/node.py"]
}
```

`expected` is a list of node IDs exactly as they appear in `palace-out/network.json`.
Run `palace eval` after adding cases to confirm both arms behave as expected.

## Interpreting the output

```
Retrieval eval — 10 cases, hit@5

arm          hit@5      recall     avg tokens
----------------------------------------------
baseline     0.900      0.900      1823
palace       1.000      1.000       648

#    query                                                 B h@k  P h@k   B tok   P tok
------------------------------------------------------------------------------------------
1    how does activate compute node scores with hop dec...  1.00   1.00    1620     648
...

✓ Palace hit@5 1.000  vs  baseline 0.900
✓ Palace context 2.8× smaller (648 vs 1823 avg tokens)
```

- **B h@k / P h@k**: baseline and palace hit@k for that case (1.00 = found, 0.00 = missed)
- **B tok / P tok**: token cost of the context each arm returned for that case
- Exit code 0 if palace wins on both metrics; 1 otherwise (useful in CI scripts)
