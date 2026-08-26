/* =====================================================================
   Vayu Air | Session 3 - Data Modeling & Warehouse Engineering
   Question 1 - Grain statement + column classification
   Engine: SQL Server (T-SQL)
   ===================================================================== */

-- ---------------------------------------------------------------------
-- OPTIONAL: run this first to see the actual joined rows before
-- classifying columns below. Not required by the acceptance criteria
-- (which only asks for the grain comment + classification + additivity
-- note) - but it's useful evidence and a good habit: classify from what the data actually looks like, 
-- not just the data dictionary.
-- ---------------------------------------------------------------------
SELECT TOP 20
    b.booking_id,
    b.passenger_id,
    b.flight_id,
    b.booking_date,
    b.travel_date,
    b.fare_class,
    b.fare_amount,
    b.tax_amount,
    b.booking_status,
    b.miles_earned,
    f.flight_number,
    f.origin_airport_code,
    f.dest_airport_code,
    f.aircraft_code,
    f.flight_date
FROM dbo.bronze_bookings b
JOIN dbo.bronze_flights f ON f.flight_id = b.flight_id
ORDER BY b.booking_id;

-- ---------------------------------------------------------------------
-- GRAIN STATEMENT
-- ---------------------------------------------------------------------
-- One row in the sales fact = one ticket sold (one booking_id) for one
-- passenger, on one flight, at one fare class.
-- Grain = one booking.

-- ---------------------------------------------------------------------
-- COLUMN CLASSIFICATION
-- Source: bronze_bookings JOIN bronze_flights ON flight_id
-- ---------------------------------------------------------------------
-- column                 | classification                | why
-- -----------------------+-------------------------------+---------------------------------------------------------------
-- booking_id             | degenerate dimension          | Uniquely identifies the fact row itself; has no attributes of
--                        |                               | its own, so it is kept directly on the fact instead of a table.
-- passenger_id           | dimension key -> Passenger    | FK to DimPassenger (business key, versioned via SCD2).
-- flight_id              | dimension key -> Flight       | FK to DimFlight.
-- booking_date           | dimension key -> Date         | FK to DimDate as BookingDateKey (transaction date).
-- travel_date            | dimension key -> Date         | FK to DimDate as TravelDateKey. In this source travel_date and
--                        |                               | the joined flight_date always match (a booking is for a specific
--                        |                               | flight on a specific date), but keeping it on the fact means
--                        |                               | "when did the passenger fly" is answerable without a join hop
--                        |                               | through DimFlight -> DimDate.
-- fare_class             | dimension key -> FareClass    | Only 4 fixed values today, but it's a genuinely browsable
--                        |                               | attribute (not just a transactional flag), so it gets its own
--                        |                               | small dw.DimFareClass table with a surrogate key - this also
--                        |                               | leaves room to add attributes (baggage allowance, refundable,
--                        |                               | priority boarding) later without touching the fact.
-- fare_amount            | MEASURE (additive)            | Base fare in INR - safe to SUM across any dimension.
-- tax_amount             | MEASURE (additive)            | Taxes/fees in INR - safe to SUM across any dimension.
-- booking_status         | degenerate dimension          | Only 3 values (Confirmed/Cancelled/NoShow); used as a revenue
--                        |                               | filter, kept as an attribute on the fact.
-- miles_earned           | MEASURE (additive)            | Loyalty miles credited - safe to SUM across any dimension.
-- flight_number          | Flight dimension attribute    | Describes the flight, not the booking - lives on DimFlight.
-- origin_airport_code    | dimension key -> Airport      | FK to DimAirport as OriginAirportKey.
-- dest_airport_code      | dimension key -> Airport      | FK to DimAirport as DestAirportKey.
-- aircraft_code          | dimension key -> Aircraft     | FK to DimAircraft.
-- flight_date            | Flight dimension attribute    | Describes the flight (its scheduled date) and lives on
--                        |                               | DimFlight as FlightDateKey. The fact reaches DimDate directly
--                        |                               | through booking_date / travel_date.

-- ---------------------------------------------------------------------
-- ADDITIVITY NOTE
-- ---------------------------------------------------------------------
-- fare_amount, tax_amount and miles_earned are fully additive: summing
-- them across any slice of the fact (by passenger, by route, by month)
-- always produces a meaningful total.
--
-- Non-additive example: seat_capacity. It describes the aircraft, not the
-- booking - summing it across every ticket sold on a flight would count
-- the plane's capacity once per passenger, wildly overstating it. It
-- belongs on DimAircraft as a descriptive attribute, never as a fact
-- measure.
