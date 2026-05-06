from __future__ import annotations

import networkx as nx

from cuddly.graph.traversal import find_node, graph_summary, subgraph


def _make_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node("entity:1", name="foo", kind="function", file_path="main.py", line=1, qualified_name="foo")
    g.add_node("entity:2", name="bar", kind="function", file_path="main.py", line=10, qualified_name="bar")
    g.add_node("entity:3", name="Baz", kind="class", file_path="utils.py", line=1, qualified_name="Baz")
    g.add_edge("entity:1", "entity:2", kind="CALLS")
    g.add_edge("entity:2", "entity:3", kind="CALLS")
    return g


def test_find_node_exact() -> None:
    g = _make_graph()
    assert find_node(g, "foo") == "entity:1"
    assert find_node(g, "Baz") == "entity:3"


def test_find_node_fuzzy() -> None:
    g = _make_graph()
    result = find_node(g, "ba")  # matches "bar" or "Baz"
    assert result in ("entity:2", "entity:3")


def test_find_node_missing() -> None:
    g = _make_graph()
    assert find_node(g, "nonexistent") is None


def test_subgraph_depth_1() -> None:
    g = _make_graph()
    sg = subgraph(g, "foo", depth=1)
    assert "entity:1" in sg.nodes
    assert "entity:2" in sg.nodes
    assert "entity:3" not in sg.nodes


def test_subgraph_depth_2() -> None:
    g = _make_graph()
    sg = subgraph(g, "foo", depth=2)
    assert all(n in sg.nodes for n in ["entity:1", "entity:2", "entity:3"])


def test_subgraph_rel_filter() -> None:
    g = _make_graph()
    g.add_edge("entity:1", "entity:3", kind="IMPORTS")
    sg = subgraph(g, "foo", depth=1, rel_types=["IMPORTS"])
    assert "entity:3" in sg.nodes
    assert "entity:2" not in sg.nodes  # only CALLS edge, not IMPORTS


def test_subgraph_missing_symbol() -> None:
    g = _make_graph()
    sg = subgraph(g, "xyz", depth=2)
    assert sg.number_of_nodes() == 0


def test_graph_summary() -> None:
    g = _make_graph()
    summary = graph_summary(g)
    assert "Nodes: 3" in summary
    assert "Edges: 2" in summary


def test_graph_summary_empty() -> None:
    assert graph_summary(nx.DiGraph()) == "Empty graph."
