from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from cuddly.indexer.walker import walk


def changed_files(root: Path, conn: sqlite3.Connection) -> list[Path]:
    db_files = {
        row["path"]: {"mtime": row["mtime"], "content_hash": row["content_hash"]}
        for row in conn.execute("SELECT path, mtime, content_hash FROM files")
    }

    changed: list[Path] = []
    for path in walk(root):
        path_str = str(path)
        if path_str not in db_files:
            changed.append(path)
            continue
        if path.stat().st_mtime != db_files[path_str]["mtime"]:
            # mtime changed — verify by hash before marking dirty
            current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if current_hash != db_files[path_str]["content_hash"]:
                changed.append(path)
    return changed
