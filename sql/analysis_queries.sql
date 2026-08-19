-- 1. Average temperature by day
SELECT DATE(timestamp) AS date, AVG(temperature_c) AS avg_temperature
FROM weather_data
GROUP BY DATE(timestamp)
ORDER BY date;

-- 2. Maximum temperature
SELECT MAX(temperature_c) AS max_temperature
FROM weather_data;

-- 3. Minimum temperature
SELECT MIN(temperature_c) AS min_temperature
FROM weather_data;

-- 4. Average humidity by day
SELECT DATE(timestamp) AS date, AVG(humidity_percent) AS avg_humidity
FROM weather_data
GROUP BY DATE(timestamp)
ORDER BY date;

-- 5. Total rainfall by day
SELECT DATE(timestamp) AS date, SUM(rain_mm) AS total_rainfall
FROM weather_data
GROUP BY DATE(timestamp)
ORDER BY date;

-- 6. Maximum wind speed
SELECT MAX(wind_speed_kmh) AS max_wind_speed
FROM weather_data;

-- 7. Most common weather condition
SELECT weather_code, COUNT(*) AS frequency
FROM weather_data
GROUP BY weather_code
ORDER BY frequency DESC
LIMIT 10;

-- 8. Temperature by hour
SELECT hour, AVG(temperature_c) AS avg_temperature
FROM weather_data
GROUP BY hour
ORDER BY hour;

-- 9. Hottest day
SELECT DATE(timestamp) AS date, MAX(temperature_c) AS max_temperature
FROM weather_data
GROUP BY DATE(timestamp)
ORDER BY max_temperature DESC
LIMIT 1;

-- 10. Coldest day
SELECT DATE(timestamp) AS date, MIN(temperature_c) AS min_temperature
FROM weather_data
GROUP BY DATE(timestamp)
ORDER BY min_temperature ASC
LIMIT 1;

-- 11. Wettest day
SELECT DATE(timestamp) AS date, SUM(rain_mm) AS total_rainfall
FROM weather_data
GROUP BY DATE(timestamp)
ORDER BY total_rainfall DESC
LIMIT 1;

-- 12. Average apparent temperature
SELECT AVG(apparent_temperature_c) AS avg_apparent_temperature
FROM weather_data;
