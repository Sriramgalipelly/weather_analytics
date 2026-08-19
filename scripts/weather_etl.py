import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import time

import pandas as pd
from dotenv import load_dotenv

from weather_extract import extract_weather_data
from weather_load import insert_weather_data
from weather_transform import transform_weather_data


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Professional logging configuration with detailed format
logging.basicConfig(
    filename=str(LOG_DIR / "weather_etl.log"),
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format="%(asctime)s [%(levelname)-8s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

# Add console handler for real-time output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s")
console_handler.setFormatter(console_formatter)

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)


def setup_environment():
    """Load environment variables and set defaults."""
    load_dotenv(BASE_DIR / ".env")
    os.environ.setdefault("MYSQL_HOST", "localhost")
    os.environ.setdefault("MYSQL_PORT", "3306")
    os.environ.setdefault("MYSQL_USER", "root")
    os.environ.setdefault("MYSQL_DATABASE", "weather_db")
    logger.debug("Environment configured successfully.")


def main():
    """Execute the complete ETL pipeline with professional error handling and timing."""
    start_time = time()
    phase_times = {}
    
    setup_environment()
    
    print("=" * 70)
    print("🌤️  WEATHER DATA ETL PIPELINE - STARTING")
    print("=" * 70)
    logger.info("=" * 70)
    logger.info("Weather ETL pipeline started (PROFESSIONAL MODE)")
    logger.info("=" * 70)

    try:
        # Calculate extraction date
        extract_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\n📅 Date being extracted: {extract_date}")
        logger.info(f"Extraction date: {extract_date}")

        # ============ EXTRACT PHASE ============
        print(f"\n📥 EXTRACT PHASE: Fetching data from Open-Meteo API...")
        extract_start = time()
        
        df_raw = extract_weather_data(extract_date)
        
        extract_time = time() - extract_start
        phase_times["EXTRACT"] = extract_time
        
        print(f"   ✅ Records extracted: {len(df_raw)}")
        print(f"   ⏱️  Time taken: {extract_time:.2f}s")
        logger.info(f"✅ EXTRACT: {len(df_raw)} records extracted in {extract_time:.2f}s")

        # ============ TRANSFORM PHASE ============
        print(f"\n⚙️  TRANSFORM PHASE: Cleaning and validating data...")
        transform_start = time()
        
        df_transformed = transform_weather_data(df_raw)
        
        transform_time = time() - transform_start
        phase_times["TRANSFORM"] = transform_time
        
        print(f"   ✅ Records transformed: {len(df_transformed)}")
        print(f"   ⏱️  Time taken: {transform_time:.2f}s")
        logger.info(f"✅ TRANSFORM: {len(df_transformed)} records transformed in {transform_time:.2f}s")

        # ============ LOAD PHASE ============
        print(f"\n💾 LOAD PHASE: Inserting data into MySQL database...")
        load_start = time()
        
        inserted, duplicates = insert_weather_data(df_transformed)
        
        load_time = time() - load_start
        phase_times["LOAD"] = load_time
        
        print(f"   ✅ New records inserted: {inserted}")
        print(f"   ⏭️  Duplicate records skipped: {duplicates}")
        print(f"   ⏱️  Time taken: {load_time:.2f}s")
        logger.info(f"✅ LOAD: {inserted} records inserted, {duplicates} duplicates skipped in {load_time:.2f}s")

        # ============ COMPLETION SUMMARY ============
        total_time = time() - start_time
        
        print("\n" + "=" * 70)
        print("📊 EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Phase Breakdown:")
        for phase, duration in phase_times.items():
            percentage = (duration / total_time) * 100
            print(f"  • {phase:12s}: {duration:8.3f}s ({percentage:5.1f}%)")
        print(f"{'─' * 70}")
        print(f"  TOTAL TIME:   {total_time:8.3f}s")
        print("=" * 70)
        print("✅ ETL completed successfully!")
        print("=" * 70 + "\n")
        
        logger.info("=" * 70)
        logger.info(f"EXECUTION SUMMARY - Total time: {total_time:.3f}s")
        for phase, duration in phase_times.items():
            percentage = (duration / total_time) * 100
            logger.info(f"  {phase}: {duration:.3f}s ({percentage:.1f}%)")
        logger.info("=" * 70)
        logger.info("✅ Weather ETL pipeline finished successfully.")
        
        return 0  # Success exit code

    except Exception as exc:
        total_time = time() - start_time
        error_msg = f"Weather ETL pipeline failed after {total_time:.2f}s: {str(exc)}"
        
        print("\n" + "=" * 70)
        print("❌ ERROR - ETL PIPELINE FAILED")
        print("=" * 70)
        print(f"Error: {str(exc)}")
        print(f"Total time before failure: {total_time:.2f}s")
        print("=" * 70 + "\n")
        
        logger.exception(error_msg)
        logger.error("Detailed error information logged above.")
        
        return 1  # Failure exit code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
