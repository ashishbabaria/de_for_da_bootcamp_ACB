CREATE DATABASE VayuAir;


USE VayuAir;

SELECT 'bronze_airports' AS table_name, COUNT(*) AS rows FROM bronze_airports
UNION ALL SELECT 'bronze_aircraft', COUNT(*) FROM bronze_aircraft
UNION ALL SELECT 'bronze_passengers', COUNT(*) FROM bronze_passengers
UNION ALL SELECT 'bronze_flights', COUNT(*) FROM bronze_flights
UNION ALL SELECT 'bronze_bookings', COUNT(*) FROM bronze_bookings
UNION ALL SELECT 'stg_passenger_updates', COUNT(*) FROM stg_passenger_updates;