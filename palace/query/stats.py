from __future__ import annotations

import json
from pathlib import Path

from palace.utils.token_counter import approx_token_count


def show_stats(repo_path: Path) -> None:
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    network_path = palace_out / "network.json"
    if not network_path.exists():
        raise SystemExit("No palace-out/network.json found. Run `palace build .` first.")

    network = json.loads(network_path.read_text("utf-8"))
    raw_tokens = sum(int(n.get("size_tokens") or 0) for n in network.get("nodes", []))

    palace_tokens = 0
    palace_md = palace_out / "PALACE.md"
    if palace_md.exists():
        palace_tokens += approx_token_count(palace_md.read_text("utf-8"))
    rooms_dir = palace_out / "rooms"
    if rooms_dir.exists():
        for p in rooms_dir.glob("*.md"):
            palace_tokens += approx_token_count(p.read_text("utf-8"))

    if palace_tokens <= 0:
        print(f"Raw repo tokens (approx): {raw_tokens}")
        print("Palace tokens: (no rooms yet)")
        return

    ratio = (raw_tokens / palace_tokens) if palace_tokens else 0.0
    print(f"Raw repo tokens (approx): {raw_tokens}")
    print(f"Palace navigation tokens (PALACE.md + rooms): {palace_tokens}")
    print(f"Token reduction ratio: {ratio:.1f}x")

