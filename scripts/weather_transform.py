from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# Required columns that must be present in raw data
REQUIRED_COLUMNS = [
    "timestamp",
    "temperature_c",
    "humidity_percent",
    "rain_mm",
    "wind_speed_kmh",
    "weather_code",
    "wind_direction_deg",
    "apparent_temperature_c",
    "dew_point_c",
    "precipitation_mm",
]

# Columns that should be converted to float
FLOAT_COLUMNS = [
    "temperature_c",
    "humidity_percent",
    "rain_mm",
    "wind_speed_kmh",
    "wind_direction_deg",
    "apparent_temperature_c",
    "dew_point_c",
    "precipitation_mm",
]

# Valid range for temperature data (quality check)
TEMP_VALID_RANGE = (-60, 60)  # Valid temperature range in Celsius
HUMIDITY_VALID_RANGE = (0, 100)  # Valid humidity range in percentage
WIND_VALID_RANGE = (0, 200)  # Valid wind speed range in km/h


def transform_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Transform raw weather data with comprehensive validation and type conversion.
    
    Args:
        df: Raw DataFrame from API
        
    Returns:
        pd.DataFrame: Cleaned and validated DataFrame ready for insertion
        
    Raises:
        ValueError: If data fails validation checks
    \"\"\"
    logger.info(\"Starting data transformation...\")
    
    if df is None or df.empty:
        error_msg = \"No weather data available to transform.\"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create a copy to avoid modifying original DataFrame
    df = df.copy()
    initial_row_count = len(df)
    logger.debug(f\"Initial row count: {initial_row_count}\")
    
    # Standardize column names
    df.columns = [str(col).strip() for col in df.columns]
    logger.debug(\"Column names standardized\")

    # Validate required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        error_msg = f\"Missing required columns: {missing}\"
        logger.error(error_msg)
        raise ValueError(error_msg)
    logger.debug(\"All required columns present\")

    # Convert timestamp to datetime
    try:
        df[\"timestamp\"] = pd.to_datetime(df[\"timestamp\"], errors=\"raise\")
        logger.debug(\"Timestamp conversion successful\")
    except Exception as e:
        error_msg = f\"Failed to convert timestamp: {e}\"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Extract date/time components
    df[\"date\"] = df[\"timestamp\"].dt.date
    df[\"hour\"] = df[\"timestamp\"].dt.hour
    df[\"day_of_week\"] = df[\"timestamp\"].dt.day_name()
    logger.debug(\"Date/time components extracted\")

    # Convert numeric columns to float
    for col in FLOAT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors=\"coerce\")
    logger.debug(\"Float columns converted\")

    # Convert weather code to integer
    try:
        df[\"weather_code\"] = pd.to_numeric(df[\"weather_code\"], errors=\"coerce\").astype(\"Int64\")
    except Exception as e:
        logger.warning(f\"Weather code conversion issue: {e}\")

    # Data quality checks
    # Check for completely invalid rows
    invalid_rows = df[FLOAT_COLUMNS + [\"weather_code\"]].isna().all(axis=1)
    if invalid_rows.any():
        invalid_count = invalid_rows.sum()
        error_msg = f\"Found {invalid_count} rows with all invalid numeric values\"
        logger.error(error_msg)
        raise ValueError(error_msg)
    logger.debug(\"Data quality check: all rows have at least one valid numeric value\")
    
    # Check for temperature outliers (data quality)
    temp_outliers = (
        (df[\"temperature_c\"] < TEMP_VALID_RANGE[0]) | 
        (df[\"temperature_c\"] > TEMP_VALID_RANGE[1])
    ) & df[\"temperature_c\"].notna()
    if temp_outliers.any():
        logger.warning(f\"Found {temp_outliers.sum()} temperature outliers outside {TEMP_VALID_RANGE}°C\")
    
    # Check for humidity outliers
    humidity_outliers = (
        (df[\"humidity_percent\"] < HUMIDITY_VALID_RANGE[0]) | 
        (df[\"humidity_percent\"] > HUMIDITY_VALID_RANGE[1])
    ) & df[\"humidity_percent\"].notna()
    if humidity_outliers.any():
        logger.warning(f\"Found {humidity_outliers.sum()} humidity outliers outside {HUMIDITY_VALID_RANGE}%\")

    # Remove duplicate timestamps (keep last)
    duplicates_before = len(df)
    df = df.drop_duplicates(subset=[\"timestamp\"], keep=\"last\")
    duplicates_removed = duplicates_before - len(df)
    if duplicates_removed > 0:
        logger.warning(f\"Removed {duplicates_removed} duplicate records based on timestamp\")
    logger.debug(f\"Duplicates removed: {duplicates_removed}\")

    # Final type conversions for compatibility
    df[\"date\"] = pd.to_datetime(df[\"date\"]).dt.date
    df[\"hour\"] = df[\"hour\"].astype(int)
    df[\"day_of_week\"] = df[\"day_of_week\"].astype(str)

    final_row_count = len(df)
    logger.info(
        f\"✅ Transformation complete: {initial_row_count} → {final_row_count} records \"
        f\"(removed {initial_row_count - final_row_count} duplicates)\"
    )

    return df
