from __future__ import annotations

from pathlib import Path
from typing import Callable

import structlog

from cuddly.indexer.languages.python import ParsedEntity, parse_python

log = structlog.get_logger()

# Extension → parser function. Add new languages here.
_REGISTRY: dict[str, Callable[[Path], list[ParsedEntity]]] = {
    ".py": parse_python,
}


def parse_file(path: Path) -> list[ParsedEntity]:
    parser = _REGISTRY.get(path.suffix.lower())
    if parser is None:
        return []
    try:
        return parser(path)
    except Exception as exc:
        log.warning("parse_failed", path=str(path), error=str(exc))
        return []
