import google.generativeai as genai
import os
from dotenv import load_dotenv
from tools import (
    get_nearest_landmark,
    get_weather_at_crash,
    get_speed_limit,
    analyze_gps_data,
    determine_severity,
)

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def format_gps_data(readings: list) -> str:
    formatted = ""
    for i, entry in enumerate(readings):
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



def build_prompt(
    gps_data_str:   str,
    analysis:       dict,
    landmark:       str,
    weather:        str,
    speed_limit:    str,
    severity_info:  dict,
) -> str:
    return f"""
You are a certified Accident Reconstruction Analyst and Forensic Engineer.
You have been given raw blackbox GPS data and pre-analyzed context from multiple tools.

════════════════════════════════════════════
        TOOL RESULTS (PRE-ANALYZED)
════════════════════════════════════════════

📍 NEAREST LANDMARK   : {landmark}
🌤️  WEATHER AT CRASH  : {weather}
🚦 SPEED LIMIT        : {speed_limit}
💥 MAX SPEED          : {analysis['max_speed_kmph']} km/h
💥 PRE-CRASH SPEED    : {analysis['pre_crash_speed']} km/h
💥 SPEED DROP         : {analysis['speed_drop_kmph']} km/h
💥 CRASH TIMESTAMP    : {analysis['crash_timestamp']}
🛰️  SATELLITES LOST   : {analysis['satellites_lost']}
⚠️  SEVERITY          : {severity_info['severity']}
🏥 INJURY RISK        : {severity_info['injuries']}
🚨 EMERGENCY NEEDED   : {severity_info['emergency']}

════════════════════════════════════════════
     GPS BLACKBOX DATA (ALL READINGS)
════════════════════════════════════════════
{gps_data_str}

════════════════════════════════════════════
     ACCIDENT RECONSTRUCTION REPORT
════════════════════════════════════════════

Generate a complete forensic accident reconstruction report with these sections:

SECTION 1: PRE-ACCIDENT ANALYSIS
- Speed trend, driver behavior, motion pattern

SECTION 2: CRASH MOMENT IDENTIFICATION
- Exact timestamp, speed at impact, GPS coordinates, satellite status

SECTION 3: PROBABLE CAUSE OF ACCIDENT
- Primary cause, impact direction, overspeeding assessment, road conditions

SECTION 4: POST-ACCIDENT ANALYSIS
- Post-impact movement, final resting state, satellite loss explanation

SECTION 5: ACCIDENT SEVERITY ASSESSMENT
- Severity rating, injury risk, emergency response required

SECTION 6: RECONSTRUCTION SUMMARY
- Full narrative paragraph
- Event timeline with timestamps [T-Xs], [T-0], [T+Xs], [Final]

Base ALL conclusions strictly on the provided data.
Use exact numerical values from the data.
State CANNOT BE DETERMINED if data is insufficient.
"""



async def run_accident_agent(readings: list, session_id: str) -> dict:
    print(f"\n🤖 BlackBox Agent starting for session: {session_id}")
    print("─" * 50)

    # ── Step 1: Analyze GPS data
    print("📊 Tool 1: Analyzing GPS data...")
    analysis = analyze_gps_data(readings)
    print(f"   Max Speed: {analysis['max_speed_kmph']} km/h")
    print(f"   Crash at : {analysis['crash_timestamp']}")

    crash_lat = analysis.get("crash_lat")
    crash_lon = analysis.get("crash_lon")

    # ── Step 2: Get nearest landmark
    print("📍 Tool 2: Fetching nearest landmark...")
    if crash_lat and crash_lon:
        landmark = await get_nearest_landmark(crash_lat, crash_lon)
    else:
        landmark = "Crash location not determined from GPS data"
    print(f"   {landmark}")

    # ── Step 3: Get weather
    print("🌤️  Tool 3: Fetching weather at crash site...")
    if crash_lat and crash_lon:
        weather = await get_weather_at_crash(crash_lat, crash_lon)
    else:
        weather = "Weather data unavailable — crash location not determined"
    print(f"   {weather}")

    # ── Step 4: Get speed limit
    print("🚦 Tool 4: Fetching road speed limit...")
    if crash_lat and crash_lon:
        speed_limit = await get_speed_limit(crash_lat, crash_lon)
    else:
        speed_limit = "Speed limit unavailable — crash location not determined"
    print(f"   {speed_limit}")

    # ── Step 5: Determine severity
    print("⚠️  Tool 5: Determining accident severity...")
    severity_info = determine_severity(
        speed_drop=analysis["speed_drop_kmph"],
        max_speed=analysis["max_speed_kmph"],
    )
    print(f"   Severity: {severity_info['severity']}")

    # ── Step 6: Build prompt + call Gemini
    print("🤖 Tool 6: Sending to Gemini AI for reconstruction...")
    gps_data_str = format_gps_data(readings)
    prompt = build_prompt(
        gps_data_str=gps_data_str,
        analysis=analysis,
        landmark=landmark,
        weather=weather,
        speed_limit=speed_limit,
        severity_info=severity_info,
    )

    response     = model.generate_content(prompt)
    report_text  = response.text

    print("✅ Agent completed reconstruction!")
    print("─" * 50)

    # ── Return full result
    return {
        "session_id":        session_id,
        "crash_gps":         f"Lat: {crash_lat}, Lon: {crash_lon}" if crash_lat else "Not detected",
        "nearest_landmark":  landmark,
        "weather_at_crash":  weather,
        "speed_limit":       speed_limit,
        "severity":          severity_info["severity"],
        "injury_risk":       severity_info["injuries"],
        "emergency":         severity_info["emergency"],
        "analysis":          analysis,
        "report_text":       report_text,
    }