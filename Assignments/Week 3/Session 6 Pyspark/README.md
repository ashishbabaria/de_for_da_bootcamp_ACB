# StayNest — Session 6 Assignment (PySpark Deep Dive)

Codebasics Data Engineering Bootcamp · Session 6 · PySpark on Databricks Free Edition.

## What this is
Eight tasks against three CSVs (`bookings`, `hotels`, `customers`) — read/inspect,
select/filter, derived columns, aggregations, joins (inner/left/left_anti/three-way),
Spark SQL + a window ranking, writing Parquet/Delta, and one chained pipeline.

## Data
| File | Rows | Grain |
|---|---|---|
| bookings.csv | 12,000 | one row per hotel booking |
| hotels.csv | 200 | one row per hotel |
| customers.csv | 2,000 | one row per customer |

## How to run
1. Databricks Free Edition → Catalog → create a Volume (e.g. `staynest`) under
   `workspace.default`.
2. Upload `bookings.csv`, `hotels.csv`, `customers.csv` into that Volume.
3. Import `StayNest_S06_assignment_notebook.py` (Databricks source format).
4. Set `BASE` in the first code cell to your Volume path, e.g.
   `/Volumes/workspace/default/staynest`.
5. Attach to Serverless compute and run top to bottom.

## Notes
- Revenue-related tasks use `status = 'completed'` bookings only.
- Task 7 writes `workspace.default.staynest_city_revenue` as a Delta table (adjust the
  catalog/schema in the notebook if yours differs).
- Task 8 drops the duplicate `city` column from the hotel side before joining.
