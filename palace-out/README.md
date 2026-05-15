# Sample `palace-out/`

Checked-in **small example** of palace output (built from `tests/fixture/`).

Regenerate:

```bash
palace build tests/fixture --no-git
cp -a tests/fixture/palace-out/. palace-out/
rm -rf palace-out/cache
```

`cache/` is omitted from git to keep the tree small.
