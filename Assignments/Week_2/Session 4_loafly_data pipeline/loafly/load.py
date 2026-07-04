"""
load.py - one job: save each order's total to the orders API, safely.

gateway.save_to_orders_api is flaky (raises ConnectionError about 30% of
the time). save_order retries it a few times with a short wait before
giving up and logging an error, instead of letting the whole run crash.
"""
import logging
import time

from gateway import save_to_orders_api
from loafly.config import API_KEY, SETTINGS

logger = logging.getLogger(__name__)

if API_KEY == "demo-key":
    logger.warning("LOAFLY_API_KEY not set in environment; using demo-key fallback")


def save_order(order_id, total, retries=None, wait_seconds=None):
    """Try to save one order, retrying on ConnectionError."""
    retries = SETTINGS["retry_attempts"] if retries is None else retries
    wait_seconds = SETTINGS["retry_wait_seconds"] if wait_seconds is None else wait_seconds

    for attempt in range(1, retries + 1):
        try:
            result = save_to_orders_api(order_id, total)
            logger.info("Saved order %s on attempt %d/%d", order_id, attempt, retries)
            return result
        except ConnectionError as e:
            logger.warning(
                "Attempt %d/%d failed for order %s: %s", attempt, retries, order_id, e
            )
            if attempt < retries:
                time.sleep(wait_seconds)

    logger.error("Giving up on order %s after %d attempts", order_id, retries)
    return None


def load_orders(discounted_orders):
    """Save every (order, total) pair, returning (order_id, result) pairs."""
    results = []
    for order, total in discounted_orders:
        result = save_order(order.order_id, total)
        results.append((order.order_id, result))
    return results
