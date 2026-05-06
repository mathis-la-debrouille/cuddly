from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser

PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


@dataclass
class ParsedEntity:
    name: str
    kind: str  # function | class | import
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed inclusive
    qualified_name: str


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _name(node: Node, source: bytes) -> str | None:
    n = node.child_by_field_name("name")
    return _text(n, source) if n else None


def _lines(node: Node) -> tuple[int, int]:
    return node.start_point[0] + 1, node.end_point[0] + 1


def _methods_of(class_node: Node, class_name: str, source: bytes) -> list[ParsedEntity]:
    entities: list[ParsedEntity] = []
    body = class_node.child_by_field_name("body")
    if not body:
        return entities
    for child in body.children:
        func_node = child
        if child.type == "decorated_definition":
            func_node = child.child_by_field_name("definition") or child
        if func_node.type == "function_definition":
            n = _name(func_node, source)
            if n:
                start, end = _lines(child)
                entities.append(ParsedEntity(
                    name=n,
                    kind="function",
                    start_line=start,
                    end_line=end,
                    qualified_name=f"{class_name}.{n}",
                ))
    return entities


def parse_python(path: Path) -> list[ParsedEntity]:
    source = path.read_bytes()
    tree = _parser.parse(source)
    entities: list[ParsedEntity] = []

    for node in tree.root_node.children:
        if node.type in ("function_definition", "decorated_definition"):
            func_node = node
            if node.type == "decorated_definition":
                func_node = node.child_by_field_name("definition") or node
            if func_node.type == "function_definition":
                n = _name(func_node, source)
                if n:
                    start, end = _lines(node)
                    entities.append(ParsedEntity(
                        name=n, kind="function",
                        start_line=start, end_line=end, qualified_name=n,
                    ))

        elif node.type == "class_definition":
            n = _name(node, source)
            if n:
                start, end = _lines(node)
                entities.append(ParsedEntity(
                    name=n, kind="class",
                    start_line=start, end_line=end, qualified_name=n,
                ))
                entities.extend(_methods_of(node, n, source))

        elif node.type in ("import_statement", "import_from_statement"):
            text = _text(node, source).split("\n")[0].strip()
            start, end = _lines(node)
            entities.append(ParsedEntity(
                name=text, kind="import",
                start_line=start, end_line=end, qualified_name=text,
            ))

    return entities
