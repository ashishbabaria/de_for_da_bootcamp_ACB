"""
transform.py - clean the data and build Order objects  (the "T" in ETL).

Three functions:
    clean_price()     str  -> float       (with a clear error if input is bad)
    apply_discount()  pure arithmetic, no I/O
    build_order()     dict -> Order       (skips bad items, never crashes)
"""

import logging
from typing import Any, Dict, Optional, Tuple

from online_store.models import Order


class BadPriceError(ValueError):
    """Raised when a price value cannot be turned into a number.

    Inherits from ValueError so callers that catch ValueError still work,
    while callers that want to be specific can catch BadPriceError.
    """


def clean_price(text: Optional[str]) -> float:
    """Turn a price written as text, like '1,250', into a number 1250.0.

    Args:
        text: the price as a string. May contain commas and whitespace.

    Returns:
        The price as a float.

    Raises:
        BadPriceError: if `text` is None, empty, or cannot be parsed.

    Examples:
        >>> clean_price("1,250")
        1250.0
        >>> clean_price(" 199 ")
        199.0
    """
    if text is None:
        raise BadPriceError("price is missing (None)")
    if not isinstance(text, str):
        raise BadPriceError(f"price must be a string, got {type(text).__name__}")
    cleaned = text.replace(",", "").strip()
    if cleaned == "":
        raise BadPriceError("price is empty after stripping")
    try:
        return float(cleaned)
    except ValueError as exc:
        raise BadPriceError(f"price {text!r} is not a number") from exc


def apply_discount(price: float, percent: float) -> float:
    """Take `percent` off `price`. Pure arithmetic, no side effects.

    Examples:
        >>> apply_discount(1000, 10)
        900.0
        >>> apply_discount(2500, 25)
        1875.0
    """
    return price - (price * percent / 100)


def build_order(raw: Dict[str, Any]) -> Tuple[Order, int]:
    """Turn one raw order dict into a clean Order object.

    Items with broken prices are logged and skipped - one bad item must
    not kill the whole order, and one bad order must not kill the run.

    Args:
        raw: a dict with keys 'id', 'customer', 'items'

    Returns:
        A tuple of (Order, items_skipped). The caller can use the
        skip count to summarise the run.
    """
    order = Order(raw["id"], raw["customer"])
    items_skipped = 0
    for name, price_text in raw["items"]:
        try:
            price = clean_price(price_text)
        except BadPriceError as exc:
            logging.warning("Order %s item '%s' skipped: %s",
                            raw["id"], name, exc)
            items_skipped += 1
            continue
        order.add_item(name, price)
    return order, items_skipped
