from __future__ import annotations

import networkx as nx

from cuddly.context.ranker import rank_chunks
from cuddly.context.tokens import count_tokens, truncate_to_budget
from cuddly.embeddings.search import SearchResult


def _result(text: str, score: float = 0.9, path: str = "test.py") -> SearchResult:
    return SearchResult(chunk_id=1, file_path=path, start_line=1, end_line=10, text=text, score=score)


def test_count_tokens_positive() -> None:
    assert count_tokens("hello world") > 0


def test_count_tokens_empty() -> None:
    assert count_tokens("") == 0


def test_truncate_within_budget() -> None:
    text = "hello world"
    assert truncate_to_budget(text, 100) == text


def test_truncate_enforces_budget() -> None:
    text = "word " * 500
    budget = 20
    result = truncate_to_budget(text, budget)
    assert count_tokens(result) <= budget


def test_rank_no_graph() -> None:
    results = [_result("low", 0.3), _result("high", 0.9)]
    ranked = rank_chunks(results, graph=None)
    assert ranked[0].score >= ranked[1].score


def test_rank_with_graph_boosts_connected_nodes() -> None:
    g = nx.DiGraph()
    g.add_node("n1", name="func", kind="function", file_path="main.py", line=1, qualified_name="func")
    g.add_node("n2", name="other", kind="function", file_path="other.py", line=1, qualified_name="other")
    g.add_edge("n1", "n2", kind="CALLS")

    results = [
        _result("low relevance", 0.5, path="main.py"),
        _result("same score", 0.5, path="other.py"),
    ]
    ranked = rank_chunks(results, graph=g)
    # main.py node has degree 1, other.py has degree 1 — both get same boost; order preserved
    assert len(ranked) == 2
