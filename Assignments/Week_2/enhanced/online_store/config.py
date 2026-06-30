"""
config.py - every tunable value the pipeline has, in one place.

The principle: code reads from SETTINGS, code never contains values directly.
To change behaviour, edit this file - never the logic files.

Layout note: settings are grouped by concern so the file scales as the
project grows. Adding a new setting? Put it in the group it belongs to,
or start a new group if none fits.
"""

SETTINGS = {
    # --- Business rules -------------------------------------------------
    "currency": "INR",
    "discount_percent": 10,        # festive discount applied to every order

    # --- Reliability ----------------------------------------------------
    "max_save_retries": 3,         # how many attempts before giving up
    "retry_base_wait_seconds": 0.5,  # first wait; doubles each attempt

    # --- Demo behaviour (would be removed in production) ----------------
    "save_success_rate": 0.7,      # simulated success probability in load.py
}
