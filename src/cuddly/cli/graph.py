from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.tree import Tree

app = typer.Typer(help="Explore the knowledge graph around a symbol.")
console = Console()


@app.callback(invoke_without_command=True)
def graph(
    symbol: str = typer.Argument(help="Function, class, or module name"),
    depth: int = typer.Option(2, "--depth", "-d", help="Traversal depth"),
    rel: Optional[list[str]] = typer.Option(None, "--rel", help="Filter by edge type (e.g. IMPORTS CALLS)"),
) -> None:
    from cuddly.config import get_config
    from cuddly.graph.builder import load_graph
    from cuddly.graph.traversal import graph_summary, subgraph

    config = get_config()
    graph_path = config.db_path.parent / "graph.json"
    g = load_graph(graph_path)

    if g is None or g.number_of_nodes() == 0:
        console.print("[yellow]No graph found. Run [bold]cuddly index[/bold] first.[/yellow]")
        raise typer.Exit(1)

    sg = subgraph(g, symbol, depth=depth, rel_types=rel)
    if sg.number_of_nodes() == 0:
        console.print(f"[yellow]Symbol not found:[/yellow] {symbol}")
        raise typer.Exit(1)

    console.print(f"\n[bold]Subgraph:[/bold] {symbol} (depth={depth})")
    console.print(graph_summary(sg))

    if sg.number_of_edges() > 0:
        tree = Tree(f"[cyan]{symbol}[/cyan]")
        for u, v, data in sg.edges(data=True):
            u_name = sg.nodes[u].get("name", u)
            v_name = sg.nodes[v].get("name", v)
            tree.add(f"[green]{u_name}[/green] → [blue]{v_name}[/blue]  [dim]({data.get('kind', '?')})[/dim]")
        console.print(tree)
