"""
config.py  -  every setting in ONE place (config-driven design).

Instead of scattering numbers and names through the code, we keep them here.
Other modules just read from SETTINGS. To change behaviour, you change this
file, not the logic.
"""

SETTINGS = {
    "currency": "INR",
    "discount_percent": 10,    # festive discount applied to every order
    "max_save_retries": 3,     # how many times load.py retries a failed save
}
