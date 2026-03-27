from pydantic import BaseModel
from typing import Optional, List


class GPSReading(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    altitude_m: float
    speed_kmph: float
    satellites: int


class AccidentReport(BaseModel):
    session_id: str
    crash_gps: Optional[str] = None
    nearest_landmark: Optional[str] = None
    weather_at_crash: Optional[str] = None
    speed_limit: Optional[str] = None
    report_text: str
    severity: Optional[str] = None
    generated_at: str