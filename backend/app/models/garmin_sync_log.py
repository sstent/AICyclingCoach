from sqlalchemy import Column, Integer, DateTime, String, Text, Enum
from .base import BaseModel
import enum


class GarminSyncStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AUTH_FAILED = "auth_failed"
    FAILED = "failed"


class GarminSyncLog(BaseModel):
    """Log model for tracking Garmin sync operations."""
    __tablename__ = "garmin_sync_log"

    last_sync_time = Column(DateTime)
    activities_synced = Column(Integer, default=0)
    status = Column(Enum(GarminSyncStatus), default=GarminSyncStatus.PENDING)
    error_message = Column(Text)