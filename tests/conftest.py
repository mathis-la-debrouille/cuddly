from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cuddly.db.schema import create_schema


@pytest.fixture()
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """In-memory SQLite with the cuddly schema (no sqlite-vec extension)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    # Create schema without vec0 (not available without extension in test env)
    conn.executescript("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY, path TEXT NOT NULL UNIQUE,
            mtime REAL NOT NULL, content_hash TEXT NOT NULL, indexed_at REAL NOT NULL
        );
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY, file_id INTEGER NOT NULL,
            kind TEXT NOT NULL, start_line INTEGER NOT NULL, end_line INTEGER NOT NULL,
            text TEXT NOT NULL, token_count INTEGER NOT NULL
        );
        CREATE VIRTUAL TABLE chunks_fts USING fts5(text, tokenize='porter ascii');
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY, chunk_id INTEGER NOT NULL,
            name TEXT NOT NULL, kind TEXT NOT NULL, qualified_name TEXT NOT NULL
        );
        CREATE TABLE edges (
            src_entity_id INTEGER NOT NULL, dst_entity_id INTEGER NOT NULL,
            edge_type TEXT NOT NULL, PRIMARY KEY (src_entity_id, dst_entity_id, edge_type)
        );
    """)
    conn.commit()
    return conn


@pytest.fixture()
def sample_project() -> Path:
    return Path(__file__).parent / "fixtures" / "sample_project"
