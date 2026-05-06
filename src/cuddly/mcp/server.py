from __future__ import annotations

import sqlite3

import networkx as nx
from mcp.server.fastmcp import FastMCP

from cuddly.embeddings.embedder import Embedder

mcp = FastMCP("cuddly", description="Local knowledge graph for AI coding agents")

_conn: sqlite3.Connection | None = None
_embedder: Embedder | None = None
_graph: nx.DiGraph | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        from cuddly.db.connection import get_connection
        from cuddly.db.migrations import apply_migrations
        from cuddly.db.schema import create_schema
        _conn = get_connection()
        create_schema(_conn)
        apply_migrations(_conn)
    return _conn


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def _get_graph() -> nx.DiGraph:
    global _graph
    if _graph is None:
        from cuddly.config import get_config
        from cuddly.graph.builder import build_graph, load_graph
        config = get_config()
        graph_path = config.db_path.parent / "graph.json"
        _graph = load_graph(graph_path) or build_graph(_get_conn())
    return _graph


# Register all tools
from cuddly.mcp.tools import register_tools  # noqa: E402
register_tools(mcp, _get_conn, _get_embedder, _get_graph)


def run_mcp() -> None:
    mcp.run(transport="stdio")
