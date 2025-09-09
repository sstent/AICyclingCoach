from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class PlanBase(BaseModel):
    jsonb_plan: dict = Field(..., description="Training plan data in JSONB format")
    version: int = Field(..., gt=0, description="Plan version number")
    parent_plan_id: Optional[int] = Field(None, description="Parent plan ID for evolution tracking")

class PlanCreate(PlanBase):
    pass

class Plan(PlanBase):
    id: int
    created_at: datetime
    analyses: List["Analysis"] = Field([], description="Analyses that created this plan version")
    child_plans: List["Plan"] = Field([], description="Evolved versions of this plan")

    class Config:
        orm_mode = True