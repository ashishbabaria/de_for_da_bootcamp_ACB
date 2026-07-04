"""
extract.py - one job: read the day's raw order-item rows off disk.
No cleaning, no discounting, no saving happens here.
"""
import csv
import logging

from loafly.config import SETTINGS

logger = logging.getLogger(__name__)


def read_raw_rows(input_file=None):
    """Read raw_orders.csv into a list of dict rows (one row per item)."""
    path = input_file or SETTINGS["input_file"]
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    logger.info("Extracted %d raw item rows from %s", len(rows), path)
    return rows
