from __future__ import annotations

import tiktoken

_enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def truncate_to_budget(text: str, budget: int) -> str:
    tokens = _enc.encode(text)
    if len(tokens) <= budget:
        return text
    return _enc.decode(tokens[:budget])
