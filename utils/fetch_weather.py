"""
Fetches historical weather data for Siegen, Germany using Open-Meteo API and saves as weather_data.csv.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta

# Siegen, Germany coordinates
LAT = 50.8748
LON = 8.0243

# Read sensor data to get date range (robust to mixed lines)
dates = []
with open('data/ubi_data.csv', 'r') as f:
    for line in f:
        if line.startswith('DATA_LOG:'):
            ts = line.replace('DATA_LOG:', '').strip().split(',')[0]
            dates.append(ts)
dates = pd.to_datetime(dates)
start_date = dates.min().date()
end_date = dates.max().date()

# Open-Meteo API endpoint
BASE_URL = 'https://archive-api.open-meteo.com/v1/archive'

params = {
    'latitude': LAT,
    'longitude': LON,
    'start_date': start_date.isoformat(),
    'end_date': end_date.isoformat(),
    'hourly': ','.join([
        'temperature_2m',
        'relative_humidity_2m',
        'wind_speed_10m',
        'precipitation',
        'cloudcover'
    ]),
    'timezone': 'auto'
}

print(f"Fetching weather data for {start_date} to {end_date}...")
response = requests.get(BASE_URL, params=params)
response.raise_for_status()
data = response.json()

# Convert to DataFrame
weather_df = pd.DataFrame({
    'timestamp': data['hourly']['time'],
    'external_temperature': data['hourly']['temperature_2m'],
    'external_humidity': data['hourly']['relative_humidity_2m'],
    'wind_speed': data['hourly']['wind_speed_10m'],
    'precipitation': data['hourly']['precipitation'],
    'cloud_cover': data['hourly']['cloudcover']
})
weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])

weather_df.to_csv('data/weather_data.csv', index=False)
print('Weather data saved to data/weather_data.csv') 