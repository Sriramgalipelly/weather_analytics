CREATE DATABASE IF NOT EXISTS weather_db;
USE weather_db;

CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL UNIQUE,
    date DATE NOT NULL,
    hour INT NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    temperature_c FLOAT,
    humidity_percent FLOAT,
    rain_mm FLOAT,
    wind_speed_kmh FLOAT,
    weather_code INT,
    wind_direction_deg FLOAT,
    apparent_temperature_c FLOAT,
    dew_point_c FLOAT,
    precipitation_mm FLOAT
);

CREATE INDEX IF NOT EXISTS idx_weather_data_date ON weather_data(date);
CREATE INDEX IF NOT EXISTS idx_weather_data_hour ON weather_data(hour);
CREATE INDEX IF NOT EXISTS idx_weather_data_day_of_week ON weather_data(day_of_week);
