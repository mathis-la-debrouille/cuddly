from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from cuddly.embeddings.embedder import Embedder


@dataclass
class SearchResult:
    chunk_id: int
    file_path: str
    start_line: int
    end_line: int
    text: str
    score: float


def semantic_search(
    conn: sqlite3.Connection,
    embedder: Embedder,
    query: str,
    top_k: int = 10,
    file_filter: str | None = None,
) -> list[SearchResult]:
    vec_count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    if vec_count == 0:
        return _keyword_search(conn, query, top_k, file_filter)

    query_vec = embedder.embed_one(query).astype(np.float32).tobytes()

    rows = conn.execute(
        """
        SELECT vc.chunk_id, vc.distance, c.start_line, c.end_line, c.text, f.path
        FROM vec_chunks vc
        JOIN chunks c ON c.id = vc.chunk_id
        JOIN files  f ON f.id = c.file_id
        WHERE vc.embedding MATCH ?
        ORDER BY vc.distance
        LIMIT ?
        """,
        (query_vec, top_k),
    ).fetchall()

    results: list[SearchResult] = []
    for row in rows:
        chunk_id, distance, start_line, end_line, text, path = row
        if file_filter and not Path(path).match(file_filter):
            continue
        results.append(SearchResult(
            chunk_id=chunk_id,
            file_path=path,
            start_line=start_line,
            end_line=end_line,
            text=text,
            score=1.0 / (1.0 + float(distance)),
        ))
    return results


def _keyword_search(
    conn: sqlite3.Connection,
    query: str,
    top_k: int,
    file_filter: str | None,
) -> list[SearchResult]:
    if not query.strip():
        return []

    rows = conn.execute(
        """
        SELECT c.id, c.start_line, c.end_line, c.text, f.path, chunks_fts.rank
        FROM chunks_fts
        JOIN chunks c ON c.rowid = chunks_fts.rowid
        JOIN files  f ON f.id  = c.file_id
        WHERE chunks_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (query, top_k),
    ).fetchall()

    results: list[SearchResult] = []
    for row in rows:
        chunk_id, start_line, end_line, text, path, rank = row
        if file_filter and not Path(path).match(file_filter):
            continue
        results.append(SearchResult(
            chunk_id=chunk_id,
            file_path=path,
            start_line=start_line,
            end_line=end_line,
            text=text,
            score=float(-rank),
        ))
    return results
