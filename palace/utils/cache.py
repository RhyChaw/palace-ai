from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8", errors="replace"))


@dataclass(frozen=True)
class CachePaths:
    palace_out: Path

    @property
    def cache_dir(self) -> Path:
        return self.palace_out / "cache"

    @property
    def rooms_dir(self) -> Path:
        return self.palace_out / "rooms"

    @property
    def visualizer_dir(self) -> Path:
        return self.palace_out / "visualizer"

    @property
    def manifest_path(self) -> Path:
        return self.cache_dir / "manifest.json"

    @property
    def extractions_dir(self) -> Path:
        return self.cache_dir / "extractions"


def ensure_output_dirs(palace_out: Path) -> CachePaths:
    palace_out.mkdir(parents=True, exist_ok=True)
    cp = CachePaths(palace_out=palace_out)
    cp.cache_dir.mkdir(parents=True, exist_ok=True)
    cp.rooms_dir.mkdir(parents=True, exist_ok=True)
    cp.visualizer_dir.mkdir(parents=True, exist_ok=True)
    cp.extractions_dir.mkdir(parents=True, exist_ok=True)
    return cp


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text("utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", "utf-8")

