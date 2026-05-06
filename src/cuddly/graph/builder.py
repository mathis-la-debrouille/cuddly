from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import networkx as nx


def build_graph(conn: sqlite3.Connection) -> nx.DiGraph:
    g = nx.DiGraph()

    rows = conn.execute("""
        SELECT e.id, e.name, e.kind, e.qualified_name, f.path, c.start_line
        FROM entities e
        JOIN chunks c ON c.id = e.chunk_id
        JOIN files  f ON f.id = c.file_id
    """).fetchall()

    for row in rows:
        eid, name, kind, qualified_name, path, line = row
        nid = f"entity:{eid}"
        g.add_node(nid, name=name, kind=kind, qualified_name=qualified_name, file_path=path, line=line)

    for src_id, dst_id, edge_type in conn.execute(
        "SELECT src_entity_id, dst_entity_id, edge_type FROM edges"
    ).fetchall():
        g.add_edge(f"entity:{src_id}", f"entity:{dst_id}", kind=edge_type)

    return g


def build_import_edges(conn: sqlite3.Connection) -> None:
    """Infer IMPORTS edges from import statements."""
    imports = conn.execute(
        "SELECT id, name FROM entities WHERE kind = 'import'"
    ).fetchall()

    for import_id, import_text in imports:
        target = _extract_import_target(import_text)
        if not target:
            continue
        targets = conn.execute(
            "SELECT id FROM entities WHERE name = ? AND kind IN ('function', 'class')",
            (target,),
        ).fetchall()
        for (target_id,) in targets:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO edges (src_entity_id, dst_entity_id, edge_type) VALUES (?, ?, ?)",
                    (import_id, target_id, "IMPORTS"),
                )
            except Exception:
                pass
    conn.commit()


def _extract_import_target(import_text: str) -> str | None:
    parts = import_text.strip().split()
    if not parts:
        return None
    if parts[0] == "from" and len(parts) >= 4 and parts[2] == "import":
        return parts[3].rstrip(",").rstrip(")")
    if parts[0] == "import" and len(parts) >= 2:
        return parts[1].rstrip(",").split(".")[0]
    return None


def graph_to_json(g: nx.DiGraph) -> dict:
    return {
        "nodes": [{"id": nid, **data} for nid, data in g.nodes(data=True)],
        "edges": [{"src": u, "dst": v, **data} for u, v, data in g.edges(data=True)],
    }


def json_to_graph(data: dict) -> nx.DiGraph:
    g = nx.DiGraph()
    for node in data["nodes"]:
        nid = node["id"]
        g.add_node(nid, **{k: v for k, v in node.items() if k != "id"})
    for edge in data["edges"]:
        g.add_edge(edge["src"], edge["dst"], **{k: v for k, v in edge.items() if k not in ("src", "dst")})
    return g


def save_graph(g: nx.DiGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph_to_json(g)))


def load_graph(path: Path) -> nx.DiGraph | None:
    if not path.exists():
        return None
    try:
        return json_to_graph(json.loads(path.read_text()))
    except Exception:
        return None
