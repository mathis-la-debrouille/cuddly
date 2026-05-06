from __future__ import annotations

import sqlite3

# Embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIM = 384


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS files (
            id           INTEGER PRIMARY KEY,
            path         TEXT    NOT NULL UNIQUE,
            mtime        REAL    NOT NULL,
            content_hash TEXT    NOT NULL,
            indexed_at   REAL    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id          INTEGER PRIMARY KEY,
            file_id     INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            kind        TEXT    NOT NULL,
            start_line  INTEGER NOT NULL,
            end_line    INTEGER NOT NULL,
            text        TEXT    NOT NULL,
            token_count INTEGER NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, tokenize='porter ascii');

        CREATE TABLE IF NOT EXISTS entities (
            id             INTEGER PRIMARY KEY,
            chunk_id       INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
            name           TEXT    NOT NULL,
            kind           TEXT    NOT NULL,
            qualified_name TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS edges (
            src_entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            dst_entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            edge_type     TEXT    NOT NULL,
            PRIMARY KEY (src_entity_id, dst_entity_id, edge_type)
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_file     ON chunks(file_id);
        CREATE INDEX IF NOT EXISTS idx_entities_chunk  ON entities(chunk_id);
        CREATE INDEX IF NOT EXISTS idx_entities_name   ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_edges_src       ON edges(src_entity_id);
        CREATE INDEX IF NOT EXISTS idx_edges_dst       ON edges(dst_entity_id);
    """)

    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
            chunk_id  INTEGER PRIMARY KEY,
            embedding FLOAT[{EMBEDDING_DIM}]
        )
    """)
    conn.commit()
