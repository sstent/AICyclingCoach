from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class Plan(BaseModel):
    __tablename__ = "plans"

    jsonb_plan = Column(JSONB, nullable=False)
    version = Column(Integer, nullable=False)
    parent_plan_id = Column(Integer, ForeignKey('plans.id'), nullable=True)

    parent_plan = relationship("Plan", remote_side="Plan.id", backref="child_plans")
    analyses = relationship("Analysis", back_populates="plan", lazy="selectin")
    workouts = relationship("Workout", back_populates="plan", cascade="all, delete-orphan", lazy="selectin")
    rules = relationship("Rule", secondary="plan_rules", back_populates="plans", lazy="selectin")