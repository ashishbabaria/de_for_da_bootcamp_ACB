/* =====================================================================
   Vayu Air | Session 3 - Data Modeling & Warehouse Engineering
   Question 6 - Partition FactTicketSales by date
     ===================================================================== */

-- ---------------------------------------------------------------------
-- 1. Partition function + scheme on BookingDateKey (INT, yyyymmdd)
-- ---------------------------------------------------------------------
CREATE PARTITION FUNCTION PF_BookingDate (INT)
AS RANGE RIGHT FOR VALUES (
    20241101, 20241201,
    20250101, 20250201, 20250301, 20250401, 20250501, 20250601,
    20250701, 20250801, 20250901, 20251001, 20251101, 20251201,
    20260101, 20260201, 20260301, 20260401
);
GO

CREATE PARTITION SCHEME PS_BookingDate
AS PARTITION PF_BookingDate ALL TO ([PRIMARY]);
GO

-- ---------------------------------------------------------------------
-- 2. Build a partitioned copy of the fact. The clustered index must
--    include the partitioning column (BookingDateKey) for partition
--    elimination to work.
-- ---------------------------------------------------------------------
CREATE TABLE dw.FactTicketSales_Partitioned (
    TicketSalesKey     BIGINT IDENTITY(1,1) NOT NULL,
    BookingId          INT            NOT NULL,
    BookingDateKey     INT            NOT NULL,
    TravelDateKey      INT            NOT NULL,
    PassengerKey       INT            NOT NULL,
    FlightKey          INT            NOT NULL,
    OriginAirportKey   INT            NOT NULL,
    DestAirportKey     INT            NOT NULL,
    AircraftKey        INT            NOT NULL,
    FareClassKey       INT            NOT NULL,
    BookingStatus      VARCHAR(20)    NOT NULL,
    FareAmount         DECIMAL(18,2)  NOT NULL,
    TaxAmount          DECIMAL(18,2)  NOT NULL,
    MilesEarned        INT            NOT NULL,
    CONSTRAINT PK_FactTicketSales_Partitioned
        PRIMARY KEY CLUSTERED (BookingDateKey, TicketSalesKey),
    CONSTRAINT UQ_FactTicketSales_BookingId_P UNIQUE (BookingId, BookingDateKey),
    CONSTRAINT FK_Fact_BookingDate_P   FOREIGN KEY (BookingDateKey)   REFERENCES dw.DimDate (DateKey),
    CONSTRAINT FK_Fact_TravelDate_P    FOREIGN KEY (TravelDateKey)    REFERENCES dw.DimDate (DateKey),
    CONSTRAINT FK_Fact_Passenger_P     FOREIGN KEY (PassengerKey)     REFERENCES dw.DimPassenger (PassengerKey),
    CONSTRAINT FK_Fact_Flight_P        FOREIGN KEY (FlightKey)        REFERENCES dw.DimFlight (FlightKey),
    CONSTRAINT FK_Fact_OriginAirport_P FOREIGN KEY (OriginAirportKey) REFERENCES dw.DimAirport (AirportKey),
    CONSTRAINT FK_Fact_DestAirport_P   FOREIGN KEY (DestAirportKey)   REFERENCES dw.DimAirport (AirportKey),
    CONSTRAINT FK_Fact_Aircraft_P      FOREIGN KEY (AircraftKey)      REFERENCES dw.DimAircraft (AircraftKey),
    CONSTRAINT FK_Fact_FareClass_P     FOREIGN KEY (FareClassKey)     REFERENCES dw.DimFareClass (FareClassKey)
) ON PS_BookingDate (BookingDateKey);
GO
 
SET IDENTITY_INSERT dw.FactTicketSales_Partitioned ON;
 
INSERT INTO dw.FactTicketSales_Partitioned (
    TicketSalesKey, BookingId, BookingDateKey, TravelDateKey, PassengerKey, FlightKey,
    OriginAirportKey, DestAirportKey, AircraftKey, FareClassKey, BookingStatus,
    FareAmount, TaxAmount, MilesEarned
)
SELECT
    TicketSalesKey, BookingId, BookingDateKey, TravelDateKey, PassengerKey, FlightKey,
    OriginAirportKey, DestAirportKey, AircraftKey, FareClassKey, BookingStatus,
    FareAmount, TaxAmount, MilesEarned
FROM dw.FactTicketSales;
 
SET IDENTITY_INSERT dw.FactTicketSales_Partitioned OFF;
GO
 
-- ---------------------------------------------------------------------
-- 3. Swap the partitioned table in.
-- ---------------------------------------------------------------------
EXEC sp_rename 'dw.FactTicketSales', 'FactTicketSales_Unpartitioned';
EXEC sp_rename 'dw.FactTicketSales_Partitioned', 'FactTicketSales';
GO
 
DROP TABLE dw.FactTicketSales_Unpartitioned;
GO
 
-- ---------------------------------------------------------------------
-- 4. Confirm the partition layout.
-- ---------------------------------------------------------------------
SELECT
    p.partition_number,
    prv.value AS lower_boundary_exclusive,
    p.rows
FROM sys.partitions p
LEFT JOIN sys.partition_range_values prv
    ON prv.function_id = (SELECT function_id FROM sys.partition_functions WHERE name = 'PF_BookingDate')
   AND prv.boundary_id = p.partition_number - 1
WHERE p.object_id = OBJECT_ID('dw.FactTicketSales')
  AND p.index_id = 1
ORDER BY p.partition_number;
GO

-- ---------------------------------------------------------------------
-- 5. Test queries - 
-- ---------------------------------------------------------------------
SET STATISTICS IO, TIME ON;

-- Query A: filters on the partition key (BookingDateKey) -> should
-- prune to a single partition (January 2025).

SELECT COUNT(*) AS bookings_jan_2025, SUM(FareAmount) AS fare_jan_2025
FROM dw.FactTicketSales
WHERE BookingDateKey BETWEEN 20250101 AND 20250131;

-- Query B: filters on a non-partition column (PassengerKey) -> must
-- scan every partition, since BookingDateKey isn't restricted.

SELECT COUNT(*) AS bookings_for_passenger
FROM dw.FactTicketSales
WHERE PassengerKey = 1;



SET STATISTICS IO, TIME OFF;

