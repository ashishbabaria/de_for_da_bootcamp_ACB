"""
load.py  -  save the orders OUT  (the "L" in ETL).

This module shows three production ideas in one place:
    - LOGGING : we record what happened
    - RETRY   : saving can fail, so we try again a few times
    - SECRETS : the database password comes from the environment, never code
"""

import os
import time
import random
import logging

from online_store.config import SETTINGS


def get_db_password():
    """SECRETS: never hard-code a password. Read it from the environment.

    On your laptop you would put DB_PASSWORD in a .env file (and never commit
    it). In production a secrets manager provides it. Here we fall back to a
    demo value so the program runs.
    """
    return os.getenv("DB_PASSWORD", "demo-password")


def save_order(order):
    """RETRY: saving can fail (a network blip). Try a few times, then give up."""
    password = get_db_password()                 # used to connect, never printed
    retries = SETTINGS["max_save_retries"]
    for attempt in range(1, retries + 1):
        if random.random() < 0.7:                # pretend it works 70% of the time
            logging.info("Saved order %s for %s", order.order_id, order.customer)
            return True
        logging.warning("Save failed for order %s (attempt %s), trying again",
                        order.order_id, attempt)
        time.sleep(0.5)                          # wait a moment, then try again
    logging.error("Gave up saving order %s", order.order_id)
    return False
