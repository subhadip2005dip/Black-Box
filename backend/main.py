from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Database import gps_collection, reports_collection
from models import GPSReading
from agents import run_accident_agent
from datetime import datetime
from bson import ObjectId
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LandmarkResponse(BaseModel):
    name: str
    type: str
    address: str
    latitude: float
    longitude: float
    distance_meters: float | None = None

def serialize(doc: dict) -> dict:
    """Convert MongoDB ObjectId to string."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@app.get("/nearest-landmark", response_model=LandmarkResponse)
async def get_nearest_landmark(
    lat: float = Query(..., description="Latitude of the location", ge=-90, le=90),
    lon: float = Query(..., description="Longitude of the location", ge=-180, le=180),
):
    """
    Returns the nearest landmark to the given latitude and longitude.

    Uses OpenStreetMap's Nominatim reverse geocoding API (free, no API key required).
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 17,
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NearestLandmarkAPI/1.0; +https://github.com/0x-rekt/nearest-landmark-api)"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Nominatim API error: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not reach Nominatim: {e}")

    data = response.json()

    if "error" in data:
        raise HTTPException(status_code=404, detail=f"No landmark found: {data['error']}")

    address_parts = data.get("address", {})

    address_fields = [
        address_parts.get("road"),
        address_parts.get("suburb") or address_parts.get("neighbourhood"),
        address_parts.get("city") or address_parts.get("town") or address_parts.get("village"),
        address_parts.get("state"),
        address_parts.get("country"),
    ]
    address = ", ".join(part for part in address_fields if part)

    name = (
        data.get("name")
        or address_parts.get("amenity")
        or address_parts.get("tourism")
        or address_parts.get("leisure")
        or address_parts.get("building")
        or address_parts.get("road")
        or address_parts.get("suburb")
        or address_parts.get("neighbourhood")
        or address_parts.get("city")
        or address_parts.get("town")
        or address_parts.get("village")
        or "Unknown landmark"
    )

    landmark_type = data.get("type") or data.get("class") or "unknown"

    return LandmarkResponse(
        name=name,
        type=landmark_type,
        address=address,
        latitude=float(data["lat"]),
        longitude=float(data["lon"]),
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/upload-gps", status_code=status.HTTP_201_CREATED, tags=["GPS"])
async def upload_gps(readings: list[GPSReading], session_id: str):
    """Upload GPS blackbox readings for a session."""

    if not readings:
        raise HTTPException(status_code=400, detail="No GPS readings provided")

    data = [r.model_dump() for r in readings]
    for d in data:
        d["session_id"] = session_id


    existing = await gps_collection.find_one({"session_id": session_id})
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Session '{session_id}' already exists. Use a different session_id."
        )

    await gps_collection.insert_many(data)
    return {
        "message":    f"✅ {len(data)} GPS readings uploaded successfully",
        "session_id": session_id,
        "readings":   len(data)
    }

@app.get("/gps/{session_id}", tags=["GPS"])
async def get_gps(session_id: str):
    """Get all GPS readings for a session."""
    readings = await gps_collection.find(
        {"session_id": session_id},
        {"_id": 0}
    ).to_list(10000)

    if not readings:
        raise HTTPException(status_code=404, detail=f"No GPS data found for session '{session_id}'")

    return {
        "session_id": session_id,
        "total":      len(readings),
        "readings":   readings
    }



@app.post("/reconstruct/{session_id}", tags=["Agent"])
async def reconstruct_accident(session_id: str):
    """
    🤖 Run the AI Agent to reconstruct the accident.

    The agent will:
    1. Analyze GPS data
    2. Find nearest landmark (OpenStreetMap)
    3. Get weather at crash site (Open-Meteo)
    4. Get road speed limit (Overpass API)
    5. Determine severity
    6. Generate full report (Gemini AI)
    7. Save report to MongoDB
    """


    readings = await gps_collection.find(
        {"session_id": session_id},
        {"_id": 0, "session_id": 0}
    ).to_list(10000)

    if not readings:
        raise HTTPException(
            status_code=404,
            detail=f"No GPS data found for session '{session_id}'. Upload GPS data first."
        )

    # Run the agent
    result = await run_accident_agent(readings, session_id)

    # Save report to MongoDB
    report_doc = {
        **result,
        "generated_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    await reports_collection.insert_one(report_doc)

    return {
        "message":          "✅ Accident reconstruction complete",
        "session_id":       session_id,
        "severity":         result["severity"],
        "crash_gps":        result["crash_gps"],
        "nearest_landmark": result["nearest_landmark"],
        "weather_at_crash": result["weather_at_crash"],
        "speed_limit":      result["speed_limit"],
        "injury_risk":      result["injury_risk"],
        "emergency":        result["emergency"],
        "report":           result["report_text"],
        "generated_at":     report_doc["generated_at"],

        "confidence"      : result["confidence"],
        "confidence_pct"  : result["confidence_pct"],
        "google_maps_link": result["google_maps_link"],
        "weather_risk"    : result["weather_risk"],
        "road_type"       : result["road_type"],
        "confirmed_facts" : result["confirmed_facts"],
        "unavailable_data": result["unavailable_data"],
        "legal_note"      : result["legal_note"],
        "data_sources"    : result["data_sources"],
        "crash_timestamp" : result["crash_timestamp"],
        "max_speed_kmph"  : result["max_speed_kmph"],
        "speed_drop_kmph" : result["speed_drop_kmph"],
        
        
    }


@app.get("/report/{session_id}", tags=["Reports"])
async def get_report(session_id: str):
    """Get a previously generated accident report."""
    report = await reports_collection.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for session '{session_id}'. Run /reconstruct first."
        )
    return report



@app.get("/sessions", tags=["Sessions"])
async def get_all_sessions():
    """Get all uploaded sessions."""
    sessions = await gps_collection.distinct("session_id")
    return {
        "total":    len(sessions),
        "sessions": sessions
    }



@app.delete("/session/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """Delete a session and its report."""
    gps_result    = await gps_collection.delete_many({"session_id": session_id})
    report_result = await reports_collection.delete_many({"session_id": session_id})

    if gps_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return {
        "message":          f"✅ Session '{session_id}' deleted",
        "gps_deleted":      gps_result.deleted_count,
        "reports_deleted":  report_result.deleted_count
    }
