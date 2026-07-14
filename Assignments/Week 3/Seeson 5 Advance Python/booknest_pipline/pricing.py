"""
pricing.py  -  Booknest's small money functions (for the testing task).

These are the kind of functions that must never break silently, because a
wrong number here is real money. You will write pytest tests for them.
"""


def member_price(price, percent):
    """Booknest member discount.  member_price(1000, 10) -> 900.0"""
    return price - (price * percent / 100)


def add_gst(price, rate=5):
    """Add GST to a price.  add_gst(1000, 5) -> 1050.0  (books default to 5%)"""
    return price + (price * rate / 100)


def delivery_fee(order_total, free_above=500, flat=40):
    """Free delivery at or above the threshold, otherwise a flat fee.
    delivery_fee(600) -> 0    delivery_fee(300) -> 40"""
    if order_total >= free_above:
        return 0
    return flat


def loyalty_points(amount):
    """One point for every whole 100 spent.  loyalty_points(950) -> 9"""
    return int(amount // 100)
