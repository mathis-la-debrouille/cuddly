from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

import networkx as nx

from cuddly.context.ranker import rank_chunks
from cuddly.context.tokens import count_tokens, truncate_to_budget
from cuddly.embeddings.embedder import Embedder
from cuddly.embeddings.search import SearchResult, semantic_search
from cuddly.graph.traversal import graph_summary, subgraph


@dataclass
class ContextResult:
    chunks: list[SearchResult] = field(default_factory=list)
    graph_summary: str | None = None
    tokens_used: int = 0


def assemble_context(
    query: str,
    token_budget: int,
    conn: sqlite3.Connection,
    embedder: Embedder,
    graph: nx.DiGraph | None = None,
    include_graph: bool = True,
) -> ContextResult:
    graph_budget = min(500, token_budget // 8) if include_graph and graph else 0
    content_budget = token_budget - graph_budget

    candidates = semantic_search(conn, embedder, query, top_k=30)
    ranked = rank_chunks(candidates, graph)

    selected: list[SearchResult] = []
    tokens_used = 0

    for result in ranked:
        chunk_tokens = count_tokens(result.text)
        if tokens_used + chunk_tokens <= content_budget:
            selected.append(result)
            tokens_used += chunk_tokens
        elif not selected:
            truncated = truncate_to_budget(result.text, content_budget)
            selected.append(SearchResult(
                chunk_id=result.chunk_id,
                file_path=result.file_path,
                start_line=result.start_line,
                end_line=result.end_line,
                text=truncated,
                score=result.score,
            ))
            tokens_used += count_tokens(truncated)
            break

    graph_text: str | None = None
    if include_graph and graph and selected and graph.number_of_nodes() > 0:
        top_path = selected[0].file_path
        file_nodes = [nid for nid, d in graph.nodes(data=True) if d.get("file_path") == top_path]
        if file_nodes:
            top_name = graph.nodes[file_nodes[0]].get("name", "")
            sg = subgraph(graph, top_name, depth=1)
            summary = graph_summary(sg)
            graph_text = truncate_to_budget(summary, graph_budget)
            tokens_used += count_tokens(graph_text)

    return ContextResult(chunks=selected, graph_summary=graph_text, tokens_used=tokens_used)
