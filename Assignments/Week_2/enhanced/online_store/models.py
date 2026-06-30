"""
models.py - domain objects used across the package.

Currently just the Order class. As the package grows, Customer, Invoice,
Refund, etc. would live here too - one file for the "nouns" of the system.
"""

from typing import List, Tuple


class Order:
    """A customer order: who placed it, what was bought, what it totals.

    Attributes:
        order_id: unique identifier for the order
        customer: customer name (in production: usually a customer_id)
        items:    list of (item_name, price) tuples on the order
    """

    def __init__(self, order_id: int, customer: str) -> None:
        self.order_id: int = order_id
        self.customer: str = customer
        self.items: List[Tuple[str, float]] = []

    def add_item(self, name: str, price: float) -> None:
        """Attach one line item to the order."""
        self.items.append((name, price))

    def total(self) -> float:
        """Sum every item's price. Empty order returns 0.0."""
        return sum(price for _, price in self.items)

    def item_count(self) -> int:
        """How many line items are on this order."""
        return len(self.items)

    def __repr__(self) -> str:
        """Useful when logging or debugging - shows what's inside the object."""
        return (
            f"Order(id={self.order_id}, customer={self.customer!r}, "
            f"items={self.item_count()}, total={self.total():.2f})"
        )
