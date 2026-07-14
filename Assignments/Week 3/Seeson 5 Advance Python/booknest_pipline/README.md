# Booknest — Advanced Python Data Processing (Session 5 Revision)

Six small, independent scripts covering the whole session: APIs, pagination
and incremental loads, sync vs async, serial vs parallel, file streaming and
memory optimisation, and pytest.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac / Linux

pip install requests pandas pytest
```

`data/sales.csv` and `data/offline_books.json` must stay in a `data/`
subfolder next to the scripts.

## How to run each script

| Task | File | Command | Needs internet? |
|------|------|---------|------------------|
| 1. APIs | `get_books.py` | `python get_books.py` | Yes (falls back to `data/offline_books.json` if unreachable) |
| 2. Pagination + incremental | `ingestion.py` | `python ingestion.py` | Yes (same fallback) |
| 3. Sync vs async | `sync_async.py` | `python sync_async.py` | Yes |
| 4. Serial vs parallel | `serial_parallel.py` | `python serial_parallel.py` | No |
| 5. Streaming + memory | `streaming_memory.py` | `python streaming_memory.py` | No |
| 6. Testing | `test_pricing.py` | `pytest -v` | No |

## Notes

- Tasks 1–3 call the free Open Library API (no key needed). If the network
  is unavailable, task 1 and 2 automatically fall back to the local sample
  in `data/offline_books.json` so the script still runs end to end.
- Task 4's `score_genre` function is defined at module (top) level on
  purpose — `ProcessPoolExecutor` needs to pickle the function to send it
  to worker processes, which only works for top-level functions.
- Task 5 never loads `sales.csv` fully into memory; it aggregates revenue
  chunk by chunk with `pd.read_csv(chunksize=50_000)`.
- Task 6 covers the normal cases plus edge cases: a zero discount, a full
  (100%) discount, and the delivery-fee free-shipping boundary.
