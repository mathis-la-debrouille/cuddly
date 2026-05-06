from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

import structlog
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from cuddly.embeddings.embedder import Embedder

log = structlog.get_logger()


class _Handler(FileSystemEventHandler):
    def __init__(self, root: Path, conn: sqlite3.Connection, embedder: Embedder) -> None:
        self._root = root
        self._conn = conn
        self._embedder = embedder
        self._lock = threading.Lock()

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self._reindex(Path(event.src_path))

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self._reindex(Path(event.src_path))

    def on_deleted(self, event: FileDeletedEvent) -> None:
        if not event.is_directory:
            self._delete(Path(event.src_path))

    def _reindex(self, path: Path) -> None:
        from cuddly.indexer.indexer import index_file
        with self._lock:
            try:
                index_file(path, self._conn, self._embedder)
            except Exception as exc:
                log.warning("watcher_reindex_failed", path=str(path), error=str(exc))

    def _delete(self, path: Path) -> None:
        with self._lock:
            try:
                row = self._conn.execute("SELECT id FROM files WHERE path = ?", (str(path),)).fetchone()
                if not row:
                    return
                file_id = row["id"]
                chunk_ids = [
                    r[0] for r in self._conn.execute("SELECT id FROM chunks WHERE file_id = ?", (file_id,))
                ]
                if chunk_ids:
                    ph = ",".join("?" * len(chunk_ids))
                    self._conn.execute(f"DELETE FROM chunks_fts WHERE rowid IN ({ph})", chunk_ids)
                    self._conn.execute(f"DELETE FROM vec_chunks WHERE chunk_id IN ({ph})", chunk_ids)
                self._conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                self._conn.commit()
                log.info("watcher_deleted", path=str(path))
            except Exception as exc:
                log.warning("watcher_delete_failed", path=str(path), error=str(exc))


def watch(root: Path, conn: sqlite3.Connection, embedder: Embedder) -> None:
    handler = _Handler(root, conn, embedder)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()
    log.info("watcher_started", root=str(root))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
