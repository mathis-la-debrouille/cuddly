from __future__ import annotations

import typer

from cuddly.cli.graph import app as graph_app
from cuddly.cli.index import app as index_app
from cuddly.cli.search import app as search_app
from cuddly.cli.serve import app as serve_app
from cuddly.cli.stats import app as stats_app

app = typer.Typer(
    name="cuddly",
    help="Local knowledge graph for AI coding agents.",
    add_completion=False,
    no_args_is_help=True,
)

app.add_typer(index_app, name="index")
app.add_typer(search_app, name="search")
app.add_typer(graph_app, name="graph")
app.add_typer(serve_app, name="serve")
app.add_typer(stats_app, name="stats")
