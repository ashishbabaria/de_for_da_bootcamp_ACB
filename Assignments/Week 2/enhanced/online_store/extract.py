"""
extract.py - pull raw orders IN  (the "E" in ETL).

In production this would read from a database, file, or API. The function
boundary stays the same - callers just see "give me a list of raw orders" -
so the rest of the pipeline does not change when the source does.

The demo data here is intentional: messy text prices and one broken row,
so transform.py has something to clean and something to fail on.
"""

from typing import List, Dict, Any


def fetch_todays_orders() -> List[Dict[str, Any]]:
    """Return today's raw orders, in the shape downstream code expects.

    Each order is a dict with:
        id:       int       - unique order id
        customer: str       - customer name
        items:    list of (item_name, price_as_text) tuples

    Notes for the demo:
        - Prices are strings with commas, on purpose - to exercise cleaning.
        - Order 103 has a None price - to exercise the exception handler.

    Returns:
        A list of raw order dicts.
    """
    return [
        {"id": 101, "customer": "Asha",  "items": [("Shoes", "2,499"), ("Socks", "199")]},
        {"id": 102, "customer": "Ravi",  "items": [("Phone", "15,999")]},
        {"id": 103, "customer": "Meena", "items": [("Bag", None)]},   # broken: no price
    ]
