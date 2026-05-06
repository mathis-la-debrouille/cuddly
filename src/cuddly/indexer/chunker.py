from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cuddly.indexer.languages.python import ParsedEntity

WINDOW_SIZE = 50
WINDOW_OVERLAP = 10


@dataclass
class Chunk:
    file_path: Path
    kind: str  # entity_function | entity_class | window
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed inclusive
    text: str
    token_count: int


def _count_tokens(text: str) -> int:
    # Imported lazily to avoid paying tiktoken startup cost at module import time
    from cuddly.context.tokens import count_tokens
    return count_tokens(text)


def _windows(lines: list[str], start: int, end: int, path: Path) -> list[Chunk]:
    """Sliding window chunks for a range of 0-indexed line indices [start, end)."""
    chunks: list[Chunk] = []
    i = start
    while i < end:
        window_end = min(i + WINDOW_SIZE, end)
        text = "\n".join(lines[i:window_end])
        if text.strip():
            chunks.append(Chunk(
                file_path=path,
                kind="window",
                start_line=i + 1,
                end_line=window_end,
                text=text,
                token_count=_count_tokens(text),
            ))
        if window_end == end:
            break
        i += WINDOW_SIZE - WINDOW_OVERLAP
    return chunks


def chunk_file(path: Path, entities: list[ParsedEntity]) -> list[Chunk]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError):
        return []

    lines = content.splitlines()
    if not lines:
        return []

    chunks: list[Chunk] = []
    covered: set[int] = set()

    # Entity-aligned chunks (function and class bodies)
    for entity in entities:
        if entity.kind not in ("function", "class"):
            continue
        start = entity.start_line - 1  # 0-indexed
        end = min(entity.end_line, len(lines))
        text = "\n".join(lines[start:end])
        chunks.append(Chunk(
            file_path=path,
            kind=f"entity_{entity.kind}",
            start_line=entity.start_line,
            end_line=end,
            text=text,
            token_count=_count_tokens(text),
        ))
        covered.update(range(start, end))

    # Sliding window for uncovered lines — find contiguous runs first
    uncovered = sorted(i for i in range(len(lines)) if i not in covered)
    if not uncovered:
        return chunks

    run_start = uncovered[0]
    prev = uncovered[0]
    for idx in uncovered[1:]:
        if idx != prev + 1:
            chunks.extend(_windows(lines, run_start, prev + 1, path))
            run_start = idx
        prev = idx
    chunks.extend(_windows(lines, run_start, prev + 1, path))

    return chunks
