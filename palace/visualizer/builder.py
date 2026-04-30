from __future__ import annotations

import json
from pathlib import Path

from palace.utils.cache import ensure_output_dirs


def build_visualizer(repo_path: Path) -> Path:
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    cp = ensure_output_dirs(palace_out)

    network_path = palace_out / "network.json"
    if not network_path.exists():
        raise SystemExit("No palace-out/network.json found. Run `palace build` first.")

    network = json.loads(network_path.read_text("utf-8"))
    template_path = Path(__file__).with_name("template.html")
    template = template_path.read_text("utf-8")

    html = template.replace("__NETWORK_JSON__", json.dumps(network))
    out = cp.visualizer_dir / "index.html"
    out.write_text(html, "utf-8")
    return out

