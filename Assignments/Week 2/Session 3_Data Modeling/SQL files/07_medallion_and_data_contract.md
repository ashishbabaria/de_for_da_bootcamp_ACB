# Vayu Air | Session 3 — Curate (Question 7)

## (a) Medallion layer mapping

| Table | Layer | Why it sits there |
|---|---|---|
| `bronze_airports`, `bronze_aircraft`, `bronze_passengers`, `bronze_flights`, `bronze_bookings` | **Bronze** | Raw, as-landed copies of the source system's tables — untouched, unconformed, kept for lineage/replay. |
| `stg_passenger_updates` | **Bronze** | Also a raw landed feed (the daily passenger change file); it hasn't been cleaned, deduplicated, or conformed to a business key yet. |
| `dw.DimCountry`, `dw.DimCity`, `dw.DimAirport`, `dw.DimAircraft`, `dw.DimFareClass`, `dw.DimFlight`, `dw.DimPassenger`, `dw.DimDate`, `dw.FactTicketSales` | **Gold** | The full curated star schema — surrogate-keyed dimensions (including snowflaked geography and SCD2 passenger history), plus the partitioned fact — modeled and optimized specifically to serve Power BI dashboards and the semantic layer. Dimensions and fact belong together in gold: neither is useful to a dashboard on its own. |

**A note on silver in this pipeline.** In this warehouse there is no explicit silver-layer set of tables. The cleaning, deduplication, and business-key conforming that a silver layer would normally hold happens *inside* the load scripts (`03_load_dims_and_fact.sql`, `05_scd2_passenger.sql`) as they populate gold directly from bronze. That is a legitimate choice at this scale — the source is small and stable, so a full silver tier would add pipeline surface area without buying much. In a larger deployment (or a Fabric lakehouse where bronze/silver/gold are literal physical layers), silver would typically hold cleaned, typed, deduplicated versions of the bronze tables — e.g. `silver.Passengers`, `silver.Airports` — that gold then models into the star.

## (b) Data contract — `bronze_bookings` feed

**Owner:** Vayu Air booking-platform team (source system owner).

**Schema and types**

| Field | Type | Nullable |
|---|---|---|
| booking_id | INT | No (unique) |
| passenger_id | INT | No (FK to passengers) |
| flight_id | INT | No (FK to flights) |
| booking_date | DATE | No |
| travel_date | DATE | No |
| fare_class | VARCHAR | No |
| fare_amount | DECIMAL(18,2) | No |
| tax_amount | DECIMAL(18,2) | No |
| booking_status | VARCHAR | No |
| miles_earned | INT | No |

**Allowed values**
- `fare_class`: `Economy`, `Premium Economy`, `Business`, `First`
- `booking_status`: `Confirmed`, `Cancelled`, `NoShow`

**Freshness / delivery SLA:** one full-file delivery per day by 06:00 IST, covering all bookings created in the previous calendar day; the pipeline expects the file to be present and readable by 07:00 IST for the daily load.

**Breaking vs. non-breaking change — examples**
- **Non-breaking:** adding a new optional column, e.g. `seat_number`, that downstream consumers can ignore until they choose to use it.
- **Breaking:** renaming `booking_status` to `status`, removing a column, changing `fare_amount` from DECIMAL to a formatted string, or adding a new `booking_status` value that isn't one of the three the contract declares — any of these silently breaks existing joins, filters, or the fact's referential integrity.
