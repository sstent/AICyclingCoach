from pydantic import BaseModel
from typing import Optional, Dict, Any


class AnalysisBase(BaseModel):
    workout_id: int
    analysis_type: str = 'workout_review'
    jsonb_feedback: Optional[Dict[str, Any]] = None
    suggestions: Optional[Dict[str, Any]] = None
    approved: bool = False


class AnalysisCreate(AnalysisBase):
    pass


class Analysis(AnalysisBase):
    id: int

    class Config:
        from_attributes = True


class AnalysisUpdate(BaseModel):
    approved: bool