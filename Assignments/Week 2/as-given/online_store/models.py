"""
models.py  -  the Order class (object oriented programming).

A class bundles DATA (attributes) and the ACTIONS on that data (methods)
into one tidy object. Here, one Order knows its customer, its items,
and how to total itself.
"""


class Order:
    def __init__(self, order_id, customer):
        self.order_id = order_id     # attribute (data)
        self.customer = customer     # attribute (data)
        self.items = []              # attribute (data): list of (name, price)

    def add_item(self, name, price):     # method (action)
        self.items.append((name, price))

    def total(self):                     # method (action)
        # add up the price of every item in this order
        running_total = 0
        for name, price in self.items:
            running_total = running_total + price
        return running_total
