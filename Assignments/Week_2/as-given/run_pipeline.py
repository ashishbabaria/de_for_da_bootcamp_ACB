"""
run_pipeline.py  -  the AFTER (a clean package)

Runs the online_store package in order: EXTRACT -> TRANSFORM -> LOAD.
Keep this file NEXT TO the online_store/ folder.

Run:  python run_pipeline.py
"""

import logging

# Import only what we need, from the module it lives in.
from online_store.extract import fetch_todays_orders
from online_store.transform import build_order, apply_discount
from online_store.load import save_order
from online_store.config import SETTINGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")


def main():
    logging.info("Starting today's order run")
    for raw in fetch_todays_orders():                   # EXTRACT
        order = build_order(raw)                        # TRANSFORM
        subtotal = order.total()
        final = apply_discount(subtotal, SETTINGS["discount_percent"])
        logging.info("Order %s total: %s %.2f (after %d%% discount)",
                     order.order_id, SETTINGS["currency"], final,
                     SETTINGS["discount_percent"])
        save_order(order)                               # LOAD
    logging.info("Order run finished")


if __name__ == "__main__":
    main()
