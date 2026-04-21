# 🌦️ Weather Analytics Dashboard (Flask + ML)

## 📌 Overview

This is a Flask-based weather analytics application that fetches real-time weather data from an external API, processes it, stores it in a database, and provides insights, forecasts, and temperature predictions using machine learning.

---

## 🚀 Features

* 🌍 **Current Weather** – Get real-time weather data for any city
* 📅 **5-Day Forecast** – Aggregated daily forecast from 3-hour interval data
* 🕒 **History Tracking** – Stores past weather data in SQLite
* 🤖 **Prediction (ML)** – Predict next day temperature using Linear Regression
* 📊 **Insights** – View statistics like average, max, min temperature and humidity

---

## 🧠 Tech Stack

* **Backend:** Flask (Python)
* **API:** OpenWeather API
* **Database:** SQLite
* **ML Model:** Linear Regression (scikit-learn)
* **Frontend:** HTML (Jinja templates)

---

## 🔄 Project Flow

User → Flask → External API → Data Cleaning → Database Storage → Processing → Response

---

## 📂 Project Structure

```
weather-app/
│
├── app.py
├── templates/
│     └── index.html
├── data/
│     └── weather.db
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```
git clone https://github.com/your-username/weather-flask-app.git
cd weather-flask-app
```

### 2️⃣ Create virtual environment

```
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install dependencies

```
pip install flask requests numpy scikit-learn
```

### 4️⃣ Set API Key

```
set OPENWEATHER_API_KEY=your_api_key
```

### 5️⃣ Run the app

```
python app.py
```

---

## 🌐 API Endpoints

* `/api/weather/current` → Current weather
* `/api/weather/forecast` → 5-day forecast
* `/api/weather/history` → Past data
* `/api/weather/prediction` → ML prediction
* `/api/weather/insights` → Statistics

---

## 📘 Key Concepts

* Data preprocessing of nested JSON
* Grouping & aggregation of time-series data
* Database storage & retrieval
* Supervised learning (Linear Regression)
* REST API design

---

## 📊 Example Output

```json
{
  "temperature": 34.5,
  "humidity": 70,
  "description": "Clear Sky"
}
```

---

## 🔥 Future Improvements

* Add caching to reduce API calls
* Deploy on cloud (AWS / Render / Railway)
* Add user authentication
* Improve UI/UX

---

## 👨‍💻 Author

Sai Chetan

---

## ⭐ If you like this project

Give it a star on GitHub!

