"""
Trains an AutoGluon time series model on merged sensor and weather data.
"""
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
import pandas as pd, pathlib

CSV_FILE = pathlib.Path("data/merged_data.csv")
PRED_STEPS = 6           # Adjust as needed for your data

def load_merged_csv(path: pathlib.Path) -> pd.DataFrame:
    """Load merged sensor and weather data from CSV."""
    df = pd.read_csv(path)
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

def main():
    """Train the AutoGluon model and print summary."""
    df = load_merged_csv(CSV_FILE)
    print(f"Loaded {len(df)} merged data points")
    print(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    tsdf = to_tsdf(df)
    print(f"TimeSeriesDataFrame shape: {tsdf.shape}")

    predictor = TimeSeriesPredictor(
        prediction_length=PRED_STEPS,
        verbosity=2,
        known_covariates_names=[
            "external_temperature",
            "external_humidity",
            "wind_speed",
            "precipitation",
            "cloud_cover"
        ]
    ).fit(tsdf)

    # --- Prepare future known covariates ---
    last_timestamp = df['timestamp'].max()
    freq = pd.infer_freq(df['timestamp']) or '10s'
    future_timestamps = pd.date_range(start=last_timestamp + pd.Timedelta(freq), periods=PRED_STEPS, freq=freq)
    last_weather = df.iloc[-1][["external_temperature", "external_humidity", "wind_speed", "precipitation", "cloud_cover"]]
    # Repeat last weather values for each step and both item_ids
    known_covariates = pd.DataFrame([
        {
            "item_id": item_id,
            "timestamp": ts,
            "external_temperature": last_weather["external_temperature"],
            "external_humidity": last_weather["external_humidity"],
            "wind_speed": last_weather["wind_speed"],
            "precipitation": last_weather["precipitation"],
            "cloud_cover": last_weather["cloud_cover"]
        }
        for item_id in ["temperature", "humidity"]
        for ts in future_timestamps
    ])

    # Predict next steps directly
    forecast = predictor.predict(tsdf, known_covariates=known_covariates)

    # Pretty print ﹣ first few rows
    print("\n=== Next steps (mean forecast) ===")
    print(
        forecast.reset_index()
                .pivot(index="timestamp", columns="item_id", values="mean")
                .head(10)
    )
    
    # Print forecast details
    print(f"\nForecast shape: {forecast.shape}")
    print(f"Prediction length: {PRED_STEPS} steps")
    print(f"Forecast time range: {forecast.index.get_level_values('timestamp').min()} to {forecast.index.get_level_values('timestamp').max()}")

if __name__ == "__main__":
    main()