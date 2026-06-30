# enhanced/

The same pipeline as `../as-given/`, with light production polish applied.
No new dependencies - everything is still the Python standard library.

## What changed vs. as-given

| Area | as-given | enhanced |
|---|---|---|
| Type hints | none | every function signature typed |
| Docstrings | one-liners | what / args / returns / examples |
| `Order.total()` | manual loop with running total | pythonic `sum(...)` |
| `Order` repr | `<Order object at 0x...>` | `Order(id=101, customer='Asha', items=2, total=2698.00)` |
| Bad price handling | generic `TypeError/AttributeError` catch | custom `BadPriceError` with a clear message |
| Retry strategy | fixed 0.5s wait | exponential backoff: 0.5s, 1s, 2s |
| Save abstraction | save logic inlined in `save_order` | private `_attempt_save` - swap one function to plug in a real DB |
| Skip tracking | none | items skipped are counted and reported |
| Exit code | always 0 | 0 on success, 1 if any save failed (schedulers use this) |
| End-of-run summary | none | one line: `orders=3 items_skipped=1 saved=3 failed=0` |
| Demo magic numbers | `0.7` baked into `load.py` | moved to `SETTINGS["save_success_rate"]` |

## Layout

```
enhanced/
    run_pipeline.py        the runner, now with a summary and exit code
    requirements.txt
    online_store/
        __init__.py        marks the package, exposes __version__
        config.py          settings grouped by concern
        models.py          Order with type hints, __repr__, item_count()
        extract.py         typed return value, documented schema
        transform.py       custom BadPriceError, build_order returns skip count
        load.py            exponential backoff, save attempt is swappable
```

## Run it

```bash
python run_pipeline.py
echo "Exit code: $?"      # 0 if all saves succeeded, 1 otherwise
```

## Why these changes specifically

Every change is one of:

1. **Self-documentation** - type hints and richer docstrings tell future-you
   (or a reviewer) what a function expects and returns, without reading the body.
2. **Better failure stories** - `BadPriceError("price 'abc' is not a number")`
   is more debuggable than a bare `ValueError`.
3. **Production hygiene** - exit codes, summaries, exponential backoff are
   what schedulers and on-call engineers actually rely on at 2am.
4. **Swap-ability** - separating `_attempt_save` from `save_order` means the
   retry logic stays the same when you replace the dummy save with a real
   database write. Same for `fetch_todays_orders` - body changes, signature stays.

None of these change *what* the pipeline does. They change how cleanly it
fails, reports, and adapts when something downstream changes.
