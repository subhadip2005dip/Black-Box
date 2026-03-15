from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx

app = FastAPI()

class LandmarkResponse(BaseModel):
    name: str
    type: str
    address: str
    latitude: float
    longitude: float
    distance_meters: float | None = None


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
