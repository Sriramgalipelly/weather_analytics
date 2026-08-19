# Weather Data ETL & Analytics Project

## Objective
This project builds a complete end-to-end automated weather ETL pipeline that extracts hourly historical weather data from Open-Meteo, validates and transforms it, loads it incrementally into MySQL, performs SQL analysis, and exposes it via a Streamlit dashboard.

## Architecture

```text
Open-Meteo API
      ↓
   EXTRACT
      ↓
 Python + Pandas
      ↓
 TRANSFORM + VALIDATE
      ↓
   MySQL Storage
      ↓
    SQL Analysis
      ↓
 Streamlit Dashboard
      ↑
Windows Task Scheduler
```

## Technologies Used
- Python 3.10+
- Open-Meteo Historical API
- Pandas
- MySQL
- SQL
- Streamlit
- Plotly
- Windows Task Scheduler
- python-dotenv

## Data Source
The pipeline extracts hourly historical data from:

https://archive-api.open-meteo.com/v1/archive

Location:
- Latitude: 23.585236
- Longitude: 87.344574
- Timezone: Asia/Kolkata

## ETL Workflow
1. Determine extraction date automatically using Python datetime.
2. Get previous day weather data from Open-Meteo.
3. Validate the API response.
4. Convert raw arrays into a Pandas DataFrame.
5. Standardize column names and derived fields.
6. Check duplicate timestamps.
7. Insert only new rows into MySQL using `INSERT IGNORE`.
8. Log all events and failures.

## MySQL Schema
```sql
CREATE TABLE weather_data (
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
```

## Incremental Loading Strategy
The pipeline never deletes or replaces existing data. It checks each timestamp and inserts only new records.

- `INSERT IGNORE` is used to ignore duplicates.
- The `timestamp` field is unique, so duplicate hourly weather rows are rejected automatically.

## Environment Variables
Create a `.env` file in the project root with:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_MYSQL_PASSWORD
MYSQL_DATABASE=weather_db
```

Do not commit `.env` to version control.

## Installation
```bash
pip install -r requirements.txt
```

## Manual Execution
```bash
python scripts/weather_etl.py
```

## Dashboard Execution
```bash
streamlit run dashboard/app.py
```

## Windows Task Scheduler
Use the provided `run_weather_etl.bat` file and set the Python interpreter path.

## Troubleshooting
- Check `logs/weather_etl.log` for pipeline errors.
- Verify MySQL is running.
- Ensure `.env` is loaded correctly.
- Ensure the Python interpreter matches the environment used for dependencies.

## Future Improvements
- Add alerting for missing data.
- Add more weather locations.
- Add automated database backups.
- Add more advanced forecasting analytics.
