from __future__ import annotations

import logging
from datetime import datetime, timedelta
from time import time

import pandas as pd
import requests_cache
from openmeteo_requests import Client
from retry_requests import retry

logger = logging.getLogger(__name__)

# Configuration constants for professional reliability
RETRY_ATTEMPTS = 10  # Increased from 5 to 10 for better resilience
RETRY_BACKOFF_FACTOR = 0.3  # Increased for better exponential backoff
REQUEST_TIMEOUT = 30  # Add timeout to prevent hanging
CACHE_EXPIRY_DAYS = 7  # Cache expires after 7 days
CACHE_MAX_AGE = int(timedelta(days=CACHE_EXPIRY_DAYS).total_seconds())


def build_openmeteo_client():
    """Build Open-Meteo API client with enhanced retry logic and caching.
    
    Returns:
        Client: Configured Open-Meteo client with retries and caching.
    """
    # Enhanced cache configuration
    cache_session = requests_cache.CachedSession(
        ".cache",
        expire_after=CACHE_MAX_AGE,  # Cache expires after 7 days
        allowable_codes=(200, 404),  # Cache successful responses
        allowable_methods=("GET", "HEAD"),  # Only cache GET/HEAD
    )
    
    # Enhanced retry configuration with more attempts
    retry_session = retry(
        cache_session,
        retries=RETRY_ATTEMPTS,  # Increased from 5 to 10
        backoff_factor=RETRY_BACKOFF_FACTOR,  # Better exponential backoff
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
    )
    
    return Client(session=retry_session)


def extract_weather_data(extract_date: str) -> pd.DataFrame:
    """Extract hourly weather data from Open-Meteo API with enhanced error handling.
    
    Args:
        extract_date: Date to extract (format: YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: DataFrame with 24 hourly weather records
        
    Raises:
        ValueError: If API returns no data or DataFrame is empty
        Exception: If API call fails after all retries
    """
    start_time = time()
    logger.info(f"Starting data extraction for date: {extract_date}")
    
    try:
        openmeteo = build_openmeteo_client()
        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": 23.585236,
            "longitude": 87.344574,
            "start_date": extract_date,
            "end_date": extract_date,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "rain",
                "wind_speed_10m",
                "weather_code",
                "wind_direction_10m",
                "apparent_temperature",
                "dew_point_2m",
                "precipitation",
            ],
            "timezone": "Asia/Kolkata",
        }

        logger.debug(f"API URL: {url}")
        logger.debug(f"API Parameters: {params}")
        
        responses = openmeteo.weather_api(url, params=params)
        if not responses or len(responses) == 0:
            error_msg = f"Open-Meteo API returned no data for date {extract_date}."
            logger.error(error_msg)
            raise ValueError(error_msg)

        response = responses[0]
        hourly = response.Hourly()

        timestamps = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s"),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )

        weather_data = {
            "timestamp": timestamps,
            "temperature_c": hourly.Variables(0).ValuesAsNumpy(),
            "humidity_percent": hourly.Variables(1).ValuesAsNumpy(),
            "rain_mm": hourly.Variables(2).ValuesAsNumpy(),
            "wind_speed_kmh": hourly.Variables(3).ValuesAsNumpy(),
            "weather_code": hourly.Variables(4).ValuesAsNumpy(),
            "wind_direction_deg": hourly.Variables(5).ValuesAsNumpy(),
            "apparent_temperature_c": hourly.Variables(6).ValuesAsNumpy(),
            "dew_point_c": hourly.Variables(7).ValuesAsNumpy(),
            "precipitation_mm": hourly.Variables(8).ValuesAsNumpy(),
        }

        df = pd.DataFrame(weather_data)
        if df.empty:
            error_msg = f"Extracted DataFrame is empty for date {extract_date}."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        extraction_time = time() - start_time
        logger.info(f"✅ Data extraction successful: {len(df)} records extracted in {extraction_time:.2f}s")
        return df
        
    except Exception as exc:
        error_msg = f"❌ Data extraction failed for date {extract_date}: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        raise


if __name__ == "__main__":
    date_to_extract = (datetime.utcnow() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    df = extract_weather_data(date_to_extract)
    print(df.head())
    print(f"Rows extracted: {len(df)}")


