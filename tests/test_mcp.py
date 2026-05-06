from __future__ import annotations

import networkx as nx
import pytest
from unittest.mock import MagicMock

from cuddly.graph.traversal import graph_summary, subgraph, find_node


def _make_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node("entity:1", name="my_func", kind="function", file_path="app.py", line=5, qualified_name="my_func")
    g.add_node("entity:2", name="helper", kind="function", file_path="utils.py", line=1, qualified_name="helper")
    g.add_edge("entity:1", "entity:2", kind="CALLS")
    return g


def test_cuddly_graph_tool_found() -> None:
    from cuddly.mcp.tools import register_tools
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    graph = _make_graph()

    register_tools(
        mcp,
        get_conn=MagicMock(),
        get_embedder=MagicMock(),
        get_graph=lambda: graph,
    )

    # Invoke the graph tool directly through its registered function
    # FastMCP stores tools; we test the logic indirectly via traversal
    sg = subgraph(graph, "my_func", depth=1)
    assert sg.number_of_nodes() == 2
    summary = graph_summary(sg)
    assert "Nodes: 2" in summary


def test_cuddly_summary_empty_db(tmp_db) -> None:
    from cuddly.config import get_config
    from cuddly.mcp.tools import register_tools
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    graph = nx.DiGraph()

    register_tools(
        mcp,
        get_conn=lambda: tmp_db,
        get_embedder=MagicMock(),
        get_graph=lambda: graph,
    )

    # Directly call the inner logic that cuddly_summary uses
    conn = tmp_db
    file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    assert file_count == 0
    assert chunk_count == 0
