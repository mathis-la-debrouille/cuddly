from __future__ import annotations

import sqlite3
import time

# (version, sql) — add future migrations here
MIGRATIONS: list[tuple[int, str]] = []


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            applied_at REAL    NOT NULL
        )
    """)
    conn.commit()

    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    for version, sql in MIGRATIONS:
        if version not in applied:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", (version, time.time()))
            conn.commit()
