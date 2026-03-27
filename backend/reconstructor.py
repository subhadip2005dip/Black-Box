import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def get_blackbox_data():
    return [
        {
            "timestamp": "15/03/2026  08:45:00",
            "latitude": 22.572646,
            "longitude": 88.363895,
            "altitude_m": 12.5,
            "speed_kmph": 65.3,
            "satellites": 8,
        },
        {
            "timestamp": "15/03/2026  08:45:01",
            "latitude": 22.572700,
            "longitude": 88.363950,
            "altitude_m": 12.4,
            "speed_kmph": 70.1,
            "satellites": 8,
        },
        {
            "timestamp": "15/03/2026  08:45:02",
            "latitude": 22.572760,
            "longitude": 88.364010,
            "altitude_m": 12.3,
            "speed_kmph": 78.5,
            "satellites": 8,
        },
        {
            "timestamp": "15/03/2026  08:45:03",
            "latitude": 22.572820,
            "longitude": 88.364080,
            "altitude_m": 12.2,
            "speed_kmph": 85.2,
            "satellites": 7,
        },
        {
            "timestamp": "15/03/2026  08:45:04",
            "latitude": 22.572860,
            "longitude": 88.364120,
            "altitude_m": 12.1,
            "speed_kmph": 92.7,
            "satellites": 7,
        },
        {
            "timestamp": "15/03/2026  08:45:05",
            "latitude": 22.572880,
            "longitude": 88.364140,
            "altitude_m": 11.8,
            "speed_kmph": 95.4,
            "satellites": 6,
        },
        {
            "timestamp": "15/03/2026  08:45:06",
            "latitude": 22.572890,
            "longitude": 88.364150,
            "altitude_m": 10.2,
            "speed_kmph": 45.0,
            "satellites": 5,
        },
        {
            "timestamp": "15/03/2026  08:45:07",
            "latitude": 22.572895,
            "longitude": 88.364155,
            "altitude_m": 8.5,
            "speed_kmph": 10.0,
            "satellites": 4,
        },
        {
            "timestamp": "15/03/2026  08:45:08",
            "latitude": 22.572895,
            "longitude": 88.364155,
            "altitude_m": 8.5,
            "speed_kmph": 0.0,
            "satellites": 4,
        },
    ]


def format_gps_data(data):
    formatted = ""
    for i, entry in enumerate(data):
        formatted += f"""
Reading {i+1}:
  Timestamp  : {entry['timestamp']}
  Latitude   : {entry['latitude']}
  Longitude  : {entry['longitude']}
  Altitude   : {entry['altitude_m']} m
  Speed      : {entry['speed_kmph']} km/h
  Satellites : {entry['satellites']}
"""
    return formatted


def get_crash_gps(data):                          # Fixed Bug 1
    for entry in data:
        if entry['speed_kmph'] == 0.0:
            return f"Lat: {entry['latitude']}, Lng: {entry['longitude']}, Time: {entry['timestamp']}"
    return "Not available"

# ─────────────────────────────────────────
# Accident Reconstruction Prompt
# ─────────────────────────────────────────
def build_prompt(gps_data_str,                    # Fixed Bug 2
                 imu_data_str="No IMU data available",
                 gps_coordinates_if_available="Not available"):
    return f"""
You are a certified Accident Reconstruction Analyst and Forensic Engineer 
with expertise in vehicle dynamics, biomechanics, road physics, and 
embedded sensor data interpretation.

You have been provided with raw blackbox data captured by an IoT-based 
Event Data Recorder (EDR) mounted on a two-wheeler. The data was recorded 
continuously at 100Hz and covers the pre-crash, crash, and post-crash phases.

Your task is to perform a thorough, evidence-based accident reconstruction 
using ONLY the data provided. Do not make assumptions beyond what the data supports.

════════════════════════════════════════════
             DEVICE & SENSOR CONTEXT
════════════════════════════════════════════
Device          : MPU6050 (6-DOF IMU)
Sampling Rate   : 100Hz (one reading every 10ms)
Accel Range     : ±16g (X = forward/backward,
                        Y = left/right,
                        Z = up/down)
Gyro Range      : ±500°/s (Roll, Pitch, Yaw)
Gravity Axis    : Primarily X-axis (~9.81 m/s² at rest)
Velocity        : Numerically integrated from (ax, ay, az)
GPS Module      : Neo-6M (latitude, longitude, speed, altitude)

Crash Detection Criteria (ALL must be met within 200ms window):
  ✔ Peak Acceleration  ≥ 8g
  ✔ Delta-V            ≥ 4 m/s
  ✔ Jerk               ≥ 30 g/s

════════════════════════════════════════════
        GPS DATA AT CRASH MOMENT
════════════════════════════════════════════
{gps_coordinates_if_available}

════════════════════════════════════════════
     GPS BLACKBOX DATA (PRE + POST CRASH)
════════════════════════════════════════════
{gps_data_str}

════════════════════════════════════════════
  IMU BLACKBOX DATA (PRE + POST CRASH 100Hz)
════════════════════════════════════════════
{imu_data_str}

════════════════════════════════════════════
     ACCIDENT RECONSTRUCTION REPORT
════════════════════════════════════════════

Using the sensor data above, generate a structured forensic report 
with the following sections:

──────────────────────────────────────────
SECTION 1 : PRE-ACCIDENT ANALYSIS
──────────────────────────────────────────
Analyze the vehicle's state BEFORE the crash event:

  • Overall motion trend        : Was the vehicle calm, accelerating, 
                                  braking, or maneuvering?
  • Most active axis            : Which accelerometer axis showed the 
                                  highest activity? What does this indicate 
                                  about the vehicle's direction of travel?
  • Pre-impact anomalies        : Was there unusual jerk, vibration, or 
                                  sudden directional change before impact?
  • Driver behavior assessment  : Based on throttle/braking patterns 
                                  visible in the data, describe the 
                                  driver's behavior (alert, distracted, 
                                  aggressive, panic braking, etc.)
  • Speed trend                 : Was the vehicle speeding up or slowing 
                                  down before impact?

──────────────────────────────────────────
SECTION 2 : CRASH MOMENT IDENTIFICATION
──────────────────────────────────────────
Pinpoint the exact moment of impact:

  • Crash timestamp             : Exact time of impact from data
  • Peak acceleration           : Maximum g-force recorded (in g)
  • Peak jerk                   : Maximum rate of acceleration change (g/s)
  • Delta-V                     : Total velocity change during impact (m/s)
  • Crash GPS coordinates       : Latitude & Longitude (if available)
  • Crash confirmation          : Does the data meet ALL 3 crash detection 
                                  criteria? State clearly YES or NO with values.

──────────────────────────────────────────
SECTION 3 : PROBABLE CAUSE OF ACCIDENT
──────────────────────────────────────────
Determine the most likely cause:

  • Primary cause               : What does the acceleration signature 
                                  suggest as the main cause?
                                  (e.g., frontal collision, side impact, 
                                   rollover, hard braking, skid, pothole)
  • Impact direction            : Based on which axis spiked most — 
                                  was the impact FRONTAL, LATERAL, 
                                  REAR, or ROLLOVER?
  • Overspeeding assessment     : Was the vehicle exceeding safe speed 
                                  limits based on GPS speed data?
  • Road condition indicators   : Any signs of skidding or instability 
                                  before impact?
  • Contributing factors        : Any secondary factors visible in data

──────────────────────────────────────────
SECTION 4 : POST-ACCIDENT ANALYSIS
──────────────────────────────────────────
Analyze the vehicle's state AFTER the crash:

  • Post-impact movement        : Did the vehicle continue moving 
                                  after impact? In which direction?
  • Stabilization time          : How long did it take for sensor 
                                  readings to return to near-rest values?
  • Final resting orientation   : Based on gravity axis shift in 
                                  accelerometer data, is the vehicle 
                                  upright, tilted, or overturned?
  • GPS satellite loss          : If satellites dropped, explain why 
                                  (antenna blockage due to vehicle 
                                  orientation change)

──────────────────────────────────────────
SECTION 5 : ACCIDENT SEVERITY ASSESSMENT
──────────────────────────────────────────
Rate the severity and potential injuries:

  • Severity rating             : Minor / Moderate / Severe / Critical
  • Justification               : Based on peak g-force, delta-V, 
                                  and jerk rate
  • Estimated injury risk       : Based on the deceleration profile, 
                                  what injuries are likely?
                                  (e.g., whiplash, head trauma, 
                                   fractures, fatal risk)
  • Emergency response needed   : YES or NO — and what level 
                                  (ambulance, fire brigade, police)

──────────────────────────────────────────
SECTION 6 : RECONSTRUCTION SUMMARY
──────────────────────────────────────────
Provide a complete narrative of the accident:

  • Narrative paragraph         : Write a clear, concise paragraph 
                                  describing EXACTLY what happened — 
                                  from the vehicle's normal operation 
                                  to the final resting state.
  • Event timeline              : List key events with timestamps:
      [T-Xs] → Vehicle state before crash
      [T-0 ] → Crash moment
      [T+Xs] → Post-crash state
      [Final] → Resting state

──────────────────────────────────────────
IMPORTANT GUIDELINES
──────────────────────────────────────────
  ✔ Base ALL conclusions strictly on provided sensor data
  ✔ Clearly state "CANNOT BE DETERMINED FROM AVAILABLE DATA" 
    if any conclusion is not supported by data
  ✔ Use precise numerical values from the data in your analysis
  ✔ Distinguish between CONFIRMED findings and PROBABLE findings
  ✔ Flag if crash detection criteria were NOT fully met.
"""

# ─────────────────────────────────────────
# Main Accident Reconstructor
# ─────────────────────────────────────────
def reconstruct_accident():
    print("=" * 60)
    print("       BLACKBOX ACCIDENT RECONSTRUCTOR")
    print("       Powered by Google Generative AI")
    print("=" * 60)

    # Step 1 - Get blackbox data
    print("\n Reading BlackBox GPS Data...")
    blackbox_data = get_blackbox_data()
    print(f" {len(blackbox_data)} GPS readings loaded!")

    # Step 2 - Format data
    print("\n Processing GPS data...")
    gps_data_str = format_gps_data(blackbox_data)

    # Step 3 - Get crash GPS coordinates       # Fixed Bug 1
    crash_gps = get_crash_gps(blackbox_data)

    # Step 4 - Build prompt                    # Fixed Bug 3
    prompt = build_prompt(
        gps_data_str=gps_data_str,
        imu_data_str="No IMU data available — GPS only mode",
        gps_coordinates_if_available=crash_gps
    )

    
    print("\n🤖 Sending data to AI for reconstruction...")
    print("─" * 60)
    response = model.generate_content(prompt)

    # Step 6 - Print Report
    print("\n" + "=" * 60)
    print("        ACCIDENT RECONSTRUCTION REPORT")
    print("=" * 60)
    print(response.text)
    print("=" * 60)
    print(f"\n📅 Report Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    reconstruct_accident()