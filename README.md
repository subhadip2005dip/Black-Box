<<<<<<< HEAD
# 🚨 Black-Box — AI-Powered Accident Reconstruction System
=======
# Hlo Welcome to your Lovable project
>>>>>>> 0d6c0d5ad8184c9bbf06ef0e8950ff07755fd8f4

> An IoT-based Event Data Recorder (EDR) that automatically detects vehicle accidents, reconstructs them using AI, and sends emergency alerts — powered by ESP32, MPU6050, Neo-6M GPS, FastAPI, MongoDB, and Google Gemini AI.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Hardware Components](#hardware-components)
- [Software Stack](#software-stack)
- [System Architecture](#system-architecture)
- [Hardware Wiring](#hardware-wiring)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [API Documentation](#api-documentation)
- [How It Works](#how-it-works)
- [Future Roadmap](#future-roadmap)

---

## 🧠 Overview

**Black-Box** is an intelligent accident detection and reconstruction system inspired by aircraft flight recorders. It is mounted on a two-wheeler and continuously records GPS and IMU sensor data. When a crash is detected, it:

1. 📡 Captures real-time GPS + IMU data via ESP32
2. 💥 Automatically detects the accident using sensor thresholds
3. 🤖 Sends data to an AI agent for full forensic reconstruction
4. 🗄️ Stores all data and reports in MongoDB
5. 🚨 Sends emergency alerts with crash location

---

## 🔧 Hardware Components

| Component | Model | Purpose |
|-----------|-------|---------|
| Microcontroller | ESP32 | Main processing unit, WiFi data transmission |
| IMU Sensor | MPU6050 | Measures acceleration (±16g) and gyroscope (±500°/s) |
| GPS Module | Neo-6M | Captures latitude, longitude, speed, altitude |
| Power Supply | LiPo Battery | Portable power for the device |

### Crash Detection Criteria
All three must be met within a **200ms window**:

```
✔ Peak Acceleration  ≥ 8g
✔ Delta-V            ≥ 4 m/s
✔ Jerk               ≥ 30 g/s
```

### Sensor Specifications

**MPU6050 (IMU):**
- Sampling Rate: 100Hz (one reading every 10ms)
- Accelerometer Range: ±16g
  - X-axis → Forward/Backward
  - Y-axis → Left/Right
  - Z-axis → Up/Down
- Gyroscope Range: ±500°/s (Roll, Pitch, Yaw)

**Neo-6M (GPS):**
- Output: Latitude, Longitude, Speed (km/h), Altitude (m)
- Satellites: Tracks up to 8+ satellites
- Update Rate: 1Hz

---

## 🔌 Hardware Wiring

### ESP32 → MPU6050

```
ESP32           MPU6050
─────────────────────────
3.3V     →     VCC
GND      →     GND
GPIO 21  →     SDA
GPIO 22  →     SCL
```

### ESP32 → Neo-6M GPS

```
ESP32           Neo-6M
──────────────────────────
5V       →     VCC
GND      →     GND
GPIO 16  →     TX (GPS)
GPIO 17  →     RX (GPS)
```

---

## 💻 Software Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Firmware | ESP32 (MicroPython/Arduino) | Sensor data collection |
| Backend | FastAPI (Python) | REST API |
| Database | MongoDB + Motor | Store GPS data & reports |
| AI Agent | Google Gemini 2.5 Flash | Accident reconstruction |
| HTTP Client | HTTPX | External API calls |
| Geocoding | OpenStreetMap Nominatim | Nearest landmark |
| Weather | Open-Meteo API | Weather at crash site |
| Road Data | Overpass API (OSM) | Speed limits |
| Validation | Pydantic | Data models |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   HARDWARE LAYER                     │
│                                                     │
│   MPU6050 ──┐                                       │
│             ├──► ESP32 ──► WiFi ──► FastAPI         │
│   Neo-6M  ──┘                                       │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   BACKEND LAYER                      │
│                                                     │
│   FastAPI                                           │
│     ├── POST /upload-gps   → Save to MongoDB        │
│     ├── POST /reconstruct  → Run AI Agent           │
│     ├── GET  /report       → Fetch Report           │
│     └── DELETE /session    → Clean up               │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                    AI AGENT LAYER                    │
│                                                     │
│   Tool 1: Analyze GPS Data                          │
│   Tool 2: Get Nearest Landmark (OpenStreetMap)      │
│   Tool 3: Get Weather at Crash (Open-Meteo)         │
│   Tool 4: Get Road Speed Limit (Overpass API)       │
│   Tool 5: Determine Severity                        │
│   Tool 6: Generate Report (Google Gemini AI)        │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   DATABASE LAYER                     │
│                                                     │
│   MongoDB                                           │
│     ├── gps_readings   → Raw sensor data            │
│     └── reports        → AI reconstruction reports  │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Black-Box/
├── backend/
│   ├── main.py              # FastAPI endpoints
│   ├── agent.py             # AI agent orchestrator
│   ├── tools.py             # Agent tools (landmark, weather, etc.)
│   ├── Database.py          # MongoDB connection
│   ├── models.py            # Pydantic data models
│   ├── reconstructor.py     # Accident reconstruction logic
│   ├── requirements.txt     # Python dependencies
│   └── Sample Data.json     # Sample GPS data for testing
├── frontend/                # Frontend (coming soon)
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- MongoDB running on `localhost:27017`
- Google Gemini API key ([Get one here](https://aistudio.google.com))

### Steps

**1. Clone the repository:**
```bash
git clone https://github.com/subhajitchakraborty23/Black-Box.git
cd Black-Box/backend
```

**2. Create and activate virtual environment:**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Create `.env` file:**
```env
GOOGLE_API_KEY=your_google_api_key_here
MONGO_URL=mongodb://localhost:27017
```

**5. Run the server:**
```bash
uvicorn main:app --reload
```

**6. Open API docs:**
```
http://localhost:8000/docs
```

---

## 📡 API Documentation

### Upload GPS Data
```http
POST /upload-gps?session_id=session_001
Content-Type: application/json

[
  {
    "timestamp": "15/03/2026 08:45:00",
    "latitude": 22.572646,
    "longitude": 88.363895,
    "altitude_m": 12.5,
    "speed_kmph": 65.3,
    "satellites": 8
  }
]
```

### Run AI Reconstruction
```http
POST /reconstruct/session_001
```

### Get Report
```http
GET /report/session_001
```

### Get All Sessions
```http
GET /sessions
```

### Delete Session
```http
DELETE /session/session_001
```

---

## 🤖 How It Works

```
1. ESP32 reads MPU6050 + Neo-6M at 100Hz
          ↓
2. Crash detected (acceleration ≥ 8g, delta-V ≥ 4 m/s, jerk ≥ 30 g/s)
          ↓
3. GPS + IMU data sent to FastAPI via WiFi
          ↓
4. Data stored in MongoDB (gps_readings collection)
          ↓
5. AI Agent triggered:
   ├── Analyzes GPS data → finds crash moment
   ├── Fetches nearest landmark (OpenStreetMap)
   ├── Fetches weather at crash site (Open-Meteo)
   ├── Fetches road speed limit (Overpass API)
   ├── Determines severity (Minor/Moderate/Severe/Critical)
   └── Generates full forensic report (Google Gemini AI)
          ↓
6. Report saved to MongoDB (reports collection)
          ↓
7. Emergency alert sent with crash location 🚨
```

---

## 🗺️ Future Roadmap

- [ ] Add IMU data integration (MPU6050 acceleration + gyroscope)
- [ ] Real-time dashboard (Frontend)
- [ ] SMS/Email emergency alerts
- [ ] Mobile app for live tracking
- [ ] Deploy to cloud (Railway / Render)
- [ ] Add OTA (Over The Air) firmware updates for ESP32
- [ ] Multi-vehicle support

---

## 👨‍💻 Author

**Subhajit Chakraborty**
- GitHub: [@subhajitchakraborty23](https://github.com/subhajitchakraborty23)

---

## 📄 License

This project is licensed under the MIT License.