from __future__ import annotations


def slugify(text: str) -> str:
    return text.lower().replace(" ", "-")


def paginate(items: list, page: int, per_page: int = 10) -> list:
    start = (page - 1) * per_page
    return items[start : start + per_page]


def flatten(nested: list[list]) -> list:
    return [item for sub in nested for item in sub]
