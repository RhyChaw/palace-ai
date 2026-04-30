from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LanguageInfo:
    id: str
    extensions: tuple[str, ...]


PYTHON = LanguageInfo("python", (".py",))
JAVASCRIPT = LanguageInfo("javascript", (".js", ".jsx", ".mjs", ".cjs"))
TYPESCRIPT = LanguageInfo("typescript", (".ts", ".tsx", ".mts", ".cts"))


LANGUAGES: tuple[LanguageInfo, ...] = (PYTHON, JAVASCRIPT, TYPESCRIPT)


def detect_language(path: str | Path) -> str | None:
    p = Path(path)
    suf = p.suffix.lower()
    for lang in LANGUAGES:
        if suf in lang.extensions:
            return lang.id
    return None

