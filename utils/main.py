"""
Runs the full ML pipeline: preprocess, fetch weather, merge, train.
"""
import subprocess

steps = [
    ("Preprocessing sensor data", ["python", "utils/preprocess_sensor.py"]),
    ("Fetching weather data", ["python", "utils/fetch_weather.py"]),
    ("Merging sensor and weather data", ["python", "utils/merge_data.py"]),
    ("Training model", ["python", "utils/train.py"]),
]

for desc, cmd in steps:
    print(f"\n=== {desc} ===")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Step failed: {desc}")
        exit(result.returncode)

print("\nAll steps completed! You can now run the app with:")
print("streamlit run utils/app.py") 