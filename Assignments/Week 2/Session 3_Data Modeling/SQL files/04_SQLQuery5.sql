/* =====================================================================
   Vayu Air | Session 3 - Data Modeling & Warehouse Engineering
   Question 4 - Snowflake the geography
   
   Normalises the flat dw.DimAirport (from 02/03) into three linked
   tables: DimCountry -> DimCity -> DimAirport. AirportKey values are
   left untouched, so the existing FKs on DimFlight / FactTicketSales
   keep working without any reload.

   Region placement note: the source data has a clean country -> region
   functional dependency (every country maps to exactly one region), so
   Region lives on DimCountry. Keeping it on DimAirport would repeat the same region value across every airport
   in a country - the exact redundancy snowflaking exists to remove.
   ===================================================================== */

-- ---------------------------------------------------------------------
-- 1. DimCountry (Region lives here, one level up from the airport)
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimCountry (
    CountryKey    INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CountryName   VARCHAR(100) NOT NULL,
    Region        VARCHAR(50)  NOT NULL,
    CONSTRAINT UQ_DimCountry_Name UNIQUE (CountryName)
);
GO

INSERT INTO dw.DimCountry (CountryName, Region)
SELECT DISTINCT Country, Region
FROM dw.DimAirport;
GO

-- ---------------------------------------------------------------------
-- 2. DimCity
-- ---------------------------------------------------------------------
CREATE TABLE dw.DimCity (
    CityKey       INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CityName      VARCHAR(100) NOT NULL,
    CountryKey    INT          NOT NULL,
    CONSTRAINT FK_DimCity_Country FOREIGN KEY (CountryKey) REFERENCES dw.DimCountry (CountryKey),
    CONSTRAINT UQ_DimCity_NameCountry UNIQUE (CityName, CountryKey)
);
GO

INSERT INTO dw.DimCity (CityName, CountryKey)
SELECT DISTINCT a.City, c.CountryKey
FROM dw.DimAirport a
JOIN dw.DimCountry c ON c.CountryName = a.Country;
GO

-- ---------------------------------------------------------------------
-- 3. Normalise DimAirport: add CityKey, backfill it, then drop the
--    now-redundant City / Country / Region text columns. All three
--    have been moved up the hierarchy - City to DimCity, Country and
--    Region to DimCountry - so leaving copies on DimAirport would
--    re-introduce the redundancy snowflaking is meant to remove.
-- ---------------------------------------------------------------------
ALTER TABLE dw.DimAirport ADD CityKey INT NULL;
GO

UPDATE a
SET a.CityKey = ci.CityKey
FROM dw.DimAirport a
JOIN dw.DimCity ci ON ci.CityName = a.City
JOIN dw.DimCountry co ON co.CountryKey = ci.CountryKey AND co.CountryName = a.Country;
GO

ALTER TABLE dw.DimAirport ALTER COLUMN CityKey INT NOT NULL;
ALTER TABLE dw.DimAirport ADD CONSTRAINT FK_DimAirport_City FOREIGN KEY (CityKey) REFERENCES dw.DimCity (CityKey);
GO

ALTER TABLE dw.DimAirport DROP COLUMN City;
ALTER TABLE dw.DimAirport DROP COLUMN Country;
ALTER TABLE dw.DimAirport DROP COLUMN Region;
GO

-- ---------------------------------------------------------------------
-- Trade-off note:
-- Snowflaking removes the repeated city/country/region text on every
-- one of the 24 airport rows and guarantees a country can never be
-- spelled two different ways, at the cost of needing two extra joins
-- (Airport -> City -> Country) for any query that wants a country- or
-- region-level rollup.
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
-- Verification: resolve an airport all the way up to its country and
-- region. Region now comes from DimCountry, one join further up.
-- ---------------------------------------------------------------------
SELECT
    a.AirportCode,
    a.AirportName,
    ci.CityName,
    co.CountryName,
    co.Region
FROM dw.DimAirport a
JOIN dw.DimCity ci ON ci.CityKey = a.CityKey
JOIN dw.DimCountry co ON co.CountryKey = ci.CountryKey
ORDER BY co.Region, co.CountryName, ci.CityName, a.AirportCode;


SELECT 'DimCountry' AS t, COUNT(*) AS rows FROM dw.DimCountry
UNION ALL SELECT 'DimCity', COUNT(*) FROM dw.DimCity
UNION ALL SELECT 'DimAirport', COUNT(*) FROM dw.DimAirport;
