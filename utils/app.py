"""
Streamlit web app for interactive temperature and humidity prediction using AutoGluon and real weather forecasts.
"""
import streamlit as st
import pandas as pd
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
import pathlib
from datetime import datetime, timedelta
import requests

st.title("Temperature & Humidity Prediction App")

# Siegen, Germany coordinates
LAT = 50.8748
LON = 8.0243

CSV_FILE = pathlib.Path("data/merged_data.csv")
MODEL_DIR = max(pathlib.Path("AutogluonModels").glob("ag-*"), key=lambda p: p.stat().st_mtime)

@st.cache_data
def load_data():
    """Load merged data from CSV."""
    df = pd.read_csv(CSV_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def to_tsdf(df: pd.DataFrame) -> TimeSeriesDataFrame:
    """Convert wide-format DataFrame to AutoGluon TimeSeriesDataFrame."""
    long_df = pd.concat(
        [
            df[["timestamp", "temperature", "external_temperature", "external_humidity", "wind_speed", "precipitation", "cloud_cover"]]
              .rename(columns={"temperature": "target"})
              .assign(item_id="temperature"),
            df[["timestamp", "humidity", "external_temperature", "external_humidity", "wind_speed", "precipitation", "cloud_cover"]]
              .rename(columns={"humidity": "target"})
              .assign(item_id="humidity"),
        ]
    )
    return TimeSeriesDataFrame.from_data_frame(
        long_df,
        id_column="item_id",
        timestamp_column="timestamp"
    )

@st.cache_resource
def load_predictor():
    """Load the trained AutoGluon predictor."""
    return TimeSeriesPredictor.load(MODEL_DIR)

def fetch_weather_forecast(target_dt):
    """Fetch real weather forecast for a given datetime from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,cloudcover",
        "start_date": target_dt.date().isoformat(),
        "end_date": target_dt.date().isoformat(),
        "timezone": "auto"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["hourly"]["time"]),
        "external_temperature": data["hourly"]["temperature_2m"],
        "external_humidity": data["hourly"]["relative_humidity_2m"],
        "wind_speed": data["hourly"]["wind_speed_10m"],
        "precipitation": data["hourly"]["precipitation"],
        "cloud_cover": data["hourly"]["cloudcover"]
    })
    # Find the closest hour to the requested time
    idx = (df["timestamp"] - target_dt).abs().idxmin()
    return df.iloc[idx][["external_temperature", "external_humidity", "wind_speed", "precipitation", "cloud_cover"]]

df = load_data()
tsdf = to_tsdf(df)
predictor = load_predictor()

# User input for prediction timestamp
st.header("Enter the date and time for prediction:")
default_dt = df['timestamp'].max() + timedelta(seconds=10)
default_date = default_dt.date()
default_time = default_dt.time()
user_date = st.date_input("Date", value=default_date)
user_time = st.time_input("Time", value=default_time)
user_dt = datetime.combine(user_date, user_time)

timestamp_min = df['timestamp'].max() + timedelta(seconds=10)
freq = pd.infer_freq(df['timestamp']) or '10s'
freq_seconds = pd.Timedelta(freq).total_seconds()
steps_ahead = int((user_dt - timestamp_min).total_seconds() // freq_seconds) + 1

if steps_ahead < 1:
    st.warning("Please select a date/time after the last data point: {}".format(timestamp_min))
    st.stop()

# Prepare future known covariates
target_steps = steps_ahead
future_timestamps = pd.date_range(start=timestamp_min, periods=target_steps, freq=freq)

# Use real weather forecast for future, else last known for past
if user_dt > df['timestamp'].max():
    try:
        forecast_weather = fetch_weather_forecast(user_dt)
        st.info(f"Using real weather forecast for {user_dt.date()} (hourly value closest to your time)")
    except Exception as e:
        st.warning(f"Could not fetch weather forecast: {e}. Using last known values instead.")
        forecast_weather = df.iloc[-1][["external_temperature", "external_humidity", "wind_speed", "precipitation", "cloud_cover"]]
else:
    forecast_weather = df.iloc[-1][["external_temperature", "external_humidity", "wind_speed", "precipitation", "cloud_cover"]]

known_covariates = pd.DataFrame([
    {
        "item_id": item_id,
        "timestamp": ts,
        "external_temperature": forecast_weather["external_temperature"],
        "external_humidity": forecast_weather["external_humidity"],
        "wind_speed": forecast_weather["wind_speed"],
        "precipitation": forecast_weather["precipitation"],
        "cloud_cover": forecast_weather["cloud_cover"]
    }
    for item_id in ["temperature", "humidity"]
    for ts in future_timestamps
])

if st.button("Predict"):
    forecast = predictor.predict(tsdf, known_covariates=known_covariates)
    forecast = forecast.reset_index().pivot(index="timestamp", columns="item_id", values="mean")
    if user_dt in forecast.index:
        temp_pred = forecast.loc[user_dt, "temperature"]
        hum_pred = forecast.loc[user_dt, "humidity"]
        st.success(f"**Prediction for {user_dt}:**")
        st.write(f"Temperature: {temp_pred:.2f} °C")
        st.write(f"Humidity: {hum_pred:.2f} %")
    else:
        st.warning("Prediction not available for the selected time. Try a different time.")
    st.subheader("Forecast Table (all steps)")
    st.dataframe(forecast) 