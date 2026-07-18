# Session 7 — PySpark, Delta Lake & Lakehouse Engineering
**StayNest Assignment** · Codebasics Data Engineering Bootcamp

## Overview
Delta Lake and medallion-architecture assignment built on the StayNest hotel booking
dataset (`bookings`, `hotels`, `customers`, `bookings_updates`). Covers reading query
plans, forcing broadcast joins, Delta table history/time-travel/RESTORE, file
compaction with OPTIMIZE/ZORDER, a bronze → silver → gold pipeline, and an
incremental MERGE load.

Run on Databricks Free Edition (Serverless), catalog `workspace.default`, data in
Volume `/Volumes/workspace/default/staynest`.

## Files
| File | What it is |
|---|---|
| `StayNest/StayNest_S07_assignment_notebook.py` | Solved notebook, source-format (all 8 tasks) |
| `StayNest/screenshots/` | Cell outputs captured per task (see below) |

## Task-by-task summary

**Task 1 — Read the plan, force a broadcast join.**
`hotels_df` is only 200 rows (well under the ~10 MB auto-broadcast threshold), so
Catalyst already chose a `BroadcastHashJoin` for the plain join with no shuffle
(`Exchange`) in the plan. Forcing it with `broadcast(hotels_df.drop("city"))` produces
the identical join strategy — the small table is copied to every executor so the join
resolves locally, which is why no shuffle is needed.

**Task 2 — Create the Delta table and inspect history.**
Wrote `bookings_df` as a managed Delta table (`bookings_delta`), then ran an `UPDATE`
(pending → completed) and a `DELETE` (remove cancelled). `DESCRIBE HISTORY` shows
three commits: version 0 (WRITE), version 1 (UPDATE), version 2 (DELETE) — each DML
statement is its own atomic, versioned commit in the transaction log.

**Task 3 — Time travel and RESTORE.**
Read version 0 via `versionAsOf` and confirmed its row count matched the pre-UPDATE/
DELETE state. Ran `RESTORE TABLE ... TO VERSION AS OF 0`, confirmed the count matched
version 0 again. `DESCRIBE HISTORY` afterward shows a 4th commit (version 3,
`RESTORE`) — the UPDATE/DELETE commits are still in the log, RESTORE just added a new
commit rather than erasing history, so a forward-restore is still possible.

**Task 4 — OPTIMIZE and ZORDER.**
`OPTIMIZE` compacted the small files produced by the earlier writes/updates/deletes
into fewer, larger files. `OPTIMIZE ... ZORDER BY (city)` additionally co-locates rows
by city so filters on `city` can skip whole files. `city` is a good ZORDER candidate
(high cardinality, used in filters/group-bys); `status` would be a poor one (only 3
distinct values, so almost no data-skipping benefit).

**Task 5 — Bronze.**
Landed the raw bookings as-is into `bronze_bookings`, adding only an `ingested_at`
timestamp column. No filtering, no joins — bronze stays a faithful, replayable copy
of the source.

**Task 6 — Silver.**
Built `silver_bookings` from bronze: filtered to `status = 'completed'` and joined the
hotel dimension (dropping the duplicate `city` column from the hotel side) to add
`hotel_name`, `category`, and `star_rating`.

**Task 7 — Gold.**
Aggregated `gold_city_revenue` from silver: booking count and total revenue per city,
ordered by revenue descending — a business-ready table for a city-performance
dashboard.

**Task 8 — Incremental MERGE.**
Merged `bookings_updates` (150 changed + 50 new bookings) into `bookings_delta` in a
single `MERGE INTO` statement — matched `booking_id`s updated, unmatched ones
inserted. Row count grew from 12,000 to 12,050, confirming exactly the 50 new rows
landed and the 150 existing rows were updated in place rather than duplicated.

## How to reproduce
1. Open `StayNest/StayNest_S07_assignment_notebook.py` in the same Databricks workspace
   folder used for Session 6 (`Staynest Assignment`).
2. Confirm all four CSVs are in the Volume: `bookings.csv`, `hotels.csv`,
   `customers.csv`, `bookings_updates.csv`.
3. Attach to Serverless compute and **Run all**.

## Screenshots included
- Task 1 — both `.explain()` outputs
- Task 2 — `DESCRIBE HISTORY` after UPDATE/DELETE (versions 0–2)
- Task 3 — before/after/restored counts + updated history (version 3 = RESTORE)
- Task 4 — `OPTIMIZE ZORDER` output
- Task 7 — `gold_city_revenue` result table
- Task 8 — before/after MERGE counts + sample updated rows
