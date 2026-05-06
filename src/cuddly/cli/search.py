from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

app = typer.Typer(help="Search the codebase semantically.")
console = Console()


@app.callback(invoke_without_command=True)
def search(
    query: str = typer.Argument(help="Natural language search query"),
    top_k: int = typer.Option(10, "--top-k", "-k", help="Number of results"),
    file_filter: Optional[str] = typer.Option(None, "--filter", "-f", help="Glob pattern to filter files"),
) -> None:
    from cuddly.db.connection import get_connection
    from cuddly.db.migrations import apply_migrations
    from cuddly.db.schema import create_schema
    from cuddly.embeddings.embedder import Embedder
    from cuddly.embeddings.search import semantic_search

    conn = get_connection()
    create_schema(conn)
    apply_migrations(conn)
    embedder = Embedder()

    results = semantic_search(conn, embedder, query, top_k=top_k, file_filter=file_filter)

    if not results:
        console.print(f"[yellow]No results for:[/yellow] {query}")
        raise typer.Exit(1)

    console.print(f"\n[bold]Search:[/bold] {query} — {len(results)} result(s)\n")
    for i, r in enumerate(results, 1):
        ext = r.file_path.rsplit(".", 1)[-1] if "." in r.file_path else "text"
        console.print(
            f"[dim]{i}.[/dim] [cyan]{r.file_path}[/cyan]"
            f":[yellow]{r.start_line}[/yellow]–[yellow]{r.end_line}[/yellow]"
            f"  [dim]score={r.score:.3f}[/dim]"
        )
        console.print(Panel(Syntax(r.text, ext, line_numbers=True, start_line=r.start_line), expand=False))
