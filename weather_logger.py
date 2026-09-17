import os
import sys
import requests
from datetime import datetime

# Direct logging to ensure GitHub Actions shows progress live
def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

log("--- STARTING WEATHER LOGGER ---")

API_KEY = os.getenv("OPENWEATHER_API_KEY")
FILE_NAME = "overnight_weather.csv"
CITIES = ["London", "Hamburg"]

if not API_KEY:
    log("❌ ERROR: API Key not found in environment!")
    sys.exit(1)

all_data = []

with requests.Session() as session:
    for city in CITIES:
        try:
            log(f"📡 Fetching weather for {city}...")
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            response = session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Formatting data to match your original CSV structure
            # timestamp, city, temp, humidity, pressure, wind, description
            row = [
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                city,
                str(data["main"]["temp"]),
                str(data["main"]["humidity"]),
                str(data["main"]["pressure"]),
                str(data["wind"]["speed"]),
                data["weather"][0]["description"]
            ]
            all_data.append(",".join(row))
            log(f"✅ Successfully processed {city}")
            
        except Exception as e:
            log(f"❌ ERROR fetching {city}: {e}")

# Save to file
if all_data:
    try:
        with open(FILE_NAME, "a", encoding="utf-8") as f:
            for line in all_data:
                f.write(line + "\n")
        log(f"💾 Successfully saved {len(all_data)} rows to {FILE_NAME}")
    except Exception as e:
        log(f"❌ FILE ERROR: {e}")
else:
    log("⚠️ No data was collected to save.")

log("--- PROCESS COMPLETE ---")