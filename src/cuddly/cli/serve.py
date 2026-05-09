from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def serve(
    mcp: bool = typer.Option(False, "--mcp", help="Run as MCP server over stdio"),
    port: int = typer.Option(8000, "--port", "-p", help="Port for the web server (Phase 2)"),
) -> None:
    """Start the MCP server or web UI."""
    if mcp:
        import logging
        from cuddly.config import setup_logging
        setup_logging(json_logs=True)
        for noisy in ("httpx", "httpcore", "sentence_transformers", "huggingface_hub"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
        from cuddly.mcp.server import run_mcp
        run_mcp()
    else:
        console.print("[yellow]Web server not implemented yet (Phase 2).[/yellow]")
        console.print("To start the MCP server: [bold]cuddly serve --mcp[/bold]")
        raise typer.Exit(1)
