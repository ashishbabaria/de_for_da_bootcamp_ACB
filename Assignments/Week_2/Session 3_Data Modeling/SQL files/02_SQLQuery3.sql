/* =====================================================================
   Vayu Air | Session 3 - Data Modeling & Warehouse Engineering
   Question 2 - Star schema DDL
 
   Grain (see 01_grain_and_classification.sql): one row = one booking.

   Design notes:
   - Every dimension has an IDENTITY surrogate key plus its original
     source id kept as a business key (unique, not primary).
   - DimAirport is intentionally flat/denormalised here (airport_name,
     city, country, region all inline) - it gets snowflaked into
     DimCountry / DimCity / DimAirport in 04_snowflake_geography.sql.
   - DimPassenger already carries its SCD Type 2 columns (IsCurrent,
     EffectiveFrom, EffectiveTo) because the fact must point at a
     specific *version* of a passenger. 03_load_dims_and_fact.sql loads
     the first ("version 1") row per passenger; 05_scd2_passenger.sql
     applies the daily change feed on top of that.
   - The fact carries OriginAirportKey / DestAirportKey / AircraftKey
     directly (not only reachable through DimFlight) so common
     questions - revenue by airport, by aircraft type - don't need an
     extra hop through DimFlight. This is a deliberate, mildly
     denormalised star-schema choice for query performance.
   - Only additive measures (fare_amount, tax_amount, miles_earned) sit
     on the fact. booking_status stays a degenerate dimension (a
     transactional flag, always filtered, never browsed on its own),
     but fare_class gets its own small dw.DimFareClass table - it's a
     genuinely browsable attribute and a natural place to hang future
     fare-class attributes (baggage allowance, refundability, etc.).
   - The fact's PK is NONCLUSTERED on TicketSalesKey here. It gets
     re-shaped in 06_partition_fact.sql to a CLUSTERED PK on
     (BookingDateKey, TicketSalesKey) - SQL Server requires the
     clustered index of a partitioned table to include the partition
     column, so the rebuild there is expected and deliberate.
   ===================================================================== */

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dw')
    EXEC('CREATE SCHEMA dw');
GO

-- ---------------------------------------------------------------------
-- DimDate
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimDate (
    DateKey       INT          NOT NULL PRIMARY KEY,   -- yyyymmdd
    FullDate      DATE         NOT NULL,
    DayOfMonth    TINYINT      NOT NULL,
    MonthNumber   TINYINT      NOT NULL,
    MonthName     VARCHAR(10)  NOT NULL,
    Quarter       TINYINT      NOT NULL,
    [Year]        SMALLINT     NOT NULL,
    DayName       VARCHAR(10)  NOT NULL,
    IsWeekend     BIT          NOT NULL
);
GO

-- ---------------------------------------------------------------------
-- DimAirport (flat for now - see 04_snowflake_geography.sql)
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimAirport (
    AirportKey    INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    AirportCode   CHAR(3)       NOT NULL,   -- business key
    AirportName   VARCHAR(100)  NOT NULL,
    City          VARCHAR(100)  NOT NULL,
    Country       VARCHAR(100)  NOT NULL,
    Region        VARCHAR(50)   NOT NULL,
    CONSTRAINT UQ_DimAirport_AirportCode UNIQUE (AirportCode)
);
GO

-- ---------------------------------------------------------------------
-- DimAircraft
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimAircraft (
    AircraftKey    INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    AircraftCode   VARCHAR(10)  NOT NULL,   -- business key
    Model          VARCHAR(50)  NOT NULL,
    Manufacturer   VARCHAR(50)  NOT NULL,
    SeatCapacity   INT          NOT NULL,
    CONSTRAINT UQ_DimAircraft_AircraftCode UNIQUE (AircraftCode)
);
GO

-- ---------------------------------------------------------------------
-- DimFareClass
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimFareClass (
    FareClassKey    INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    FareClassName   VARCHAR(20)  NOT NULL,   -- business key
    CONSTRAINT UQ_DimFareClass_Name UNIQUE (FareClassName)
);
GO

-- ---------------------------------------------------------------------
-- DimFlight
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimFlight (
    FlightKey          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    FlightId           INT          NOT NULL,   -- business key
    FlightNumber       VARCHAR(10)  NOT NULL,
    OriginAirportKey   INT          NOT NULL,
    DestAirportKey     INT          NOT NULL,
    AircraftKey        INT          NOT NULL,
    FlightDateKey      INT          NOT NULL,
    CONSTRAINT UQ_DimFlight_FlightId UNIQUE (FlightId),
    CONSTRAINT FK_DimFlight_OriginAirport FOREIGN KEY (OriginAirportKey) REFERENCES dw.DimAirport (AirportKey),
    CONSTRAINT FK_DimFlight_DestAirport   FOREIGN KEY (DestAirportKey)   REFERENCES dw.DimAirport (AirportKey),
    CONSTRAINT FK_DimFlight_Aircraft      FOREIGN KEY (AircraftKey)      REFERENCES dw.DimAircraft (AircraftKey),
    CONSTRAINT FK_DimFlight_FlightDate    FOREIGN KEY (FlightDateKey)    REFERENCES dw.DimDate (DateKey)
);
GO

-- ---------------------------------------------------------------------
-- DimPassenger (SCD Type 2)
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimPassenger (
    PassengerKey        INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    PassengerId         INT          NOT NULL,   -- business key (repeats across versions)
    PassengerName       VARCHAR(100) NOT NULL,
    HomeAirportKey      INT          NOT NULL,
    FrequentFlyerTier   VARCHAR(20)  NOT NULL,
    SignupDate          DATE         NOT NULL,
    IsCurrent           BIT          NOT NULL DEFAULT (1),
    EffectiveFrom        DATE         NOT NULL,
    EffectiveTo          DATE         NULL,
    CONSTRAINT FK_DimPassenger_HomeAirport FOREIGN KEY (HomeAirportKey) REFERENCES dw.DimAirport (AirportKey)
);
GO

CREATE INDEX IX_DimPassenger_BusinessKey_Current
    ON dw.DimPassenger (PassengerId, IsCurrent);
GO

-- ---------------------------------------------------------------------
-- FactTicketSales  (grain: one row = one booking)
-- ---------------------------------------------------------------------
CREATE TABLE dw.FactTicketSales (
    TicketSalesKey     BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY NONCLUSTERED,
    BookingId          INT            NOT NULL,   -- degenerate dimension
    BookingDateKey     INT            NOT NULL,
    TravelDateKey      INT            NOT NULL,
    PassengerKey       INT            NOT NULL,
    FlightKey          INT            NOT NULL,
    OriginAirportKey   INT            NOT NULL,
    DestAirportKey     INT            NOT NULL,
    AircraftKey        INT            NOT NULL,
    FareClassKey       INT            NOT NULL,
    BookingStatus      VARCHAR(20)    NOT NULL,   -- degenerate dimension
    FareAmount         DECIMAL(18,2)  NOT NULL,   -- measure, additive
    TaxAmount          DECIMAL(18,2)  NOT NULL,   -- measure, additive
    MilesEarned        INT            NOT NULL,   -- measure, additive
    CONSTRAINT UQ_FactTicketSales_BookingId UNIQUE (BookingId),
    CONSTRAINT FK_Fact_BookingDate  FOREIGN KEY (BookingDateKey)   REFERENCES dw.DimDate (DateKey),
    CONSTRAINT FK_Fact_TravelDate   FOREIGN KEY (TravelDateKey)    REFERENCES dw.DimDate (DateKey),
    CONSTRAINT FK_Fact_Passenger    FOREIGN KEY (PassengerKey)     REFERENCES dw.DimPassenger (PassengerKey),
    CONSTRAINT FK_Fact_Flight       FOREIGN KEY (FlightKey)        REFERENCES dw.DimFlight (FlightKey),
    CONSTRAINT FK_Fact_OriginAirport FOREIGN KEY (OriginAirportKey) REFERENCES dw.DimAirport (AirportKey),
    CONSTRAINT FK_Fact_DestAirport   FOREIGN KEY (DestAirportKey)   REFERENCES dw.DimAirport (AirportKey),
    CONSTRAINT FK_Fact_Aircraft      FOREIGN KEY (AircraftKey)      REFERENCES dw.DimAircraft (AircraftKey),
    CONSTRAINT FK_Fact_FareClass     FOREIGN KEY (FareClassKey)     REFERENCES dw.DimFareClass (FareClassKey)
);
GO

-- 1. Every dw table exists (expect exactly 7 rows:
--    DimAircraft, DimAirport, DimDate, DimFareClass, DimFlight,
--    DimPassenger, FactTicketSales).

SELECT s.name AS schema_name, t.name AS table_name
FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE s.name = 'dw' ORDER BY t.name;

-- 2. Every foreign key on the fact is declared (expect 8 rows -
--    BookingDate, TravelDate, Passenger, Flight, OriginAirport,
--    DestAirport, Aircraft, FareClass).
SELECT
    fk.name              AS fk_name,
    OBJECT_NAME(fk.parent_object_id)     AS from_table,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id)     AS from_column,
    OBJECT_NAME(fk.referenced_object_id) AS to_table,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS to_column
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
WHERE fk.parent_object_id = OBJECT_ID('dw.FactTicketSales')
ORDER BY fk.name;

-- 3. Every dimension has a surrogate PK and a business-key UNIQUE.
--    (Skim the result set - every Dim* table should appear at least
--    once as PRIMARY KEY and once as UNIQUE, except DimDate which uses
--    its natural DateKey as PK and needs no separate unique constraint,
--    and DimPassenger which intentionally allows repeat PassengerId
--    across SCD2 versions.)
SELECT
    OBJECT_NAME(kc.parent_object_id) AS table_name,
    kc.name                          AS constraint_name,
    kc.type_desc                     AS constraint_type,
    COL_NAME(ic.object_id, ic.column_id) AS column_name
FROM sys.key_constraints kc
JOIN sys.index_columns ic
    ON ic.object_id = kc.parent_object_id AND ic.index_id = kc.unique_index_id
WHERE OBJECT_SCHEMA_NAME(kc.parent_object_id) = 'dw'
ORDER BY table_name, kc.type_desc, ic.key_ordinal;