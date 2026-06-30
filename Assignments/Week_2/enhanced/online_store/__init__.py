"""
online_store - a small batch ETL package for processing customer orders.

Pipeline shape:
    extract -> transform -> load

Modules:
    config.py     all settings in one place
    models.py     the Order domain class
    extract.py    pull raw orders IN          (the "E" in ETL)
    transform.py  clean and build Orders      (the "T" in ETL)
    load.py       save orders OUT             (the "L" in ETL)

Usage (from a runner script next to this package):
    from online_store.extract import fetch_todays_orders
    from online_store.transform import build_order, apply_discount
    from online_store.load import save_order
    from online_store.config import SETTINGS

The package is passive - importing it loads definitions but runs nothing.
A runner script (e.g. run_pipeline.py) orchestrates the actual work.
"""

__version__ = "0.1.0"
