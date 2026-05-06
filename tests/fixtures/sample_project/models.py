from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str

    def display_name(self) -> str:
        return f"{self.name} <{self.email}>"


@dataclass
class Product:
    id: int
    name: str
    price: float

    def discounted(self, pct: float) -> float:
        return self.price * (1 - pct / 100)
