import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "weather_db"),
        autocommit=True,
    )


st.set_page_config(page_title="Weather Analytics Dashboard", layout="wide")
st.title("Weather Analytics Dashboard")

query = """
SELECT timestamp, date, hour, day_of_week,
       temperature_c, humidity_percent, rain_mm, wind_speed_kmh,
       weather_code, wind_direction_deg, apparent_temperature_c,
       dew_point_c, precipitation_mm
FROM weather_data
ORDER BY timestamp DESC
"""

with get_connection() as conn:
    df = pd.read_sql(query, conn)

if df.empty:
    st.warning("No data available in MySQL yet. Run the ETL first.")
    st.stop()

# Convert fields
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = pd.to_datetime(df["date"]) if "date" in df.columns else df["timestamp"].dt.date

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)

if start_date > end_date:
    st.error("Start date must be before or equal to end date.")
    st.stop()

filtered = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)].copy()

hour_values = sorted(filtered["hour"].dropna().unique().tolist()) if "hour" in filtered.columns else [0]
hours = st.multiselect("Hour", hour_values, default=hour_values)
if hours:
    filtered = filtered[filtered["hour"].isin(hours)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Temperature", f"{filtered['temperature_c'].iloc[-1]:.2f} °C")
col2.metric("Latest Humidity", f"{filtered['humidity_percent'].iloc[-1]:.2f} %")
col3.metric("Latest Wind Speed", f"{filtered['wind_speed_kmh'].iloc[-1]:.2f} km/h")
col4.metric("Total Records", f"{len(filtered):,}")

st.subheader("Time Series Charts")
chart1, chart2, chart3, chart4 = st.columns(4)
with chart1:
    st.plotly_chart(px.line(filtered, x="timestamp", y="temperature_c", title="Temperature vs Time").update_traces(line=dict(color="#ff6b6b")))
with chart2:
    st.plotly_chart(px.line(filtered, x="timestamp", y="humidity_percent", title="Humidity vs Time").update_traces(line=dict(color="#4dabf7")))
with chart3:
    st.plotly_chart(px.line(filtered, x="timestamp", y="wind_speed_kmh", title="Wind Speed vs Time").update_traces(line=dict(color="#51cf66")))
with chart4:
    st.plotly_chart(px.line(filtered, x="timestamp", y="precipitation_mm", title="Rainfall vs Time").update_traces(line=dict(color="#ffd43b")))

st.subheader("Temperature Relationships")
fig_scatter = px.scatter(filtered, x="temperature_c", y="apparent_temperature_c", title="Apparent vs Actual Temperature")
st.plotly_chart(fig_scatter)

st.subheader("Daily Aggregates")
daily = filtered.assign(date=filtered["timestamp"].dt.date).groupby("date", as_index=False).agg(
    avg_temperature=("temperature_c", "mean"),
    max_temperature=("temperature_c", "max"),
    min_temperature=("temperature_c", "min")
)

fig_daily = px.line(daily, x="date", y=["avg_temperature", "max_temperature", "min_temperature"], title="Daily Temperature Metrics")
st.plotly_chart(fig_daily)

st.subheader("Weather Condition Summary")
if "weather_code" in filtered.columns:
    weather_counts = filtered["weather_code"].value_counts().reset_index()
    weather_counts.columns = ["weather_code", "count"]
    st.dataframe(weather_counts)
