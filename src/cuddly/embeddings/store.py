from __future__ import annotations

import sqlite3

import numpy as np


def upsert_vectors(conn: sqlite3.Connection, chunk_ids: list[int], vectors: np.ndarray) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO vec_chunks(chunk_id, embedding) VALUES (?, ?)",
        [(cid, v.astype(np.float32).tobytes()) for cid, v in zip(chunk_ids, vectors)],
    )
    conn.commit()


def delete_vectors_for_file(conn: sqlite3.Connection, file_id: int) -> None:
    chunk_ids = [r[0] for r in conn.execute("SELECT id FROM chunks WHERE file_id = ?", (file_id,))]
    if not chunk_ids:
        return
    placeholders = ",".join("?" * len(chunk_ids))
    conn.execute(f"DELETE FROM vec_chunks WHERE chunk_id IN ({placeholders})", chunk_ids)
    conn.commit()
