from __future__ import annotations

from tests.fixtures.sample_project.models import Product, User
from tests.fixtures.sample_project.utils import paginate, slugify


def greet(user: User) -> str:
    return f"Hello, {user.display_name()}!"


def list_products(products: list[Product], page: int = 1) -> list[Product]:
    return paginate(products, page)


def product_slug(product: Product) -> str:
    return slugify(product.name)
