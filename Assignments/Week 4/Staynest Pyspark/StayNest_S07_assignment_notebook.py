# Databricks notebook source
# MAGIC %md
# MAGIC # StayNest - Session 7 Assignment (Delta Lake & Lakehouse)
# MAGIC Work through the 8 tasks in order. Read the Assignment Questions PDF for the full
# MAGIC detail and acceptance criteria. Fill each `# TODO` cell, run it, and keep the output
# MAGIC visible. Runs on Databricks Free Edition (serverless).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 0 - Setup (already done for you)
# MAGIC Upload `bookings.csv`, `hotels.csv`, `bookings_updates.csv` to a Volume, set `BASE`,
# MAGIC `CATALOG`, `SCHEMA`, and run this cell. Expect 12000 / 200 / 200.

# COMMAND ----------

BASE    = "/Volumes/workspace/default/staynest"
CATALOG = "workspace"
SCHEMA  = "default"
FQN = lambda name: f"{CATALOG}.{SCHEMA}.{name}"

read_csv = lambda name: (spark.read
    .option("header", True).option("inferSchema", True)
    .csv(f"{BASE}/{name}.csv"))

bookings_df = read_csv("bookings")
hotels_df   = read_csv("hotels")
updates_df  = read_csv("bookings_updates")

print(f"bookings: {bookings_df.count()}, hotels: {hotels_df.count()}, "
      f"updates: {updates_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 1 - Read the plan and force a broadcast join
# MAGIC Join bookings to hotels and call `.explain()` to see the plan. Then force a
# MAGIC broadcast join with `broadcast(hotels_df)` and `.explain()` again. In a comment,
# MAGIC say which join each plan used and why broadcast avoids a shuffle.
# MAGIC (Tip: hotels also has a `city` column, so `hotels_df.drop("city")` before joining.)

# COMMAND ----------

from pyspark.sql.functions import broadcast

# ── Plain join — let Catalyst decide the strategy ──
plain_join = bookings_df.join(hotels_df.drop("city"), "hotel_id")
print("=== Plain join — Catalyst's chosen plan ===")
plain_join.explain()

# COMMAND ----------

# ── Forced broadcast join — explicit hint ──
forced_broadcast_join = bookings_df.join(broadcast(hotels_df.drop("city")), "hotel_id")
print("=== Forced broadcast join plan ===")
forced_broadcast_join.explain()

# ── Comment: what each plan shows ──
# hotels_df is only 200 rows (well under the ~10 MB autoBroadcastJoinThreshold), so
# Catalyst's own plan already picks a BroadcastHashJoin for the plain join — no
# Exchange (shuffle) appears anywhere in the plan.
# The broadcast(hotels_df.drop("city")) hint forces the same BroadcastHashJoin
# explicitly: Spark copies the full small table to every executor up front, so the
# join is resolved locally on each partition of the large side (bookings). Because
# no rows have to move across the network to align matching keys (as a
# SortMergeJoin would require), there is no shuffle — that's what makes broadcast
# the fastest join for a small-vs-large table pair.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 2 - Create a Delta table, then read its history
# MAGIC Write `bookings_df` as a managed Delta table with `saveAsTable`. Then create some
# MAGIC history: run an `UPDATE` (set pending to completed) and a `DELETE` (remove
# MAGIC cancelled). Show `DESCRIBE HISTORY` and point out the versioned commits.

# COMMAND ----------

bookings_delta = FQN("bookings_delta")

(bookings_df.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(bookings_delta))

print(f"Created Delta table: {bookings_delta}")
print(f"Row count right after WRITE (version 0): {spark.table(bookings_delta).count()}")

# COMMAND ----------

# ── Make history: an UPDATE, then a DELETE ──
spark.sql(f"UPDATE {bookings_delta} SET status = 'completed' WHERE status = 'pending'")
spark.sql(f"DELETE FROM {bookings_delta} WHERE status = 'cancelled'")

print(f"Row count after UPDATE + DELETE: {spark.table(bookings_delta).count()}")

# COMMAND ----------

# ── Show the versioned commits ──
history_df = spark.sql(f"DESCRIBE HISTORY {bookings_delta}")
display(history_df.select("version", "timestamp", "operation", "operationParameters"))

# Expect three rows: version 0 = WRITE, version 1 = UPDATE, version 2 = DELETE
# (each DML statement is its own atomic, versioned commit in the transaction log)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 3 - Time travel and RESTORE
# MAGIC Read the table as it was at **version 0** (before your UPDATE and DELETE) and show
# MAGIC its count. Then `RESTORE` the table to version 0 and confirm the count is back.
# MAGIC Show that RESTORE appears as a new commit in the history.

# COMMAND ----------

# ── Time travel: read version 0 ──
v0_df = spark.read.option("versionAsOf", 0).table(bookings_delta)
v0_count = v0_df.count()
print(f"Version 0 count (before UPDATE/DELETE): {v0_count}")

current_count = spark.table(bookings_delta).count()
print(f"Current count (after UPDATE/DELETE)   : {current_count}")

# COMMAND ----------

# ── RESTORE back to version 0 ──
spark.sql(f"RESTORE TABLE {bookings_delta} TO VERSION AS OF 0")

restored_count = spark.table(bookings_delta).count()
print(f"Count immediately after RESTORE       : {restored_count}")
assert restored_count == v0_count, "RESTORE did not bring the count back to version 0"
print("Confirmed: restored count matches version 0 count.")

# COMMAND ----------

# ── RESTORE is itself a new, versioned commit — nothing is lost ──
display(spark.sql(f"DESCRIBE HISTORY {bookings_delta}")
        .select("version", "timestamp", "operation", "operationParameters"))

# Expect a 4th row: version 3, operation = RESTORE. The UPDATE and DELETE commits
# (versions 1 and 2) are still there in the log — RESTORE didn't erase them, it just
# added a new commit that makes the table's current state match version 0 again.
# That means you could RESTORE forward again if needed.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 4 - OPTIMIZE and ZORDER
# MAGIC Run `OPTIMIZE` on your Delta table to compact files. Then run
# MAGIC `OPTIMIZE ... ZORDER BY (city)`. In a comment, say what OPTIMIZE does and why
# MAGIC `city` is a good ZORDER column but `status` would not be.

# COMMAND ----------

# ── Compact small files into fewer, larger ones ──
display(spark.sql(f"OPTIMIZE {bookings_delta}"))

# COMMAND ----------

# ── Compact AND co-locate rows by city for data skipping ──
display(spark.sql(f"OPTIMIZE {bookings_delta} ZORDER BY (city)"))

# ── Comment ──
# OPTIMIZE bin-packs the many small files that build up from repeated writes,
# updates, and deletes into a handful of larger (~1 GB target) files, so a query
# has far fewer files to open and scan.
# ZORDER goes further: it physically co-locates rows that share similar values in
# the given column(s), so when a query filters on that column, Spark can skip
# entire files that can't contain a match (data skipping).
# city is a good ZORDER column because it is high-cardinality (many distinct
# cities) and is exactly what queries filter/group by (e.g. gold_city_revenue).
# status would be a poor choice because it only has 3 distinct values
# (completed/cancelled/pending) — with so few values, most files still contain a
# mix of all three, so co-locating by status gives almost no file-skipping benefit.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 5 - Bronze: land the raw data
# MAGIC Write the raw bookings to a `bronze_bookings` Delta table, keeping every row and
# MAGIC adding an `ingested_at` timestamp column.

# COMMAND ----------

from pyspark.sql.functions import current_timestamp

bronze_bookings_name = FQN("bronze_bookings")

bronze_bookings_df = bookings_df.withColumn("ingested_at", current_timestamp())

(bronze_bookings_df.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(bronze_bookings_name))

print(f"bronze_bookings rows: {spark.table(bronze_bookings_name).count()}")
spark.table(bronze_bookings_name).printSchema()

# Bronze is the raw, append-only landing layer: every original row is kept as-is
# (nothing filtered, nothing joined), with only an ingestion timestamp added so we
# always know when each row landed. It can always be replayed to rebuild silver/gold.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 6 - Silver: clean and conform
# MAGIC Build `silver_bookings` from bronze: keep only completed bookings and join the
# MAGIC hotel dimension to add `category`, `star_rating`, and the hotel name. Drop the
# MAGIC duplicate `city` from the hotel side so the join has a single `city`.

# COMMAND ----------

from pyspark.sql.functions import col

silver_bookings_name = FQN("silver_bookings")

silver_bookings_df = (
    spark.table(bronze_bookings_name)
    .filter(col("status") == "completed")
    .join(hotels_df.drop("city"), "hotel_id")   # drop hotel-side city to avoid a duplicate column
)

(silver_bookings_df.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(silver_bookings_name))

print(f"silver_bookings rows: {spark.table(silver_bookings_name).count()}")
spark.table(silver_bookings_name).printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 7 - Gold: business-ready aggregate
# MAGIC From silver, build a `gold_city_revenue` Delta table: bookings and total revenue
# MAGIC per city, ordered by revenue.

# COMMAND ----------

from pyspark.sql.functions import count as F_count, sum as F_sum

gold_city_revenue_name = FQN("gold_city_revenue")

gold_city_revenue_df = (
    spark.table(silver_bookings_name)
    .groupBy("city")
    .agg(
        F_count("*").alias("bookings"),
        F_sum("amount").alias("revenue"),
    )
    .orderBy(col("revenue").desc())
)

(gold_city_revenue_df.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(gold_city_revenue_name))

display(spark.table(gold_city_revenue_name))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 8 - Incremental load with MERGE
# MAGIC You have today's batch in `updates_df` (150 changed bookings + 50 new ones).
# MAGIC `MERGE` it into your Delta table: update matched booking_ids, insert new ones, in
# MAGIC one command. Report the row count before and after (it should grow by the 50 new).

# COMMAND ----------

before_count = spark.table(bookings_delta).count()
print(f"Row count BEFORE MERGE: {before_count}")

updates_df.createOrReplaceTempView("bookings_updates_batch")

spark.sql(f"""
    MERGE INTO {bookings_delta} AS target
    USING bookings_updates_batch AS source
        ON target.booking_id = source.booking_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

after_count = spark.table(bookings_delta).count()
print(f"Row count AFTER MERGE : {after_count}")
print(f"New rows added        : {after_count - before_count}  (expected 50)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample of updated rows (verification)

# COMMAND ----------

# Spot-check a few booking_ids that existed in the update batch to confirm the
# MERGE actually applied the new status/amount rather than just inserting.
sample_ids = [row.booking_id for row in updates_df.limit(5).select("booking_id").collect()]
display(spark.table(bookings_delta).filter(col("booking_id").isin(sample_ids)))
