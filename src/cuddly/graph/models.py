from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Node:
    id: str
    name: str
    kind: str  # function | class | import | file
    file_path: str
    line: int
    qualified_name: str = ""

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Edge:
    src: str  # node id
    dst: str  # node id
    kind: str  # CALLS | IMPORTS | INHERITS | DEFINES
