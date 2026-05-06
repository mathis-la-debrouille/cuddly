from __future__ import annotations

from typing import Callable

import networkx as nx
from mcp.server.fastmcp import FastMCP

from cuddly.embeddings.search import semantic_search
from cuddly.graph.traversal import graph_summary, subgraph


def register_tools(
    mcp: FastMCP,
    get_conn: Callable,
    get_embedder: Callable,
    get_graph: Callable,
) -> None:

    @mcp.tool()
    def cuddly_search(
        query: str,
        top_k: int = 10,
        file_filter: str | None = None,
    ) -> str:
        """Search the codebase semantically. Returns relevant code chunks ranked by relevance."""
        results = semantic_search(get_conn(), get_embedder(), query, top_k=top_k, file_filter=file_filter)
        if not results:
            return f'No results found for: "{query}"'

        lines = [f'## Search Results for "{query}"\n']
        for i, r in enumerate(results, 1):
            lines.append(f"### {i}. {r.file_path}:{r.start_line}–{r.end_line} [score: {r.score:.3f}]")
            lines.append(f"```\n{r.text}\n```\n")
        return "\n".join(lines)

    @mcp.tool()
    def cuddly_context(
        task: str,
        token_budget: int = 8000,
        include_graph: bool = True,
    ) -> str:
        """Get optimized context for a coding task. Returns the most relevant code within a token budget."""
        from cuddly.context.optimizer import assemble_context
        result = assemble_context(task, token_budget, get_conn(), get_embedder(), get_graph(), include_graph)

        lines = [f'## Context for: "{task}"']
        lines.append(f"*Token budget: {token_budget} | Used: {result.tokens_used}*\n")
        for chunk in result.chunks:
            lines.append(f"### {chunk.file_path}:{chunk.start_line}–{chunk.end_line}")
            lines.append(f"```\n{chunk.text}\n```\n")
        if result.graph_summary:
            lines.append("### Graph Context")
            lines.append(result.graph_summary)
        return "\n".join(lines)

    @mcp.tool()
    def cuddly_graph(
        symbol: str,
        depth: int = 2,
        relationship_types: list[str] | None = None,
    ) -> str:
        """Get the subgraph around a symbol or file. Shows what's connected and how."""
        g = get_graph()
        sg = subgraph(g, symbol, depth=depth, rel_types=relationship_types)

        if sg.number_of_nodes() == 0:
            return f"Symbol not found in graph: {symbol}"

        lines = [f"## Subgraph: {symbol} (depth={depth})\n"]
        lines.append(graph_summary(sg))
        if sg.number_of_edges() > 0:
            lines.append("\n### Edges:")
            for u, v, data in sg.edges(data=True):
                u_name = sg.nodes[u].get("name", u)
                v_name = sg.nodes[v].get("name", v)
                lines.append(f"  {u_name} → {v_name} ({data.get('kind', '?')})")
        return "\n".join(lines)

    @mcp.tool()
    def cuddly_summary() -> str:
        """Get a high-level summary of the project structure and indexing coverage."""
        from cuddly.config import get_config
        conn = get_conn()
        config = get_config()

        file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        vec_count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
        kind_counts = dict(conn.execute("SELECT kind, COUNT(*) FROM entities GROUP BY kind").fetchall())
        db_size = config.db_path.stat().st_size if config.db_path.exists() else 0

        lines = [
            "## Project Summary",
            f"Files indexed: {file_count}",
            f"Chunks: {chunk_count}",
            f"Entities: {entity_count}",
        ]
        for kind, count in sorted(kind_counts.items()):
            lines.append(f"  {kind.capitalize()}s: {count}")
        coverage = f"{vec_count}/{chunk_count}" if chunk_count else "0/0"
        lines.append(f"Embedding coverage: {coverage} chunks")
        lines.append(f"Database size: {db_size / 1024 / 1024:.1f} MB")
        return "\n".join(lines)
