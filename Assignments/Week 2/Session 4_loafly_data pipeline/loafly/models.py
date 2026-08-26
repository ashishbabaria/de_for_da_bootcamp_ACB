"""
models.py - the Order class. Orders hold their own data (id, customer,
items) and their own behaviour (adding an item, computing the total).
Nothing outside this class should sum item prices by hand.
"""


class Order:
    def __init__(self, order_id, customer):
        self.order_id = order_id
        self.customer = customer
        self.items = []  # list of (item_name, price) tuples

    def add_item(self, item_name, price):
        self.items.append((item_name, price))

    def total(self):
        return sum(price for _, price in self.items)

    def __repr__(self):
        return (
            f"Order(order_id={self.order_id!r}, customer={self.customer!r}, "
            f"items={len(self.items)}, total={self.total():.2f})"
        )
