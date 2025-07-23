"""
Extracts clean sensor readings from raw CSV for downstream ML pipeline.
"""
import pandas as pd

input_file = 'data/ubi_data.csv'
output_file = 'data/sensor_data.csv'

rows = []
with open(input_file, 'r') as f:
    for line in f:
        if line.startswith('DATA_LOG:'):
            ts, temp, hum = line.replace('DATA_LOG:', '').strip().split(',')
            rows.append((ts, float(temp), float(hum)))

sensor_df = pd.DataFrame(rows, columns=['timestamp', 'temperature', 'humidity'])
sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])
sensor_df.to_csv(output_file, index=False)
print(f'Preprocessed sensor data saved to {output_file}') 