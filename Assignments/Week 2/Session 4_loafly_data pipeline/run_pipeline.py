"""
run_pipeline.py - orchestrates the Loafly pipeline: extract, then
transform, then load. Run with:

    python run_pipeline.py
"""
import logging

from loafly.config import SETTINGS, setup_logging
from loafly.extract import read_raw_rows
from loafly.load import load_orders
from loafly.transform import apply_discounts, build_orders


def main():
    setup_logging()
    logger = logging.getLogger("run_pipeline")
    logger.info("Starting Loafly pipeline")

    rows = read_raw_rows()
    orders = build_orders(rows)
    discounted = apply_discounts(orders)

    for order, total in discounted:
        logger.info(
            "Order %s (%s): %d item(s), total %.2f %s after discount",
            order.order_id, order.customer, len(order.items),
            total, SETTINGS["currency"],
        )

    results = load_orders(discounted)
    saved = sum(1 for _, result in results if result is not None)

    logger.info("Pipeline complete: %d/%d orders saved successfully", saved, len(results))


if __name__ == "__main__":
    main()
