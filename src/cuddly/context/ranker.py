from __future__ import annotations

import networkx as nx

from cuddly.embeddings.search import SearchResult


def rank_chunks(
    results: list[SearchResult],
    graph: nx.DiGraph | None = None,
) -> list[SearchResult]:
    if not graph or graph.number_of_nodes() == 0:
        return sorted(results, key=lambda r: r.score, reverse=True)

    degrees = dict(graph.degree())
    max_degree = max(degrees.values(), default=1) or 1

    scored: list[tuple[SearchResult, float]] = []
    for result in results:
        boost = 1.0
        for nid, data in graph.nodes(data=True):
            if data.get("file_path") == result.file_path:
                boost = 1.0 + (degrees.get(nid, 0) / max_degree) * 0.3
                break
        scored.append((result, result.score * boost))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in scored]
