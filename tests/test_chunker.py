from __future__ import annotations

from pathlib import Path

import pytest

from cuddly.indexer.chunker import chunk_file
from cuddly.indexer.parser import parse_file


def test_chunk_entity_function(tmp_path: Path) -> None:
    code = '''\
def hello(name: str) -> str:
    return f"Hello, {name}!"

def goodbye(name: str) -> str:
    return f"Bye, {name}!"
'''
    py = tmp_path / "test.py"
    py.write_text(code)
    entities = parse_file(py)
    chunks = chunk_file(py, entities)

    kinds = {c.kind for c in chunks}
    assert "entity_function" in kinds
    texts = "\n".join(c.text for c in chunks)
    assert "hello" in texts
    assert "goodbye" in texts


def test_chunk_entity_class(tmp_path: Path) -> None:
    code = '''\
class Greeter:
    def greet(self, name: str) -> str:
        return f"Hi, {name}!"
'''
    py = tmp_path / "test.py"
    py.write_text(code)
    entities = parse_file(py)
    chunks = chunk_file(py, entities)

    class_chunks = [c for c in chunks if c.kind == "entity_class"]
    assert len(class_chunks) >= 1
    assert "Greeter" in class_chunks[0].text


def test_chunk_window_fallback(tmp_path: Path) -> None:
    code = "x = 1\n" * 100
    py = tmp_path / "test.py"
    py.write_text(code)
    chunks = chunk_file(py, [])

    assert len(chunks) > 0
    assert all(c.kind == "window" for c in chunks)
    assert all(c.token_count > 0 for c in chunks)


def test_chunk_empty_file(tmp_path: Path) -> None:
    py = tmp_path / "empty.py"
    py.write_text("")
    assert chunk_file(py, []) == []


def test_chunk_sample_project(sample_project: Path) -> None:
    utils = sample_project / "utils.py"
    entities = parse_file(utils)
    chunks = chunk_file(utils, entities)
    assert len(chunks) > 0
    func_names = {e.name for e in entities if e.kind == "function"}
    assert "slugify" in func_names
    assert "paginate" in func_names
