"""
Merges cleaned sensor data and weather data into a single file for ML.
"""
import pandas as pd

# Load sensor and weather data
sensor_df = pd.read_csv('data/sensor_data.csv', parse_dates=['timestamp'])
weather_df = pd.read_csv('data/weather_data.csv', parse_dates=['timestamp'])

# Merge on timestamp using nearest match (within 1 hour)
merged_df = pd.merge_asof(
    sensor_df.sort_values('timestamp'),
    weather_df.sort_values('timestamp'),
    on='timestamp',
    direction='nearest',
    tolerance=pd.Timedelta('1H')
)

# Drop rows where weather data was not found (optional, for strictness)
merged_df = merged_df.dropna(subset=['external_temperature'])

merged_df.to_csv('data/merged_data.csv', index=False)
print('Merged data saved to data/merged_data.csv') 