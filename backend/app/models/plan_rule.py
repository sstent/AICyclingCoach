from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class PlanRule(BaseModel):
    __tablename__ = "plan_rules"
    
    plan_id = Column(Integer, ForeignKey('plans.id'), primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), primary_key=True)
    
    plan = relationship("Plan", back_populates="rules")
    rule = relationship("Rule", back_populates="plans")