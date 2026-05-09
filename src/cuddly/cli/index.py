from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def index(
    path: Optional[Path] = typer.Argument(default=None, help="Project root to index (default: cwd)"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-index all files, ignoring cached hashes"),
    file: Optional[Path] = typer.Option(None, "--file", help="Index a single file"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all output"),
) -> None:
    """Index a project or a single file."""
    import logging
    from cuddly.config import get_config, setup_logging
    from cuddly.db.connection import get_connection
    from cuddly.db.migrations import apply_migrations
    from cuddly.db.schema import create_schema
    from cuddly.embeddings.embedder import Embedder
    from cuddly.graph.builder import build_graph, build_import_edges, save_graph
    from cuddly.indexer.indexer import index_file, index_project

    if quiet:
        logging.disable(logging.CRITICAL)
    else:
        setup_logging()
        # Suppress noisy third-party loggers
        for noisy in ("httpx", "httpcore", "sentence_transformers", "huggingface_hub"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    config = get_config()
    conn = get_connection()
    create_schema(conn)
    apply_migrations(conn)
    embedder = Embedder()

    if file:
        result = index_file(file, conn, embedder, force=force)
        if not quiet:
            status = "skipped (unchanged)" if result.skipped else f"{result.chunks_added} chunks"
            console.print(f"[green]{file}[/green]: {status}")
    else:
        root = path or config.project_root
        stats = index_project(root, conn, embedder, force=force)
        if not quiet:
            console.print(
                f"[green]Done.[/green] Indexed: {stats['indexed']} | "
                f"Skipped: {stats['skipped']} | Errors: {stats['errors']}"
            )
        if not quiet:
            console.print("Building knowledge graph...")
        build_import_edges(conn)
        g = build_graph(conn)
        graph_path = config.db_path.parent / "graph.json"
        save_graph(g, graph_path)
        if not quiet:
            console.print(
                f"[green]Graph saved:[/green] {g.number_of_nodes()} nodes, {g.number_of_edges()} edges"
            )
