from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import structlog
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from cuddly.embeddings.embedder import Embedder
from cuddly.embeddings.store import delete_vectors_for_file, upsert_vectors
from cuddly.indexer.chunker import chunk_file
from cuddly.indexer.parser import parse_file
from cuddly.indexer.walker import walk

log = structlog.get_logger()


@dataclass
class IndexResult:
    path: Path
    chunks_added: int
    skipped: bool


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cleanup_file(conn: sqlite3.Connection, file_id: int) -> None:
    chunk_ids = [r[0] for r in conn.execute("SELECT id FROM chunks WHERE file_id = ?", (file_id,))]
    if chunk_ids:
        placeholders = ",".join("?" * len(chunk_ids))
        conn.execute(f"DELETE FROM chunks_fts WHERE rowid IN ({placeholders})", chunk_ids)
        conn.execute(f"DELETE FROM vec_chunks WHERE chunk_id IN ({placeholders})", chunk_ids)
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))  # cascades to chunks → entities → edges


def index_file(
    path: Path,
    conn: sqlite3.Connection,
    embedder: Embedder,
    *,
    force: bool = False,
) -> IndexResult:
    path_str = str(path)
    current_hash = _file_hash(path)

    existing = conn.execute("SELECT id, content_hash FROM files WHERE path = ?", (path_str,)).fetchone()
    if not force and existing and existing["content_hash"] == current_hash:
        return IndexResult(path=path, chunks_added=0, skipped=True)

    if existing:
        _cleanup_file(conn, existing["id"])

    cursor = conn.execute(
        "INSERT INTO files (path, mtime, content_hash, indexed_at) VALUES (?, ?, ?, ?)",
        (path_str, path.stat().st_mtime, current_hash, time.time()),
    )
    file_id = cursor.lastrowid
    assert file_id is not None

    entities = parse_file(path)
    chunks = chunk_file(path, entities)

    if not chunks:
        conn.commit()
        return IndexResult(path=path, chunks_added=0, skipped=False)

    chunk_ids: list[int] = []
    for chunk in chunks:
        cur = conn.execute(
            "INSERT INTO chunks (file_id, kind, start_line, end_line, text, token_count) VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, chunk.kind, chunk.start_line, chunk.end_line, chunk.text, chunk.token_count),
        )
        cid = cur.lastrowid
        assert cid is not None
        conn.execute("INSERT INTO chunks_fts(rowid, text) VALUES (?, ?)", (cid, chunk.text))
        chunk_ids.append(cid)

    # Insert entities, pinning each to the first chunk that contains it
    for entity in entities:
        for cid, chunk in zip(chunk_ids, chunks):
            if chunk.start_line <= entity.start_line <= chunk.end_line:
                conn.execute(
                    "INSERT INTO entities (chunk_id, name, kind, qualified_name) VALUES (?, ?, ?, ?)",
                    (cid, entity.name, entity.kind, entity.qualified_name),
                )
                break

    conn.commit()

    # Embed after commit so DB is consistent even if embedding fails
    vectors = embedder.embed([c.text for c in chunks])
    upsert_vectors(conn, chunk_ids, vectors)

    log.info("indexed", path=path_str, chunks=len(chunks))
    return IndexResult(path=path, chunks_added=len(chunks), skipped=False)


def index_project(
    root: Path,
    conn: sqlite3.Connection,
    embedder: Embedder,
    *,
    force: bool = False,
) -> dict[str, int]:
    files = list(walk(root))
    stats = {"indexed": 0, "skipped": 0, "errors": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task(f"Indexing {root.name}...", total=len(files))
        for path in files:
            try:
                result = index_file(path, conn, embedder, force=force)
                if result.skipped:
                    stats["skipped"] += 1
                else:
                    stats["indexed"] += 1
            except Exception as exc:
                stats["errors"] += 1
                log.warning("index_error", path=str(path), error=str(exc))
            progress.advance(task)

    return stats
