"""
load.py - save the orders OUT  (the "L" in ETL).

Production patterns demonstrated here:
    LOGGING : every outcome (success, retry, give-up) gets a log line
    RETRY   : transient failures are retried with exponential backoff
    SECRETS : the DB password is read from the environment, never code
"""

import os
import time
import random
import logging
from typing import Optional

from online_store.config import SETTINGS
from online_store.models import Order


def get_db_password() -> str:
    """Read the DB password from the environment.

    Locally: set DB_PASSWORD in your shell or a .env file.
    Production: a secrets manager (Azure Key Vault, AWS Secrets Manager, etc.)
    injects the value into the process environment.

    Returns:
        The password string. Falls back to a demo value so the script runs
        without setup; remove the fallback in real production code.
    """
    return os.getenv("DB_PASSWORD", "demo-password")


def _attempt_save(order: Order, password: str) -> bool:
    """Simulate one save attempt. Replace this body with a real DB write.

    In production: open a connection using `password`, write the order rows
    in a transaction, commit, return True on success. Any exception from
    the driver propagates up to `save_order`, which decides whether to retry.

    Here: a coin flip based on config["save_success_rate"].
    """
    return random.random() < SETTINGS["save_success_rate"]


def save_order(order: Order) -> bool:
    """Save one order, retrying transient failures with exponential backoff.

    Args:
        order: the Order to persist.

    Returns:
        True if saved within `max_save_retries`, False if all attempts failed.
    """
    password = get_db_password()                 # read once per save
    retries: int = SETTINGS["max_save_retries"]
    base_wait: float = SETTINGS["retry_base_wait_seconds"]

    for attempt in range(1, retries + 1):
        if _attempt_save(order, password):
            logging.info("Saved order %s for %s (attempt %s)",
                         order.order_id, order.customer, attempt)
            return True

        if attempt < retries:
            wait = base_wait * (2 ** (attempt - 1))   # 0.5s, 1s, 2s, ...
            logging.warning(
                "Save failed for order %s (attempt %s/%s), retrying in %.1fs",
                order.order_id, attempt, retries, wait)
            time.sleep(wait)

    logging.error("Gave up saving order %s after %s attempts",
                  order.order_id, retries)
    return False
