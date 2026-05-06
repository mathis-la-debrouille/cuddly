from __future__ import annotations

import sqlite3
from pathlib import Path

import sqlite_vec


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    from cuddly.config import get_config

    path = db_path or get_config().db_path
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn
