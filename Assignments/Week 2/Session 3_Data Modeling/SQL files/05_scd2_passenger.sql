/* =====================================================================
   Vayu Air | Session 3 - Data Modeling & Warehouse Engineering
   Question 5 - Apply stg_passenger_updates as SCD Type 2
   
   dw.DimPassenger already has the SCD2 shape (PassengerKey surrogate,
   PassengerId business key, IsCurrent, EffectiveFrom, EffectiveTo) and
   already holds "version 1" of every passenger. 

   This script applies the daily change feed in dbo.stg_passenger_updates using the two-pass pattern:
     Step 1: MERGE - expire current rows whose tier or home airport
             changed, and insert brand-new passengers as a single
             current row.
     Step 2: plain INSERT - add the new current version for every
             passenger just expired in step 1.

   @AsOfDate stands in for the feed's load date (there is no
   change_ts column on stg_passenger_updates, unlike Session 1's CDC
   feed) - in production this would come from the ingestion job.
   ===================================================================== */

DECLARE @AsOfDate DATE = CAST(GETDATE() AS DATE);

-- Resolve the staging feed's home_airport_code to an AirportKey once,
-- so both the MERGE and the follow-up INSERT can reuse it.

;WITH StagingResolved AS (
    SELECT
        s.passenger_id,
        s.passenger_name,
        s.frequent_flyer_tier,
        a.AirportKey AS HomeAirportKey
    FROM dbo.stg_passenger_updates s
    JOIN dw.DimAirport a ON a.AirportCode = s.home_airport_code
)

-- ---------------------------------------------------------------------
-- Step 1: MERGE - expire changed passengers, insert brand-new ones.
-- ---------------------------------------------------------------------
MERGE dw.DimPassenger AS tgt
USING StagingResolved AS src
    ON tgt.PassengerId = src.passenger_id
   AND tgt.IsCurrent = 1
WHEN MATCHED AND (
        tgt.FrequentFlyerTier <> src.frequent_flyer_tier
     OR tgt.HomeAirportKey   <> src.HomeAirportKey
     )
    THEN UPDATE SET
        tgt.IsCurrent  = 0,
        tgt.EffectiveTo = @AsOfDate
WHEN NOT MATCHED BY TARGET
    -- Brand-new passenger in the change feed. stg_passenger_updates
    -- doesn't carry signup_date, so we set SignupDate = @AsOfDate as
    -- a proxy - "when this passenger first appeared in our system." In
    -- production, either the feed would include the real signup date
    -- or we would default it to NULL, depending on the contract.
    THEN INSERT (PassengerId, PassengerName, HomeAirportKey, FrequentFlyerTier, SignupDate, IsCurrent, EffectiveFrom, EffectiveTo)
    VALUES (src.passenger_id, src.passenger_name, src.HomeAirportKey, src.frequent_flyer_tier, @AsOfDate, 1, @AsOfDate, NULL);
GO

-- How many current rows got expired in this run
SELECT COUNT(*) AS just_expired_rows
FROM dw.DimPassenger
WHERE IsCurrent = 0 AND EffectiveTo = CAST(GETDATE() AS DATE);

-- How many brand-new passengers got inserted (single current row, EffectiveFrom = today)
SELECT COUNT(*) AS brand_new_passengers
FROM dw.DimPassenger
WHERE IsCurrent = 1 AND EffectiveFrom = CAST(GETDATE() AS DATE);

-- Total DimPassenger row count so far
SELECT COUNT(*) AS passenger_row_count FROM dw.DimPassenger;

-- ---------------------------------------------------------------------
-- Step 2: insert the new current version for every passenger just
-- expired in step 1 (identified by EffectiveTo = today and IsCurrent = 0).
-- ---------------------------------------------------------------------

DECLARE @AsOfDate DATE = CAST(GETDATE() AS DATE);

INSERT INTO dw.DimPassenger (PassengerId, PassengerName, HomeAirportKey, FrequentFlyerTier, SignupDate, IsCurrent, EffectiveFrom, EffectiveTo)
SELECT
    old.PassengerId,
    s.passenger_name,
    a.AirportKey,
    s.frequent_flyer_tier,
    old.SignupDate,
    1,
    @AsOfDate,
    NULL
FROM dw.DimPassenger old
JOIN dbo.stg_passenger_updates s ON s.passenger_id = old.PassengerId
JOIN dw.DimAirport a ON a.AirportCode = s.home_airport_code
WHERE old.IsCurrent = 0
  AND old.EffectiveTo = @AsOfDate;
GO

SELECT COUNT(*) AS passenger_row_count FROM dw.DimPassenger;

-- ---------------------------------------------------------------------
-- Verification
-- ---------------------------------------------------------------------
-- A changed passenger should now show exactly two rows: one expired,
-- one current.
SELECT PassengerId, PassengerKey, FrequentFlyerTier, IsCurrent, EffectiveFrom, EffectiveTo
FROM dw.DimPassenger
WHERE PassengerId IN (SELECT passenger_id FROM dbo.stg_passenger_updates)
ORDER BY PassengerId, EffectiveFrom;

-- Every passenger should have exactly one current row.
SELECT PassengerId, COUNT(*) AS current_row_count
FROM dw.DimPassenger
WHERE IsCurrent = 1
GROUP BY PassengerId
HAVING COUNT(*) <> 1; 
