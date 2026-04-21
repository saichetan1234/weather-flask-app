from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
import sqlite3
import json
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "demo")
BASE_URL = "http://api.openweathermap.org/data/2.5"
DB_PATH = "data/weather.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            temperature REAL,
            feels_like REAL,
            humidity INTEGER,
            wind_speed REAL,
            description TEXT,
            timestamp TEXT,
            is_forecast INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_to_db(city, data, is_forecast=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO weather_history 
        (city, temperature, feels_like, humidity, wind_speed, description, timestamp, is_forecast)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        city,
        data.get("temperature"),
        data.get("feels_like"),
        data.get("humidity"),
        data.get("wind_speed"),
        data.get("description"),
        data.get("timestamp"),
        1 if is_forecast else 0
    ))

    conn.commit()
    conn.close()


def get_history_from_db(city, days=7):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    since = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute("""
        SELECT * FROM weather_history
        WHERE city = ? AND timestamp >= ? AND is_forecast = 0
        ORDER BY timestamp ASC
    """, (city.lower(), since))

    rows = cursor.fetchall()
    conn.close()

    result = []

    for row in rows:
        result.append({
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "wind_speed": row["wind_speed"],
            "description": row["description"],
            "timestamp": row["timestamp"]
        })

    return result


def fetch_current_weather(city):
    url = f"{BASE_URL}/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.RequestException:
        return None

    return {
        "city": raw["name"],
        "country": raw["sys"]["country"],
        "temperature": round(raw["main"]["temp"], 1),
        "feels_like": round(raw["main"]["feels_like"], 1),
        "humidity": raw["main"]["humidity"],
        "wind_speed": raw["wind"]["speed"],
        "description": raw["weather"][0]["description"].title(),
        "icon": raw["weather"][0]["icon"],
        "timestamp": datetime.now().isoformat(),
        "pressure": raw["main"]["pressure"],
        "visibility": raw.get("visibility", 0) / 1000
    }


def fetch_forecast(city):
    url = f"{BASE_URL}/forecast"
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.RequestException:
        return []

    daily = {}

    for item in raw["list"]:
        date = item["dt_txt"].split(" ")[0]

        if date not in daily:
            daily[date] = []

        daily[date].append({
            "temp": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "description": item["weather"][0]["description"].title(),
            "icon": item["weather"][0]["icon"]
        })

    result = []
    for date, readings in daily.items():
        temps = [r["temp"] for r in readings]

        result.append({
            "date": date,
            "temp_max": round(max(temps), 1),
            "temp_min": round(min(temps), 1),
            "temp_avg": round(sum(temps) / len(temps), 1),
            "humidity": round(sum(r["humidity"] for r in readings) / len(readings)),
            "description": readings[len(readings)//2]["description"],
            "icon": readings[len(readings)//2]["icon"]
        })

    return result[:5]


def compute_regression(history):
    if len(history) < 3:
        return None

    temps = [h["temperature"] for h in history]

    X = np.array(range(len(temps))).reshape(-1, 1)
    y = np.array(temps)

    model = LinearRegression()
    model.fit(X, y)

    next_day = np.array([[len(temps)]])
    prediction = model.predict(next_day)[0]

    return {
        "predicted_temp": round(float(prediction), 1),
        "trend": "rising" if model.coef_[0] > 0.1 else ("falling" if model.coef_[0] < -0.1 else "stable"),
        "confidence": min(len(history) / 10.0, 1.0)
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/weather/current")
def get_current_weather():
    city = request.args.get("city", "London")

    if API_KEY == "demo":
        data = get_mock_weather(city)
    else:
        data = fetch_current_weather(city)

    if not data:
        return jsonify({"error": "City not found"}), 404

    save_to_db(city.lower(), data)
    return jsonify(data)


@app.route("/api/weather/forecast")
def get_forecast():
    city = request.args.get("city", "London")

    if API_KEY == "demo":
        data = get_mock_forecast(city)
    else:
        data = fetch_forecast(city)

    return jsonify(data)


@app.route("/api/weather/history")
def get_history():
    city = request.args.get("city", "London")
    days = int(request.args.get("days", 7))

    history = get_history_from_db(city, days)

    if len(history) < 3:
        history = get_mock_history(city)

    return jsonify(history)


@app.route("/api/weather/prediction")
def get_prediction():
    city = request.args.get("city", "London")
    history = get_history_from_db(city, days=14)

    if len(history) < 3:
        history = get_mock_history(city)

    prediction = compute_regression(history)

    if not prediction:
        return jsonify({"error": "Not enough data"}), 400

    return jsonify(prediction)


@app.route("/api/weather/insights")
def get_insights():
    city = request.args.get("city", "London")
    history = get_history_from_db(city, days=7)

    if len(history) < 3:
        history = get_mock_history(city)

    temps = [h["temperature"] for h in history]
    humidities = [h["humidity"] for h in history]

    insights = {
        "avg_temp": round(sum(temps) / len(temps), 1),
        "max_temp": round(max(temps), 1),
        "min_temp": round(min(temps), 1),
        "temp_range": round(max(temps) - min(temps), 1),
        "avg_humidity": round(sum(humidities) / len(humidities)),
        "data_points": len(history)
    }

    return jsonify(insights)


def get_mock_weather(city):
    import random

    base_temp = {"london": 12, "paris": 15, "tokyo": 18, "mumbai": 32, "new york": 10, "chennai": 34}
    temp = base_temp.get(city.lower(), 22) + random.uniform(-3, 3)

    return {
        "city": city.title(),
        "country": "Demo",
        "temperature": round(temp, 1),
        "feels_like": round(temp - 2, 1),
        "humidity": random.randint(40, 85),
        "wind_speed": round(random.uniform(2, 15), 1),
        "description": random.choice(["Clear Sky", "Partly Cloudy", "Light Rain", "Sunny"]),
        "icon": "01d",
        "timestamp": datetime.now().isoformat(),
        "pressure": random.randint(1000, 1025),
        "visibility": round(random.uniform(5, 15), 1)
    }


def get_mock_forecast(city):
    import random
    forecast = []
    base_temp = 22

    for i in range(5):
        date = (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")

        forecast.append({
            "date": date,
            "temp_max": round(base_temp + random.uniform(0, 5), 1),
            "temp_min": round(base_temp - random.uniform(2, 6), 1),
            "temp_avg": round(base_temp + random.uniform(-1, 2), 1),
            "humidity": random.randint(45, 80),
            "description": random.choice(["Sunny", "Cloudy", "Light Rain", "Clear Sky"]),
            "icon": random.choice(["01d", "02d", "10d", "03d"])
        })

    return forecast


def get_mock_history(city):
    import random
    history = []
    base_temp = {"london": 12, "paris": 15, "tokyo": 18, "mumbai": 32, "chennai": 34}.get(city.lower(), 22)

    for i in range(14):
        ts = (datetime.now() - timedelta(days=13-i)).isoformat()

        history.append({
            "temperature": round(base_temp + random.uniform(-4, 4) + i * 0.1, 1),
            "humidity": random.randint(40, 85),
            "wind_speed": round(random.uniform(2, 15), 1),
            "description": random.choice(["Clear Sky", "Cloudy", "Light Rain"]),
            "timestamp": ts
        })

    return history


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)