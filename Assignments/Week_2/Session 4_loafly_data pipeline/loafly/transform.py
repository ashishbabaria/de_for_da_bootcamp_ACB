"""
transform.py - one job: turn raw rows into Order objects with clean,
discounted totals.

- clean_price / apply_discount (Q1): the only place price math happens.
- build_orders (Q2): groups item rows into Order objects instead of a
  hand-rolled dict-of-lists total.
- Q5: a missing or unparsable price is logged as a warning and skipped,
  it never crashes the run.
"""
import logging

from loafly.config import SETTINGS
from loafly.models import Order

logger = logging.getLogger(__name__)


def clean_price(text):
    """Turn raw price text (e.g. ' 1,250', '330') into a float.

    Raises ValueError/AttributeError on missing or unparsable input,
    which callers are expected to catch.
    """
    cleaned = text.strip().replace(",", "")
    return float(cleaned)


def apply_discount(price, percent):
    """Return price after applying a percent discount."""
    return price - price * percent / 100


def build_orders(rows):
    """Group raw item rows into Order objects, skipping bad prices."""
    orders = {}
    skipped = 0

    for row in rows:
        order_id = row["order_id"]
        customer = row["customer"]
        item_name = row["item_name"]

        if order_id not in orders:
            orders[order_id] = Order(order_id=order_id, customer=customer)

        try:
            price = clean_price(row["item_price"])
        except (ValueError, AttributeError):
            skipped += 1
            logger.warning(
                "Skipping '%s' on order %s (%s): missing or invalid price %r",
                item_name, order_id, customer, row["item_price"],
            )
            continue
        finally:
            logger.debug("Finished processing item '%s' on order %s", item_name, order_id)

        orders[order_id].add_item(item_name, price)

    logger.info(
        "Built %d orders from %d raw rows (%d items skipped)",
        len(orders), len(rows), skipped,
    )
    return list(orders.values())


def apply_discounts(orders, percent=None):
    """Return a list of (order, discounted_total) pairs."""
    pct = SETTINGS["discount_percent"] if percent is None else percent
    return [(order, apply_discount(order.total(), pct)) for order in orders]
