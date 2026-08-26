"""
config.py - single source of truth for every setting the pipeline needs.

Nothing outside this module should contain a magic number, a file path,
or the API key literal. Change a value here and the pipeline's behaviour
changes without touching extract/transform/load.
"""
import logging
import os

# project_root/loafly/config.py -> project_root/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(_THIS_DIR)

def _load_dotenv(path):
    """Minimal stdlib .env loader: reads KEY=VALUE lines into os.environ,
    without overwriting variables that are already set."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

_load_dotenv(os.path.join(PROJECT_DIR, ".env"))

SETTINGS = {
    "input_file": os.path.join(PROJECT_DIR, "raw_orders.csv"),
    "currency": "INR",
    "discount_percent": 10,
    "retry_attempts": 3,
    "retry_wait_seconds": 1,
    "log_file": os.path.join(PROJECT_DIR, "loafly.log"),
    "log_level": "INFO",
}

# The secret lives in the environment, never in this file. env.example
# documents the variable name; the real value goes in a git-ignored .env.
API_KEY = os.getenv("LOAFLY_API_KEY", "demo-key")


def setup_logging():
    """Configure logging once, at the level set in SETTINGS, to console + file."""
    level = getattr(logging, SETTINGS["log_level"].upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging() is ever called twice
    # (e.g. re-running in the same interactive session).
    if root_logger.handlers:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(SETTINGS["log_file"], encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
