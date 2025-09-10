from sqlalchemy import Column, Integer, ForeignKey, Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class Rule(BaseModel):
    __tablename__ = "rules"
    
    name = Column(String(100), nullable=False)
    user_defined = Column(Boolean, default=True)
    jsonb_rules = Column(JSONB, nullable=False)
    version = Column(Integer, default=1)
    parent_rule_id = Column(Integer, ForeignKey('rules.id'), nullable=True)

    parent_rule = relationship("Rule", remote_side="Rule.id")