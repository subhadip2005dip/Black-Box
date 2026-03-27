import httpx
from typing import Optional

#1
async def get_nearest_landmark(lat: float, lon: float) -> str:
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
        return f"Nearest Landmark: {full_address} | Coordinates: {lat}, {lon}"

    except Exception as e:
        return f"Could not fetch landmark: {str(e)}"


#2
async def get_weather_at_crash(lat: float, lon: float) -> str:
    """Get weather conditions at crash coordinates using Open-Meteo (free, no API key)."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "visibility,precipitation,windspeed_10m",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            data = response.json()

        weather = data.get("current_weather", {})
        temp        = weather.get("temperature", "N/A")
        windspeed   = weather.get("windspeed", "N/A")
        weathercode = weather.get("weathercode", "N/A")

        # Map weather codes to descriptions
        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
            3: "Overcast", 45: "Fog", 51: "Light drizzle",
            61: "Slight rain", 63: "Moderate rain", 71: "Slight snow",
            80: "Rain showers", 95: "Thunderstorm"
        }
        condition = weather_descriptions.get(weathercode, f"Code {weathercode}")

        return (
            f"Weather at crash site: {condition} | "
            f"Temperature: {temp}°C | "
            f"Wind Speed: {windspeed} km/h"
        )

    except Exception as e:
        return f"Could not fetch weather: {str(e)}"


#3
async def get_speed_limit(lat: float, lon: float) -> str:
    """Get road speed limit using OpenStreetMap Overpass API."""
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        way(around:50,{lat},{lon})[highway][maxspeed];
        out body;
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(overpass_url, data={"data": query}, timeout=15)
            data = response.json()

        elements = data.get("elements", [])
        if elements:
            maxspeed = elements[0].get("tags", {}).get("maxspeed", "Not available")
            highway  = elements[0].get("tags", {}).get("highway", "Unknown road type")
            return f"Road Type: {highway} | Speed Limit: {maxspeed}"
        return "Speed limit: Not available for this location"

    except Exception as e:
        return f"Could not fetch speed limit: {str(e)}"


#4
def analyze_gps_data(readings: list) -> dict:
    """Analyze GPS readings to find crash moment and key stats."""

    crash_entry     = None
    max_speed       = 0
    pre_crash_speed = 0
    speed_drop      = 0

    for i, entry in enumerate(readings):
        speed = entry.get("speed_kmph", 0)

        if speed > max_speed:
            max_speed = speed

        # Detect crash — sudden speed drop to 0
        if speed == 0.0 and i > 0:
            crash_entry     = entry
            pre_crash_speed = readings[i - 1].get("speed_kmph", 0)
            speed_drop      = pre_crash_speed - speed
            break

    satellites_lost = False
    if readings:
        initial_sats = readings[0].get("satellites", 8)
        final_sats   = readings[-1].get("satellites", 8)
        satellites_lost = final_sats < initial_sats

    return {
        "max_speed_kmph":     max_speed,
        "pre_crash_speed":    pre_crash_speed,
        "speed_drop_kmph":    speed_drop,
        "crash_timestamp":    crash_entry.get("timestamp") if crash_entry else "Not detected",
        "crash_lat":          crash_entry.get("latitude")  if crash_entry else None,
        "crash_lon":          crash_entry.get("longitude") if crash_entry else None,
        "satellites_lost":    satellites_lost,
        "total_readings":     len(readings),
    }


#5
def determine_severity(speed_drop: float, max_speed: float) -> dict:
    """Determine accident severity based on speed data."""

    if speed_drop >= 80 or max_speed >= 100:
        severity   = "CRITICAL"
        injuries   = "Fatal risk — severe head trauma, multiple fractures, internal bleeding"
        emergency  = "Ambulance + Fire Brigade + Police immediately"
    elif speed_drop >= 50 or max_speed >= 70:
        severity   = "SEVERE"
        injuries   = "High risk — whiplash, fractures, concussion likely"
        emergency  = "Ambulance required immediately"
    elif speed_drop >= 25 or max_speed >= 40:
        severity   = "MODERATE"
        injuries   = "Moderate risk — whiplash, bruising, possible fractures"
        emergency  = "Medical attention recommended"
    else:
        severity   = "MINOR"
        injuries   = "Low risk — minor bruising, possible whiplash"
        emergency  = "Self-assessment recommended, see doctor if pain persists"

    return {
        "severity":  severity,
        "injuries":  injuries,
        "emergency": emergency
    }