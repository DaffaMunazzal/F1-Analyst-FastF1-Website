# 🏎️ F1 Data Analytics Dashboard

![F1 Analytics](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black) ![FastF1](https://img.shields.io/badge/FastF1-Data%20API-red)

A comprehensive, real-time Formula 1 Analytics Platform built with Python and Flask. This dashboard provides deep insights into F1 races, offering interactive telemetry comparisons, live GPS tracking, and visually stunning data representations using the official FastF1 library.

---

## ✨ Key Features

*   📊 **Driver Telemetry Analysis:** Compare speed traces, throttle/brake applications, gear shifts, and RPM between any two drivers in real-time.
*   🗺️ **Live Race Replay:** Watch a fully synchronized GPS replay of the race. Cars move dynamically across the circuit map with accurate gap tracking, sector lines, and highlighted DRS zones.
*   ⏱️ **Lap Times & Pace:** Interactive charts showcasing driver lap times and stint progressions to analyze tyre strategy and race pace.
*   🏁 **Qualifying Results:** Detailed grid positions, Q1, Q2, and Q3 elimination times dynamically updated.
*   🏆 **Championship Standings:** Up-to-date Driver and Constructor leaderboards featuring team colors and aesthetic glassmorphism UI.
*   💾 **Robust ETL Pipeline:** Includes a smart data seeding script to fetch, clean, and store historical and live data directly into a local MySQL database for lightning-fast performance.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your machine:
*   **Python 3.9** or higher
*   **MySQL Server** (XAMPP, Laragon, or standalone MySQL)
*   **Git**

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/f1-analytics.git
cd f1-analytics
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
Install all required Python libraries (including `FastF1`, `Flask`, `Pandas`, `SQLAlchemy`):
```bash
pip install -r requirements.txt
```

### 4. Database Configuration
1. Open your MySQL client (e.g., phpMyAdmin, DBeaver, or MySQL Workbench).
2. Create a new empty database named `f1_analytics`:
   ```sql
   CREATE DATABASE f1_analytics;
   ```
3. *(Optional)* If your MySQL username is not `root` or you use a password, update the credentials in `config.py`.

### 5. Initialize the Database (ETL Pipeline)
To prevent the application from fetching heavy data on the fly, we use an ETL (Extract, Transform, Load) pipeline to download data from the official F1 API and store it in our MySQL database.

Run the seeding script to populate the database with the latest season's data:
```bash
python etl/seed_database.py --year 2025 --rounds 0
```
> **Note:** The `--rounds 0` argument instructs the script to fetch **all available races** for that year. Grab a cup of coffee ☕, as fetching full season telemetry might take a few minutes!

### 6. Run the Application!
Once the database is seeded, start the Flask local server:
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🏎️ How to Use the Analytics Dashboard
1. Navigate to the **Analytics** tab.
2. Select the **Grand Prix** and the **Session** (e.g., Race or Qualifying).
3. Choose two drivers to compare (e.g., *VER - Max Verstappen* vs *NOR - Lando Norris*).
4. Click **Analyze!**
5. Enjoy exploring the interactive telemetry charts and the synced Race Replay map.

---

## 🛡️ License
Distributed under the MIT License. Data provided by the brilliant [FastF1](https://docs.fastf1.dev/) Python library. This project is unofficial and is not associated in any way with the Formula 1 companies.
