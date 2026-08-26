# Loafly Order Pipeline

A small, production-ready refactor of `legacy_orders.py`: reads the day's
raw orders, cleans prices, applies a discount, and saves each order to
the orders API — with logging, error handling, and retry. Python
standard library only.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

cp env.example .env            # then edit .env with your real key
```

`requirements.txt` is present but empty — no third-party packages are
needed.

## Run

```bash
python run_pipeline.py
```

This runs extract → transform → load, prints progress to the console,
and writes the same log lines to `loafly.log`.

## Package layout

```
loafly/
    __init__.py
    config.py      # every setting (currency, discount %, file paths,
                    # retry count) lives here, plus logging setup and
                    # the API key read from the environment
    models.py       # the Order class: data + add_item()/total()
    extract.py      # reads raw_orders.csv into raw dict rows
    transform.py    # clean_price / apply_discount, and builds Order
                    # objects, skipping rows with a missing price
    load.py         # saves each order via gateway.save_to_orders_api,
                    # retrying on ConnectionError
run_pipeline.py      # orchestrates extract -> transform -> load
gateway.py           # provided orders-API client (do not edit)
raw_orders.csv        # the day's input data
env.example           # template for .env (real .env is git-ignored)
```

## Notes

- A blank `item_price` is treated as a missing price: that single item
  is skipped with a `WARNING` log line, the order and the rest of the
  run continue.
- `save_order()` retries a failed save up to `SETTINGS["retry_attempts"]`
  times (default 3), waiting `SETTINGS["retry_wait_seconds"]` between
  attempts, then logs an `ERROR` and moves on rather than crashing the
  pipeline.
- The real API key is never in the code. It's read via
  `os.getenv("LOAFLY_API_KEY")` in `loafly/config.py`, with a
  `demo-key` fallback for local runs without a `.env`.
