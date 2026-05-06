from __future__ import annotations

import networkx as nx


def find_node(g: nx.DiGraph, name: str) -> str | None:
    for nid, data in g.nodes(data=True):
        if data.get("name") == name or data.get("qualified_name") == name:
            return nid
    # Fuzzy: case-insensitive substring
    name_lower = name.lower()
    for nid, data in g.nodes(data=True):
        if name_lower in data.get("name", "").lower():
            return nid
    return None


def subgraph(
    g: nx.DiGraph,
    symbol: str,
    depth: int = 2,
    rel_types: list[str] | None = None,
) -> nx.DiGraph:
    root_id = find_node(g, symbol)
    if root_id is None:
        return nx.DiGraph()

    visited: set[str] = {root_id}
    frontier: set[str] = {root_id}

    for _ in range(depth):
        next_frontier: set[str] = set()
        for nid in frontier:
            neighbors = list(g.predecessors(nid)) + list(g.successors(nid))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                if rel_types is not None:
                    edge_data = g.get_edge_data(nid, neighbor) or g.get_edge_data(neighbor, nid) or {}
                    if edge_data.get("kind") not in rel_types:
                        continue
                next_frontier.add(neighbor)
        visited |= next_frontier
        frontier = next_frontier

    return g.subgraph(visited).copy()


def graph_summary(g: nx.DiGraph) -> str:
    if g.number_of_nodes() == 0:
        return "Empty graph."

    lines = [f"Nodes: {g.number_of_nodes()}, Edges: {g.number_of_edges()}"]

    by_degree = sorted(g.degree(), key=lambda x: x[1], reverse=True)[:5]
    for nid, degree in by_degree:
        data = g.nodes[nid]
        lines.append(f"  {data.get('name', nid)} ({data.get('kind', '?')}) — degree {degree}")

    return "\n".join(lines)
