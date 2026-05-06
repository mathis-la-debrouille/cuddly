from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pathspec

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".next", "dist", "build",
    ".venv", "venv", "env", ".eggs", ".mypy_cache", ".ruff_cache", ".pytest_cache",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".db", ".sqlite", ".sqlite3",
    ".lock",
}


def _load_gitignore(root: Path) -> pathspec.PathSpec | None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", gitignore.read_text().splitlines())


def _is_text_file(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:512]
        return b"\x00" not in chunk
    except (PermissionError, OSError):
        return False


def walk(root: Path) -> Iterator[Path]:
    spec = _load_gitignore(root)

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if any(part in SKIP_DIRS for part in path.parts):
            continue

        if path.suffix.lower() in SKIP_EXTENSIONS:
            continue

        if spec:
            try:
                rel = path.relative_to(root)
                if spec.match_file(str(rel)):
                    continue
            except ValueError:
                pass

        if not _is_text_file(path):
            continue

        yield path
