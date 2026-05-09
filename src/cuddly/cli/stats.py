from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def stats() -> None:
    """Show indexing statistics."""
    from cuddly.config import get_config
    from cuddly.db.connection import get_connection
    from cuddly.db.schema import create_schema

    config = get_config()
    conn = get_connection()
    create_schema(conn)

    file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    vec_count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    kind_counts = dict(conn.execute("SELECT kind, COUNT(*) FROM entities GROUP BY kind").fetchall())
    db_size = config.db_path.stat().st_size if config.db_path.exists() else 0

    table = Table(title="cuddly stats", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Files indexed", str(file_count))
    table.add_row("Chunks", str(chunk_count))
    table.add_row("Entities", str(entity_count))
    for kind, count in sorted(kind_counts.items()):
        table.add_row(f"  {kind.capitalize()}s", str(count))
    coverage = f"{vec_count} / {chunk_count}" if chunk_count else "0 / 0"
    table.add_row("Embedding coverage", coverage)
    table.add_row("Database", str(config.db_path))
    table.add_row("DB size", f"{db_size / 1024 / 1024:.2f} MB")

    console.print(table)
