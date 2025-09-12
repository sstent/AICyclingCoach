from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel


class Analysis(BaseModel):
    """Analysis model for AI-generated workout feedback."""
    __tablename__ = "analyses"

    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    analysis_type = Column(String(50), default='workout_review')
    jsonb_feedback = Column(JSON, nullable=False)
    suggestions = Column(JSON)
    approved = Column(Boolean, default=False)
    created_plan_id = Column(Integer, ForeignKey('plans.id'))
    approved_at = Column(DateTime, default=datetime.utcnow)  # Changed from server_default=func.now()
    
    # Relationships
    workout = relationship("Workout", back_populates="analyses")
    plan = relationship("Plan", back_populates="analyses")