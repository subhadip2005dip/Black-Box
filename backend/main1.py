from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from Database import gps_collection, reports_collection
from models import GPSReading
from agent import run_accident_agent
from datetime import datetime
from bson import ObjectId

app = FastAPI(
    title="🚨 BlackBox Accident Reconstructor Agent",
    description="AI-powered accident reconstruction using GPS blackbox data",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize(doc: dict) -> dict:
    """Convert MongoDB ObjectId to string."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc



@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "🚨 BlackBox Accident Reconstructor Agent",
        "status":  "running",
        "docs":    "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}



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
        "generated_at":     report_doc["generated_at"]
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