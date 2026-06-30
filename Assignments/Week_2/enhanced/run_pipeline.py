"""
run_pipeline.py - orchestrate one batch run of the order pipeline.

Flow:
    EXTRACT  -> fetch raw orders
    TRANSFORM-> build clean Order objects, apply discount
    LOAD     -> save each order (with retries)
    REPORT   -> print a summary at the end

Run:
    python run_pipeline.py
"""

import logging
import sys
from typing import Dict

from online_store.extract import fetch_todays_orders
from online_store.transform import build_order, apply_discount
from online_store.load import save_order
from online_store.config import SETTINGS


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)


def main() -> int:
    """Run one batch. Returns a Unix-style exit code: 0 success, 1 had failures."""
    logging.info("Starting today's order run")

    # Counters for the end-of-run summary.
    stats: Dict[str, int] = {
        "orders_seen": 0,
        "items_skipped": 0,
        "saves_ok": 0,
        "saves_failed": 0,
    }

    for raw in fetch_todays_orders():                       # EXTRACT
        stats["orders_seen"] += 1

        order, skipped = build_order(raw)                   # TRANSFORM
        stats["items_skipped"] += skipped

        subtotal = order.total()
        final = apply_discount(subtotal, SETTINGS["discount_percent"])
        logging.info(
            "Order %s | %s items | %s %.2f after %d%% discount",
            order.order_id, order.item_count(),
            SETTINGS["currency"], final, SETTINGS["discount_percent"],
        )

        if save_order(order):                               # LOAD
            stats["saves_ok"] += 1
        else:
            stats["saves_failed"] += 1

    # End-of-run summary - one line you can grep in tomorrow's logs.
    logging.info(
        "Run finished | orders=%s | items_skipped=%s | saved=%s | failed=%s",
        stats["orders_seen"], stats["items_skipped"],
        stats["saves_ok"], stats["saves_failed"],
    )

    # Non-zero exit code if any save failed - schedulers (cron, Airflow,
    # Fabric Pipelines) use the exit code to decide whether the job
    # succeeded or needs alerting.
    return 0 if stats["saves_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
