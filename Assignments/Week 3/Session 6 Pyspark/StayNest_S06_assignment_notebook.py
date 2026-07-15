# Databricks notebook source
# MAGIC %md
# MAGIC # StayNest - Session 6 Assignment (PySpark Deep Dive)
# MAGIC Work through the 8 tasks below in order. Read the Assignment Questions PDF for the
# MAGIC full detail and acceptance criteria. Fill in each `# TODO` cell, run it, and keep the
# MAGIC output visible. Run on Databricks Free Edition (serverless).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 0 - Setup (already done for you)
# MAGIC Upload `bookings.csv`, `hotels.csv`, `customers.csv` to a Volume, then set `BASE`
# MAGIC to that path and run this cell. Counts should be 12000 / 200 / 2000.

# COMMAND ----------

# Point BASE at YOUR Volume path
BASE = "/Volumes/workspace/default/staynest"

print(spark.version)

read_csv = lambda name: (spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(f"{BASE}/{name}.csv"))

bookings_df   = read_csv("bookings")
hotels_df     = read_csv("hotels")
customers_df  = read_csv("customers")

print(f"bookings: {bookings_df.count()}, "
      f"hotels: {hotels_df.count()}, "
      f"customers: {customers_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 1 - Read and inspect
# MAGIC Show the schema, a few sample rows, the row count, and summary stats for the
# MAGIC numeric columns of `bookings_df`.

# COMMAND ----------

# Schema
bookings_df.printSchema()

# Sample rows
bookings_df.show(5)

# Row count -> ACTION, triggers a Spark job
print(f"Row count: {bookings_df.count()}")

# Summary stats for numeric columns
bookings_df.describe().show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 2 - Select and filter
# MAGIC From `bookings_df`, select a few useful columns and return the **completed**
# MAGIC bookings with `amount` over 10000 in the cities Goa or Mumbai. Use `col()`, combine
# MAGIC conditions with `&`, and use `.isin(...)`.

# COMMAND ----------

from pyspark.sql.functions import col

high_value_bookings = (bookings_df
    .select("booking_id", "customer_id", "hotel_id", "city", "amount", "status")
    .filter(
        (col("status") == "completed")
        & (col("amount") > 10000)
        & (col("city").isin("Goa", "Mumbai"))
    )
)

high_value_bookings.show(10)
print(f"Matching bookings: {high_value_bookings.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 3 - Derived columns
# MAGIC Add: `amount_with_gst` (amount plus 12% tax), a `value_tier`
# MAGIC (premium / standard / budget) using `when`/`otherwise`, and a `booking_month`
# MAGIC from `booking_date`.

# COMMAND ----------

from pyspark.sql.functions import col, when, month

bookings_df = (bookings_df
    .withColumn("amount_with_gst", col("amount") * 1.12)
    .withColumn(
        "value_tier",
        when(col("amount") > 15000, "premium")
        .when(col("amount") > 7000, "standard")
        .otherwise("budget")
    )
    .withColumn("booking_month", month(col("booking_date")))
)

bookings_df.select(
    "booking_id", "amount", "amount_with_gst", "value_tier",
    "booking_date", "booking_month",
).show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 4 - Aggregations
# MAGIC For **completed** bookings, group by `city` and return: number of bookings, total
# MAGIC revenue, average amount, biggest booking, and the count of unique customers.
# MAGIC Order by revenue, highest first.

# COMMAND ----------

from pyspark.sql.functions import count, sum, avg, max, countDistinct, col

city_revenue = (bookings_df
    .filter(col("status") == "completed")
    .groupBy("city")
    .agg(
        count("booking_id").alias("num_bookings"),
        sum("amount").alias("total_revenue"),
        avg("amount").alias("avg_amount"),
        max("amount").alias("biggest_booking"),
        countDistinct("customer_id").alias("unique_customers"),
    )
    .orderBy(col("total_revenue").desc())
)

city_revenue.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 5 - Joins
# MAGIC Inner-join bookings to hotels to enrich each booking. Do a left join too. Use
# MAGIC `left_anti` to check for orphaned bookings (expect 0). Then do a three-way join
# MAGIC with customers.

# COMMAND ----------

# Inner join -> enrich each booking with hotel details
bookings_hotels = bookings_df.join(hotels_df, on="hotel_id", how="inner")
bookings_hotels.select(
    "booking_id", "hotel_id", "hotel_name", "category", "star_rating", "amount"
).show(5)

# Left join -> keep every booking even if hotel is missing
bookings_hotels_left = bookings_df.join(hotels_df, on="hotel_id", how="left")
print(f"Left join row count: {bookings_hotels_left.count()}")

# left_anti -> bookings with no matching hotel (expect 0)
orphans = bookings_df.join(hotels_df, on="hotel_id", how="left_anti")
print(f"Orphaned bookings: {orphans.count()}")

# Three-way join -> bookings + hotels + customers
bookings_full = (bookings_df
    .join(hotels_df, on="hotel_id")
    .join(customers_df, on="customer_id")
)
bookings_full.select(
    "booking_id",
    bookings_df["city"].alias("hotel_city"),
    "hotel_name", "category",
    "customer_name", "membership",
    "amount",
).show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 6 - Spark SQL + a window function
# MAGIC Register temp views and use `spark.sql` to get revenue by hotel `category` for
# MAGIC completed bookings. Then use a window function to rank the **top 3 hotels by
# MAGIC revenue within each city**.

# COMMAND ----------

bookings_df.createOrReplaceTempView("bookings")
hotels_df.createOrReplaceTempView("hotels")
customers_df.createOrReplaceTempView("customers")

revenue_by_category = spark.sql("""
    SELECT
        h.category,
        COUNT(*)             AS num_bookings,
        SUM(b.amount)        AS revenue,
        ROUND(AVG(b.amount), 2) AS avg_amount
    FROM bookings b
    JOIN hotels h USING (hotel_id)
    WHERE b.status = 'completed'
    GROUP BY h.category
    ORDER BY revenue DESC
""")

revenue_by_category.show()

# COMMAND ----------

from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, sum as F_sum, col

hotel_city_window = Window.partitionBy("city").orderBy(col("revenue").desc())

top3_hotels_per_city = (bookings_df
    .filter(col("status") == "completed")
    .join(hotels_df, "hotel_id")
    .groupBy("hotel_id", "hotel_name", hotels_df["city"])
    .agg(F_sum("amount").alias("revenue"))
    .withColumn("rank_in_city", row_number().over(hotel_city_window))
    .filter(col("rank_in_city") <= 3)
    .orderBy("city", "rank_in_city")
)

top3_hotels_per_city.show(30, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 7 - Write the result
# MAGIC Write your city-revenue result as **Parquet**, and also as a **Delta table** with
# MAGIC `saveAsTable`. Read the Delta table back to confirm.

# COMMAND ----------

# Parquet write
(city_revenue.write
    .mode("overwrite")
    .parquet(f"{BASE}/output/city_revenue_parquet"))
print(f"Written to {BASE}/output/city_revenue_parquet")

# Delta write, registered as a Unity Catalog table
(city_revenue.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable("workspace.default.staynest_city_revenue"))
print("Registered as workspace.default.staynest_city_revenue")

# Read the Delta table back to confirm
spark.table("workspace.default.staynest_city_revenue").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 8 - One chained pipeline
# MAGIC In a single chain: keep completed bookings, join hotels, keep hotels with
# MAGIC `star_rating >= 4.0`, group by `city`, sum revenue, order descending, take the
# MAGIC top 5. End with one `.show()`.

# COMMAND ----------

from pyspark.sql.functions import col, sum as F_sum

top5_cities_wellrated = (bookings_df
    .filter(col("status") == "completed")
    .join(hotels_df.drop("city"), "hotel_id")          # avoid duplicate city column
    .filter(col("star_rating") >= 4.0)
    .groupBy("city")
    .agg(F_sum("amount").alias("revenue"))
    .orderBy(col("revenue").desc())
    .limit(5))                                          # nothing runs until show()

top5_cities_wellrated.show()
