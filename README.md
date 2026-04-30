# palace-ai

`palace-ai` is a Python CLI tool that turns a code repository into a navigable **memory palace** for AI agents:

- `palace-out/network.json`: a typed associative network of files and relationships
- `palace-out/rooms/*.md`: room files that orient an agent quickly
- `palace-out/visualizer/index.html`: a self-contained graph visualizer

This repo is implemented from `plan.md`.

## Install (dev)

```bash
python -m pip install -e .
```

## Quick start

```bash
palace build .
palace query "auth flow"
palace serve
```

