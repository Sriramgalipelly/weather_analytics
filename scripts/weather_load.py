from __future__ import annotations

import logging
import os
from time import time
from typing import Tuple

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration constants
BATCH_SIZE = 200
MAX_RETRIES = 3
CONNECTION_TIMEOUT = 30


def get_mysql_connection():
    """Create and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            autocommit=False,
            connection_timeout=CONNECTION_TIMEOUT,
        )
        logger.debug(f"MySQL connection established")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Failed to connect to MySQL: {err}")
        raise


def ensure_database_and_table():
    """Create database and weather_data table if they don't exist."""
    try:
        logger.info("Ensuring database and table exist...")
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            autocommit=True,
            connection_timeout=CONNECTION_TIMEOUT,
        )
        cursor = conn.cursor()
        
        cursor.execute("CREATE DATABASE IF NOT EXISTS weather_db")
        cursor.execute("USE weather_db")
        
        cursor.execute("""
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
                precipitation_mm FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON weather_data(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON weather_data(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hour ON weather_data(hour)")
        
        logger.debug("Table verified with indexes")
        cursor.close()
        conn.close()
        logger.info("Database and table ready")
        
    except mysql.connector.Error as err:
        logger.error(f"Database setup failed: {err}")
        raise


def insert_weather_data(df: pd.DataFrame) -> Tuple[int, int]:
    """Insert weather data into MySQL database."""
    if df is None or df.empty:
        logger.warning("Empty DataFrame - no data to insert")
        return 0, 0

    start_time = time()
    logger.info(f"Starting insertion for {len(df)} records")
    
    ensure_database_and_table()

    conn = get_mysql_connection()
    cursor = conn.cursor()

    insert_sql = """
        INSERT IGNORE INTO weather_data (
            timestamp, date, hour, day_of_week,
            temperature_c, humidity_percent, rain_mm,
            wind_speed_kmh, weather_code, wind_direction_deg,
            apparent_temperature_c, dew_point_c, precipitation_mm
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = df[[
        "timestamp", "date", "hour", "day_of_week",
        "temperature_c", "humidity_percent", "rain_mm",
        "wind_speed_kmh", "weather_code", "wind_direction_deg",
        "apparent_temperature_c", "dew_point_c", "precipitation_mm",
    ]].to_dict(orient="records")

    inserted = 0
    duplicates = 0
    batch = []
    batch_count = 0

    try:
        for row in rows:
            clean_row = []
            for value in row.values():
                if hasattr(value, "item"):
                    try:
                        value = value.item()
                    except Exception:
                        pass
                if pd.isna(value):
                    value = None
                clean_row.append(value)
            batch.append(tuple(clean_row))

            if len(batch) >= BATCH_SIZE:
                batch_count += 1
                try:
                    cursor.executemany(insert_sql, batch)
                    conn.commit()
                    inserted += cursor.rowcount
                    logger.debug(f"Batch {batch_count}: {cursor.rowcount} inserted")
                except Exception as e:
                    logger.error(f"Batch {batch_count} failed: {e}")
                    conn.rollback()
                    raise
                batch.clear()

        if batch:
            batch_count += 1
            cursor.executemany(insert_sql, batch)
            conn.commit()
            inserted += cursor.rowcount
            logger.debug(f"Final batch: {cursor.rowcount} inserted")

        duplicates = len(df) - inserted
        elapsed = time() - start_time
        logger.info(f"Insertion complete: {inserted} new records, {duplicates} duplicates in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Insertion failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    return inserted, duplicates
