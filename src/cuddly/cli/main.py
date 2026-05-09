from __future__ import annotations

import typer

app = typer.Typer(
    name="cuddly",
    help="Local knowledge graph for AI coding agents.",
    add_completion=False,
    no_args_is_help=True,
)

# Import commands after app is defined to avoid circular issues
from cuddly.cli.index import index  # noqa: E402
from cuddly.cli.search import search  # noqa: E402
from cuddly.cli.graph import graph  # noqa: E402
from cuddly.cli.serve import serve  # noqa: E402
from cuddly.cli.stats import stats  # noqa: E402

app.command("index")(index)
app.command("search")(search)
app.command("graph")(graph)
app.command("serve")(serve)
app.command("stats")(stats)
