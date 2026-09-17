import requests
import sqlite3
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 1. Setup Paths (Consistent with your folder structure)
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "environment_data.db")

# 2. API Keys from your .env
WEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
UV_KEY = os.getenv("OPENUV_API_KEY")

# OpenUV needs Latitude/Longitude
# OpenUV needs Latitude/Longitude
LOCATIONS = {
    "Hamburg": {"lat": 53.5511, "lng": 9.9937},
    "London": {"lat": 51.5074, "lng": -0.1278},
    "Berlin": {"lat": 52.5200, "lng": 13.4050},
    "Istanbul": {"lat": 41.0082, "lng": 28.9784}
}

def fetch_environment_data(city, lat, lng):
    # 1. Weather (Working fine)
    w_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={WEATHER_KEY}&units=metric"
    w_response = requests.get(w_url)
    w_data = w_response.json()

    # 2. UV Index (Quota exceeded)
    uv_url = f"https://api.openuv.io/api/v1/uv?lat={lat}&lng={lng}"
    uv_headers = {"x-access-token": UV_KEY}
    uv_response = requests.get(uv_url, headers=uv_headers)
    uv_data = uv_response.json()

    # 3. THE SAFETY GATE
    # Initialize values to 0 in case the API fails
    uv_val = 0
    uv_max_val = 0
    
    if "result" in uv_data:
        uv_val = uv_data["result"]["uv"]
        uv_max_val = uv_data["result"]["uv_max"]
    else:
        # Log the error but don't let the script crash
        error_msg = uv_data.get("error", "Quota Exceeded or Unknown Error")
        print(f"⚠️ Skipping UV for {city}: {error_msg}")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city": city,
        "temp": w_data["main"]["temp"],
        "desc": w_data["weather"][0]["description"],
        "uv_index": uv_val,
        "uv_max": uv_max_val
    }

def save_to_sqlite(data):
    conn = None
    try:
        # 1. Establish connection
        # Tip: Use an absolute path if you keep seeing duplicate .db files
        conn = sqlite3.connect('environment_data.db')
        cursor = conn.cursor()

        # 2. SCHEMA INITIALIZATION (The Bootstrap)
        # This prevents the "no such table" error if the script crashed during setup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                city TEXT,
                temp_c REAL,
                description TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uv_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                city TEXT,
                uv_index REAL,
                uv_max REAL
            )
        """)

        # 3. DATA INSERTION
        cursor.execute("""
            INSERT INTO weather (timestamp, city, temp_c, description) 
            VALUES (?, ?, ?, ?)
        """, (data['timestamp'], data['city'], data['temp'], data['desc']))

        cursor.execute("""
            INSERT INTO uv_data (timestamp, city, uv_index, uv_max) 
            VALUES (?, ?, ?, ?)
        """, (data['timestamp'], data['city'], data['uv_index'], data['uv_max']))

        # 4. COMMIT
        conn.commit()
        print(f"✅ Data for {data['city']} saved successfully.")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback() # Undo changes if one insert fails but the other succeeds

    finally:
        # 5. UNLOCK THE DATABASE
        # This block runs NO MATTER WHAT. It prevents the "Database is locked" error.
        if conn:
            conn.close()

# --- MAIN LOOP ---
print(f"🚀 Logger started. Saving to: {DB_PATH}")

try:
    while True:
        for city, coords in LOCATIONS.items():
            try:
                print(f"Fetching {city}...")
                results = fetch_environment_data(city, coords['lat'], coords['lng'])
                save_to_sqlite(results)
                print(f"✅ Saved {city}: Temp {results['temp']}°C, UV {results['uv_index']}")
            except Exception as e:
                print(f"❌ Error fetching {city}: {e}")
        
        print("Sleeping for 2 hours to protect API limits...")
        time.sleep(7200)

except KeyboardInterrupt:
    print("Stopped by user.")