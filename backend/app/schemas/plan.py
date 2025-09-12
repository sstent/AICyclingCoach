from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

class TrainingGoals(BaseModel):
    """Training goals for plan generation."""
    primary_goal: str = Field(..., description="Primary training goal")
    target_weekly_hours: int = Field(..., ge=3, le=20, description="Target hours per week")
    fitness_level: str = Field(..., description="Current fitness level")
    event_date: Optional[str] = Field(None, description="Target event date (YYYY-MM-DD)")
    preferred_routes: List[int] = Field(default=[], description="Preferred route IDs")
    avoid_days: List[str] = Field(default=[], description="Days to avoid training")

class PlanBase(BaseModel):
    jsonb_plan: Dict[str, Any] = Field(..., description="Training plan data in JSONB format")
    version: int = Field(..., gt=0, description="Plan version number")
    parent_plan_id: Optional[UUID] = Field(None, description="Parent plan ID for evolution tracking")

class PlanCreate(PlanBase):
    pass

class Plan(PlanBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    model_config = {"from_attributes": True}

class PlanGenerationRequest(BaseModel):
    """Request schema for plan generation."""
    rule_ids: List[int] = Field(..., description="Rule set IDs to apply")
    goals: TrainingGoals = Field(..., description="Training goals")
    duration_weeks: int = Field(4, ge=1, le=20, description="Plan duration in weeks")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences")
    preferred_routes: List[int] = Field(default=[], description="Preferred route IDs")

class PlanGenerationResponse(BaseModel):
    """Response schema for plan generation."""
    plan: Plan
    generation_metadata: Dict[str, Any] = Field(..., description="Generation metadata")
    
    model_config = {"from_attributes": True}