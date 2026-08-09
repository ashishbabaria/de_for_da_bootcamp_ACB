# BuildMate Rentals — Microsoft Fabric Medallion Pipeline

End-to-end batch pipeline on Microsoft Fabric: four messy raw source drops → Bronze → Silver
→ Gold conformed star → business answers → Power BI serve. The whole thing runs on one Fabric
workspace over one copy of the data in OneLake.

## Repo layout
```
notebooks/
  01_bronze.ipynb            Task 1 — land raw as-is, lineage only, prove the re-send
  02_silver.ipynb            Task 2 — clean, conform, dedupe, NULL-SAFE filter
  03_gold.ipynb              Task 3 — conformed star + OPTIMIZE/ZORDER
  04_business_answers.ipynb  Task 4 — six Spark SQL answers + stakeholder write-up
screenshots/                 evidence captures (see checklist below)
README.md                    this file
```

## How to run
1. Create workspace `ws_buildmate` and Lakehouse `lh_buildmate`.
2. Upload `buildmate_raw_data.zip` to **Files/**, then expand it in a notebook:
   ```python
   import zipfile
   with zipfile.ZipFile("/lakehouse/default/Files/buildmate_raw_data.zip") as z:
       z.extractall("/lakehouse/default/Files/")
   ```
3. Import the four notebooks, attach each to `lh_buildmate`, and **run in order**:
   Bronze → Silver → Gold → Business Answers. Each layer reads the tables the previous one wrote.

## Acceptance criteria — all verified against the seeded data
| Layer  | Check | Expected |
|--------|-------|----------|
| Bronze | customers / depots / rentals / billing | 602 / 6 / 976 / 787 |
| Bronze | 10-June source-file check | two files × 31 rows |
| Silver | customers (customer_type distinct) | 600 (3) |
| Silver | rentals / quarantine (rental_type distinct) | 942 / 3 (2) |
| Silver | single-format date parse would null | **273 / 600** |
| Silver | careless filter would drop still-out | **175** |
| Silver | billing / unmatched | 779 / 8 |
| Gold   | dim_customer / dim_depot / dim_date | 600 / 6 / 30 |
| Gold   | fact_rental / fact_billing | 942 / 779 |
| Gold   | duration NULL == still-out; max asset_days | 175; ≤ 30 |
| Task 4 | (d) total revenue reconciles | ≈ ₹5 crore |
| Task 4 | (f) currently-out total == Silver still-out | 175 |

## The null-safe filter (the point of the whole assignment)
A blank `checkin_ts` means the machine is **still out on site**, not that the row is bad.
The impossibility check is `checkin_ts < checkout_ts`. In Spark, `null < timestamp` is **`null`**,
not `false` — so for a still-out machine `bad` is `null`, `~bad` is `null`, and
`filter(~bad)` **silently drops the row**. That deletes all 175 machines currently on site and
passes every eyeball review. The fix is `filter(~coalesce(bad, lit(False)))`. It saved 175 rows;
without it, "machines currently out" would have read **zero**.

## The money trap (verified)
`AMOUNT_INR` looks like `Rs. 64,157.16`. A tempting `regexp_replace("[^0-9.]", "")` keeps the
period inside *"Rs."*, producing `.64157.16` and corrupting the cast — every amount inflates
~100×, so the ₹5 crore total reads as ₹500 crore. Strip `Rs` explicitly:
`regexp_replace(col, "(?i)rs\.?|,|\s", "")` then `cast("decimal(12,2)")`. Parse failures: 0.

## Screenshot checklist (evidence is graded)
- Bronze: 4 row counts; the schema showing all-string columns; the two-file 10-June group.
- Silver: the `273/600` date print; the `175` careless-drop print; the 5 Silver counts.
- Gold: the 5 Gold counts; duration-NULL == still-out; `DESCRIBE HISTORY` showing OPTIMIZE.
- Task 4: all six result tables; the ₹5 crore reconciliation; currently-out == 175.
- Task 5: the Power BI report reading Gold through **DirectLake** (no import step).

---

## Task 5 — Serve on Power BI (DirectLake)
1. In `lh_buildmate`, open the SQL analytics endpoint → **New semantic model**, and pick the five
   Gold tables (`gold_dim_customer`, `gold_dim_depot`, `gold_dim_date`, `gold_fact_rental`,
   `gold_fact_billing`). Because the model sits on the Lakehouse, it reads the same OneLake Delta
   files through **DirectLake** — no import, nothing to refresh.
2. Model relationships on the conformed keys:
   `gold_fact_rental[depot_code] → gold_dim_depot[depot_code]`,
   `gold_fact_rental[customer_id] → gold_dim_customer[customer_id]`,
   `gold_fact_billing[rental_id] → gold_fact_rental[rental_id]` (or a date relationship to
   `gold_dim_date` on `checkout_ts`).
3. One report page: a **bar** of revenue by depot, a **bar** of utilisation by depot, and a
   **card** for machines currently out (`COUNT` of `gold_fact_rental` where `is_returned = 0`).

**Shared-capacity note.** Fabric bills every workload — notebooks, SQL endpoint, DirectLake
report — against **one shared capacity (CUs)**. A heavy Spark job can spike capacity and slow
every other item in the workspace, and sustained overrun triggers throttling. I would watch the
**Capacity Metrics app** for CU spikes and interactive-vs-background split, keep OPTIMIZE/heavy
rebuilds off peak reporting hours, and treat idle Spark sessions the way I'd terminate idle
Azure compute — stop them rather than let them draw CUs.

## Task 6 — Make the Silver rental build idempotent (stretch)
Re-running must not duplicate rows or resurrect a quarantined rental, and a new day's file must
add only its own valid rentals. Replace the overwrite write in `02_silver.ipynb` with a keyed
**MERGE** on `rental_id`:

```python
from delta.tables import DeltaTable

# silver_rentals must exist once first (run the notebook once, or create empty with the schema).
tgt = DeltaTable.forName(spark, "silver_rentals")
(tgt.alias("t")
    .merge(silver_rentals.alias("s"), "t.rental_id = s.rental_id")
    .whenMatchedUpdateAll()      # a re-sent/updated rental updates in place — no new row
    .whenNotMatchedInsertAll()   # a genuinely new rental is appended
    .execute())
```

Why it's safe: `rental_id` is the natural key, and the Silver build already keeps the *latest*
row per `rental_id` before the merge, so the 10-June re-send collapses to one row on the way in.
Matched rows update in place instead of appending, so running twice yields identical
`silver_rentals` and quarantine counts; adding one day's file inserts only that day's new
`rental_id`s. A quarantined rental never enters `silver_rentals` (it fails the null-safe check
before the merge), so a rerun cannot bring it back. **Prove it by running twice and comparing
counts** — a merge on the wrong key is worse than an append.

The full, runnable version of this — the upsert build plus both proofs (run-twice, and a held-out
day merging in only its own rentals) — is in `notebooks/05_idempotent.ipynb`.
