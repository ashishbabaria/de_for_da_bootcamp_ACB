/* =====================================================================
   Vayu Air | Session 3 - Data Modeling & Warehouse Engineering
   Question 3 - Load dimensions and fact from bronze_* tables
   
   Load order matters: DimDate and DimAirport first (nothing depends on
   them), then DimAircraft, then DimFlight (needs airport + aircraft +
   date), then DimPassenger (needs airport), then the fact last (needs
   everything).
   ===================================================================== */

-- ---------------------------------------------------------------------
-- 1. DimDate - generate a date spine covering every date that can
--    appear in booking_date / travel_date / flight_date / signup_date
--    (source data runs 2021-01-01 to 2026-03-31; padded to year-end).
-- ---------------------------------------------------------------------

;WITH DateSpine AS (
    SELECT CAST('2021-01-01' AS DATE) AS d
    UNION ALL
    SELECT DATEADD(DAY, 1, d) FROM DateSpine WHERE d < '2026-12-31'
)
INSERT INTO dw.DimDate (DateKey, FullDate, DayOfMonth, MonthNumber, MonthName, Quarter, [Year], DayName, IsWeekend)
SELECT
    YEAR(d) * 10000 + MONTH(d) * 100 + DAY(d)   AS DateKey,
    d                                            AS FullDate,
    DAY(d)                                       AS DayOfMonth,
    MONTH(d)                                     AS MonthNumber,
    DATENAME(MONTH, d)                           AS MonthName,
    DATEPART(QUARTER, d)                         AS Quarter,
    YEAR(d)                                      AS [Year],
    DATENAME(WEEKDAY, d)                         AS DayName,
    -- Language-neutral weekend check: DATEDIFF from a known Monday
    -- (1900-01-01 is a Monday), mod 7. 0..4 = Mon..Fri, 5 = Sat, 6 = Sun.
    -- Using DATENAME(WEEKDAY,...) IN ('Saturday','Sunday') would silently
    -- return 0 for every row on a non-English SQL Server language setting.
    CASE WHEN (DATEDIFF(DAY, '19000101', d) % 7) >= 5 THEN 1 ELSE 0 END AS IsWeekend
FROM DateSpine
OPTION (MAXRECURSION 0);
GO

-- ---------------------------------------------------------------------
-- 2. DimAirport (flat load - snowflaked later in 04)
-- ---------------------------------------------------------------------
INSERT INTO dw.DimAirport (AirportCode, AirportName, City, Country, Region)
SELECT airport_code, airport_name, city, country, region
FROM dbo.bronze_airports;
GO

-- ---------------------------------------------------------------------
-- 3. DimAircraft
-- ---------------------------------------------------------------------
INSERT INTO dw.DimAircraft (AircraftCode, Model, Manufacturer, SeatCapacity)
SELECT aircraft_code, model, manufacturer, seat_capacity
FROM dbo.bronze_aircraft;
GO

-- ---------------------------------------------------------------------
-- 3b. DimFareClass
-- ---------------------------------------------------------------------
INSERT INTO dw.DimFareClass (FareClassName)
SELECT DISTINCT fare_class
FROM dbo.bronze_bookings;
GO

-- ---------------------------------------------------------------------
-- 4. DimFlight
-- ---------------------------------------------------------------------
INSERT INTO dw.DimFlight (FlightId, FlightNumber, OriginAirportKey, DestAirportKey, AircraftKey, FlightDateKey)
SELECT
    f.flight_id,
    f.flight_number,
    ao.AirportKey,
    ad.AirportKey,
    ac.AircraftKey,
    YEAR(f.flight_date) * 10000 + MONTH(f.flight_date) * 100 + DAY(f.flight_date)
FROM dbo.bronze_flights f
JOIN dw.DimAirport ao ON ao.AirportCode = f.origin_airport_code
JOIN dw.DimAirport ad ON ad.AirportCode = f.dest_airport_code
JOIN dw.DimAircraft ac ON ac.AircraftCode = f.aircraft_code;
GO

-- ---------------------------------------------------------------------
-- 5. DimPassenger 
-- ---------------------------------------------------------------------
INSERT INTO dw.DimPassenger (PassengerId, PassengerName, HomeAirportKey, FrequentFlyerTier, SignupDate, IsCurrent, EffectiveFrom, EffectiveTo)
SELECT
    p.passenger_id,
    p.passenger_name,
    a.AirportKey,
    p.frequent_flyer_tier,
    p.signup_date,
    1,
    p.signup_date,
    NULL
FROM dbo.bronze_passengers p
JOIN dw.DimAirport a ON a.AirportCode = p.home_airport_code;
GO

-- ---------------------------------------------------------------------
-- 6. FactTicketSales
-- ---------------------------------------------------------------------
INSERT INTO dw.FactTicketSales (
    BookingId, BookingDateKey, TravelDateKey, PassengerKey, FlightKey,
    OriginAirportKey, DestAirportKey, AircraftKey, FareClassKey, BookingStatus,
    FareAmount, TaxAmount, MilesEarned
)
SELECT
    b.booking_id,
    YEAR(b.booking_date) * 10000 + MONTH(b.booking_date) * 100 + DAY(b.booking_date),
    YEAR(b.travel_date)  * 10000 + MONTH(b.travel_date)  * 100 + DAY(b.travel_date),
    dp.PassengerKey,
    df.FlightKey,
    df.OriginAirportKey,
    df.DestAirportKey,
    df.AircraftKey,
    fc.FareClassKey,
    b.booking_status,
    b.fare_amount,
    b.tax_amount,
    b.miles_earned
FROM dbo.bronze_bookings b
JOIN dw.DimFlight df ON df.FlightId = b.flight_id
JOIN dw.DimPassenger dp ON dp.PassengerId = b.passenger_id AND dp.IsCurrent = 1
JOIN dw.DimFareClass fc ON fc.FareClassName = b.fare_class;
GO

-- ---------------------------------------------------------------------
-- Verification: row counts must match, and every fact row must resolve
-- to all of its dimensions (no dangling/NULL keys expected, since the
-- FK constraints on FactTicketSales already enforce this on insert).
-- ---------------------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM dbo.bronze_bookings)     AS bronze_bookings_rows,
    (SELECT COUNT(*) FROM dw.FactTicketSales)      AS fact_rows;

SELECT COUNT(*) AS fact_rows_with_any_null_key
FROM dw.FactTicketSales
WHERE BookingDateKey IS NULL OR TravelDateKey IS NULL OR PassengerKey IS NULL
   OR FlightKey IS NULL OR OriginAirportKey IS NULL OR DestAirportKey IS NULL
   OR AircraftKey IS NULL;   -- expected: 0
