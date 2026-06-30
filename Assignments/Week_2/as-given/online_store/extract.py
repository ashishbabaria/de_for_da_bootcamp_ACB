"""
extract.py  -  pull raw orders IN  (the "E" in ETL).

In a real project this would read from a database, a file, or an API.
To keep the demo simple and always runnable, we return a small hard-coded
list of today's orders. The prices are messy text on purpose, and one item
is missing its price, so transform.py can show how we clean and handle that.
"""


def fetch_todays_orders():
    """Return today's raw orders, exactly as they arrived."""
    return [
        {"id": 101, "customer": "Asha",  "items": [("Shoes", "2,499"), ("Socks", "199")]},
        {"id": 102, "customer": "Ravi",  "items": [("Phone", "15,999")]},
        {"id": 103, "customer": "Meena", "items": [("Bag", None)]},   # broken: no price
    ]
