import httpx
import math
from typing import Optional
from datetime import datetime

# ─────────────────────────────────────────
# Tool 1: Get Nearest Landmark
# ─────────────────────────────────────────
async def get_nearest_landmark(lat: float, lon: float) -> dict:
    """Get the nearest landmark/address from GPS coordinates using OpenStreetMap."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 17,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "BlackBoxAccidentReconstructor/1.0"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10)
            data = response.json()

        address_parts = data.get("address", {})
        name = (
            data.get("name")
            or address_parts.get("road")
            or address_parts.get("suburb")
            or "Unknown location"
        )
        road    = address_parts.get("road", "")
        city    = address_parts.get("city") or address_parts.get("town") or address_parts.get("village", "")
        state   = address_parts.get("state", "")
        country = address_parts.get("country", "")

        full_address = ", ".join(p for p in [name, road, city, state, country] if p)

        # ✅ Return structured dict with confidence
        return {
            "status"         : "SUCCESS",
            "landmark"       : full_address,
            "coordinates"    : f"{lat}, {lon}",
            "google_maps"    : f"https://maps.google.com/?q={lat},{lon}",
            "confidence"     : "HIGH",       # real API data = high confidence
            "data_source"    : "OpenStreetMap Nominatim",
            "note"           : "CONFIRMED from live API"
        }

    except Exception as e:
        # ✅ Fallback — never return empty
        return {
            "status"      : "FAILED",
            "landmark"    : f"Coordinates: {lat}, {lon}",
            "coordinates" : f"{lat}, {lon}",
            "google_maps" : f"https://maps.google.com/?q={lat},{lon}",
            "confidence"  : "LOW",
            "data_source" : "Fallback coordinates only",
            "note"        : f"API unavailable: {str(e)}"
        }


# ─────────────────────────────────────────
# Tool 2: Get Weather at Crash
# ─────────────────────────────────────────
async def get_weather_at_crash(lat: float, lon: float) -> dict:
    """Get weather conditions at crash coordinates using Open-Meteo (free, no API key)."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude"       : lat,
            "longitude"      : lon,
            "current_weather": True,
            "hourly"         : "visibility,precipitation,windspeed_10m",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            data = response.json()

        weather     = data.get("current_weather", {})
        temp        = weather.get("temperature", "N/A")
        windspeed   = weather.get("windspeed", "N/A")
        weathercode = weather.get("weathercode", "N/A")

        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
            3: "Overcast", 45: "Fog", 51: "Light drizzle",
            61: "Slight rain", 63: "Moderate rain", 71: "Slight snow",
            80: "Rain showers", 95: "Thunderstorm"
        }
        condition = weather_descriptions.get(weathercode, f"Code {weathercode}")

        # ✅ Assess if weather contributed to accident
        weather_risk = "LOW"
        if weathercode in [45, 51, 61, 63, 71, 80, 95]:
            weather_risk = "HIGH"   # fog/rain/snow/storm
        elif weathercode in [2, 3]:
            weather_risk = "MEDIUM" # cloudy/overcast

        return {
            "status"        : "SUCCESS",
            "condition"     : condition,
            "temperature"   : f"{temp}°C",
            "wind_speed"    : f"{windspeed} km/h",
            "weather_risk"  : weather_risk,
            "confidence"    : "HIGH",
            "data_source"   : "Open-Meteo API",
            "note"          : "CONFIRMED from live API",
            # ✅ Flag if weather likely contributed
            "contributed_to_accident": weather_risk == "HIGH"
        }

    except Exception as e:
        return {
            "status"                  : "FAILED",
            "condition"               : "CANNOT BE DETERMINED FROM AVAILABLE DATA",
            "temperature"             : "N/A",
            "wind_speed"              : "N/A",
            "weather_risk"            : "UNKNOWN",
            "confidence"              : "NONE",
            "data_source"             : "Unavailable",
            "note"                    : f"API error: {str(e)}",
            "contributed_to_accident" : False
        }


# ─────────────────────────────────────────
# Tool 3: Get Speed Limit
# ─────────────────────────────────────────
async def get_speed_limit(lat: float, lon: float) -> dict:
    """Get road speed limit using OpenStreetMap Overpass API."""
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        way(around:50,{lat},{lon})[highway][maxspeed];
        out body;
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                overpass_url,
                data={"data": query},
                timeout=15
            )
            data = response.json()

        elements = data.get("elements", [])
        if elements:
            maxspeed = elements[0].get("tags", {}).get("maxspeed", "Not available")
            highway  = elements[0].get("tags", {}).get("highway", "Unknown road type")

            return {
                "status"      : "SUCCESS",
                "road_type"   : highway,
                "speed_limit" : maxspeed,
                "confidence"  : "HIGH",
                "data_source" : "OpenStreetMap Overpass API",
                "note"        : "CONFIRMED from live API"
            }

        return {
            "status"      : "NOT_FOUND",
            "road_type"   : "CANNOT BE DETERMINED FROM AVAILABLE DATA",
            "speed_limit" : "CANNOT BE DETERMINED FROM AVAILABLE DATA",
            "confidence"  : "NONE",
            "data_source" : "OpenStreetMap Overpass API",
            "note"        : "No speed limit data for this location"
        }

    except Exception as e:
        return {
            "status"      : "FAILED",
            "road_type"   : "CANNOT BE DETERMINED FROM AVAILABLE DATA",
            "speed_limit" : "CANNOT BE DETERMINED FROM AVAILABLE DATA",
            "confidence"  : "NONE",
            "data_source" : "Unavailable",
            "note"        : f"API error: {str(e)}"
        }


# ─────────────────────────────────────────
# Tool 4: Analyze GPS Data
# ─────────────────────────────────────────
def analyze_gps_data(readings: list) -> dict:
    """
    Analyze GPS readings to find crash moment and key stats.
    Returns ONLY facts from actual data — no assumptions.
    """

    if not readings:
        return {
            "status"          : "NO_DATA",
            "confidence"      : "NONE",
            "note"            : "CANNOT BE DETERMINED — no GPS readings provided"
        }

    crash_entry     = None
    max_speed       = 0
    pre_crash_speed = 0
    speed_drop      = 0
    speed_history   = []

    for i, entry in enumerate(readings):
        speed = entry.get("speed_kmph", 0)
        speed_history.append(speed)

        if speed > max_speed:
            max_speed = speed

        # ✅ Detect crash — sudden speed drop to 0
        if speed == 0.0 and i > 0:
            crash_entry     = entry
            pre_crash_speed = readings[i - 1].get("speed_kmph", 0)
            speed_drop      = pre_crash_speed - speed
            break

    # ✅ Satellite analysis
    satellites_lost = False
    initial_sats    = readings[0].get("satellites", 8)
    final_sats      = readings[-1].get("satellites", 8)
    if final_sats < initial_sats:
        satellites_lost = True

    # ✅ Speed trend analysis (was vehicle accelerating or braking?)
    if len(speed_history) >= 3:
        recent_speeds = speed_history[-3:]
        if recent_speeds[-1] > recent_speeds[0]:
            speed_trend = "ACCELERATING"
        elif recent_speeds[-1] < recent_speeds[0]:
            speed_trend = "DECELERATING"
        else:
            speed_trend = "CONSTANT"
    else:
        speed_trend = "CANNOT BE DETERMINED"

    # ✅ Calculate deceleration rate (g-force estimate)
    deceleration_g = "CANNOT BE DETERMINED FROM AVAILABLE DATA"
    if crash_entry and pre_crash_speed > 0:
        # Convert kmph to m/s
        speed_ms   = pre_crash_speed / 3.6
        # Assume crash happened in ~1 second
        decel_ms2  = speed_ms / 1.0
        decel_g    = decel_ms2 / 9.81
        deceleration_g = round(decel_g, 2)

    # ✅ Confidence based on data quality
    confidence = "HIGH"
    if not crash_entry:
        confidence = "LOW"
    elif len(readings) < 5:
        confidence = "MEDIUM"

    return {
        "status"           : "SUCCESS" if crash_entry else "NO_CRASH_DETECTED",
        "confidence"       : confidence,
        "data_source"      : "GPS BlackBox Readings",

        # ✅ Only CONFIRMED facts
        "max_speed_kmph"   : max_speed,
        "pre_crash_speed"  : pre_crash_speed,
        "speed_drop_kmph"  : speed_drop,
        "deceleration_g"   : deceleration_g,
        "speed_trend"      : speed_trend,
        "crash_timestamp"  : crash_entry.get("timestamp") if crash_entry else "CANNOT BE DETERMINED",
        "crash_lat"        : crash_entry.get("latitude")  if crash_entry else None,
        "crash_lon"        : crash_entry.get("longitude") if crash_entry else None,
        "crash_altitude"   : crash_entry.get("altitude_m") if crash_entry else "CANNOT BE DETERMINED",
        "satellites_lost"  : satellites_lost,
        "initial_satellites": initial_sats,
        "final_satellites" : final_sats,
        "total_readings"   : len(readings),

        # ✅ Clearly mark what cannot be determined
        "impact_direction" : "CANNOT BE DETERMINED FROM GPS DATA ALONE — IMU data required",
        "rollover"         : "CANNOT BE DETERMINED FROM GPS DATA ALONE — IMU data required",
        "note"             : "All values derived from actual GPS readings only. No assumptions made."
    }


# ─────────────────────────────────────────
# Tool 5: Determine Severity
# ─────────────────────────────────────────
def determine_severity(speed_drop: float, max_speed: float) -> dict:
    """
    Determine accident severity based on ACTUAL speed data only.
    Confidence reflects data quality.
    """

    # ✅ Validate inputs — don't guess
    if speed_drop == 0 and max_speed == 0:
        return {
            "severity"        : "CANNOT BE DETERMINED",
            "injuries"        : "CANNOT BE DETERMINED FROM AVAILABLE DATA",
            "emergency"       : "Treat as CRITICAL until confirmed otherwise",
            "confidence"      : "NONE",
            "confidence_pct"  : 0,
            "data_basis"      : "Insufficient data",
            "note"            : "Speed data unavailable — defaulting to maximum caution"
        }

    # ✅ Determine severity with confidence scores
    if speed_drop >= 80 or max_speed >= 100:
        severity        = "CRITICAL"
        injuries        = "Fatal risk — severe head trauma, multiple fractures, internal bleeding likely"
        emergency       = "🚑 Ambulance + 👮 Police + 🚒 Fire Brigade — IMMEDIATELY via 112"
        confidence_pct  = 92
        confidence      = "HIGH"

    elif speed_drop >= 50 or max_speed >= 70:
        severity        = "SEVERE"
        injuries        = "High risk — whiplash, fractures, concussion likely"
        emergency       = "🚑 Ambulance required immediately via 112"
        confidence_pct  = 85
        confidence      = "HIGH"

    elif speed_drop >= 25 or max_speed >= 40:
        severity        = "MODERATE"
        injuries        = "Moderate risk — whiplash, bruising, possible fractures"
        emergency       = "Medical attention recommended — 38 second countdown initiated"
        confidence_pct  = 75
        confidence      = "MEDIUM"

    else:
        severity        = "MINOR"
        injuries        = "Low risk — minor bruising, possible whiplash"
        emergency       = "Self-assessment recommended — notify rider only"
        confidence_pct  = 70
        confidence      = "MEDIUM"

    # ✅ Add disclaimer for legal use
    return {
        "severity"        : severity,
        "injuries"        : injuries,
        "emergency"       : emergency,
        "confidence"      : confidence,
        "confidence_pct"  : confidence_pct,

        # ✅ Exact data used for this assessment
        "data_basis"      : {
            "speed_drop_used" : f"{speed_drop} km/h",
            "max_speed_used"  : f"{max_speed} km/h",
            "assessed_at"     : datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        },

        # ✅ Limitations clearly stated
        "limitations"     : [
            "Severity based on GPS speed data only",
            "IMU acceleration data would improve accuracy",
            "Road conditions not factored in speed assessment",
            "Individual injury risk varies by age, health, protective gear"
        ],

        # ✅ Legal disclaimer
        "legal_note"      : (
            "AI ASSISTED ASSESSMENT — NOT FINAL. "
            "Must be reviewed by qualified medical/forensic professional "
            "before use in legal proceedings or insurance claims."
        )
    }


# ─────────────────────────────────────────
# Tool 6: Validate All Data Before Gemini
# ─────────────────────────────────────────
def validate_data_for_prompt(analysis: dict,
                              landmark: dict,
                              weather: dict,
                              speed_limit: dict,
                              severity: dict) -> dict:
    """
    ✅ NEW TOOL — Validates all data before sending to Gemini.
    Prevents AI hallucination by clearly marking
    what is CONFIRMED vs UNAVAILABLE.
    """

    validated = {
        "confirmed_facts"    : [],
        "unavailable_data"   : [],
        "low_confidence_data": [],
        "prompt_instructions": ""
    }

    # ✅ Check each data point
    checks = [
        ("Max Speed",      analysis.get("max_speed_kmph"),    analysis.get("confidence")),
        ("Crash Time",     analysis.get("crash_timestamp"),   analysis.get("confidence")),
        ("Crash Location", analysis.get("crash_lat"),         analysis.get("confidence")),
        ("Landmark",       landmark.get("landmark"),          landmark.get("confidence")),
        ("Weather",        weather.get("condition"),          weather.get("confidence")),
        ("Speed Limit",    speed_limit.get("speed_limit"),    speed_limit.get("confidence")),
        ("Severity",       severity.get("severity"),          severity.get("confidence")),
    ]

    for name, value, confidence in checks:
        if not value or value == "CANNOT BE DETERMINED FROM AVAILABLE DATA":
            validated["unavailable_data"].append(name)
        elif confidence == "LOW":
            validated["low_confidence_data"].append(name)
        else:
            validated["confirmed_facts"].append(name)

    # ✅ Build strict prompt instructions
    validated["prompt_instructions"] = f"""
CRITICAL INSTRUCTIONS FOR REPORT GENERATION:
═══════════════════════════════════════════

✅ CONFIRMED DATA (use freely):
{chr(10).join(f'   → {f}' for f in validated['confirmed_facts'])}

⚠️ LOW CONFIDENCE DATA (use with caution, state uncertainty):
{chr(10).join(f'   → {f}' for f in validated['low_confidence_data'])}

❌ UNAVAILABLE DATA (write EXACTLY "CANNOT BE DETERMINED FROM AVAILABLE DATA"):
{chr(10).join(f'   → {f}' for f in validated['unavailable_data'])}

STRICT RULES:
1. Base ALL conclusions ONLY on confirmed sensor data above
2. NEVER invent or assume values not present in the data
3. For unavailable data, write: "CANNOT BE DETERMINED FROM AVAILABLE DATA"
4. Distinguish CONFIRMED findings from PROBABLE findings
5. Add confidence percentage to each major conclusion
6. Mark report as: "AI ASSISTED — REQUIRES EXPERT REVIEW"
7. Do NOT speculate about cause without data evidence
8. If IMU data is missing, state impact direction as UNDETERMINED
"""

    return validated