from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(help="Start the MCP server or web UI.")
console = Console()


@app.callback(invoke_without_command=True)
def serve(
    mcp: bool = typer.Option(False, "--mcp", help="Run as MCP server over stdio"),
    port: int = typer.Option(8000, "--port", "-p", help="Port for the web server (Phase 2)"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Also run the file watcher"),
) -> None:
    if mcp:
        from cuddly.config import setup_logging
        setup_logging(json_logs=True)  # JSON for MCP — no ANSI escapes over stdio
        from cuddly.mcp.server import run_mcp
        run_mcp()
    else:
        console.print("[yellow]Web server not implemented yet (Phase 2).[/yellow]")
        console.print("To start the MCP server: [bold]cuddly serve --mcp[/bold]")
        raise typer.Exit(1)
