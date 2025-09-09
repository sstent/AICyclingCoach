from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class WorkoutMetric(BaseModel):
    timestamp: datetime
    heart_rate: Optional[int] = None
    power: Optional[float] = None
    cadence: Optional[float] = None

class WorkoutBase(BaseModel):
    garmin_activity_id: str
    activity_type: Optional[str] = None
    start_time: datetime
    duration_seconds: Optional[int] = None
    distance_m: Optional[float] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    avg_power: Optional[float] = None
    max_power: Optional[float] = None
    avg_cadence: Optional[float] = None
    elevation_gain_m: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None


class WorkoutCreate(WorkoutBase):
    plan_id: Optional[int] = None


class Workout(WorkoutBase):
    id: int
    plan_id: Optional[int] = None

    class Config:
        orm_mode = True


class WorkoutSyncStatus(BaseModel):
    status: str
    last_sync_time: Optional[datetime] = None
    activities_synced: int = 0
    error_message: Optional[str] = None

    class Config:
        orm_mode = True