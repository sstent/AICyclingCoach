from sqlalchemy import Column, Integer, ForeignKey, Boolean, String, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Rule(BaseModel):
    __tablename__ = "rules"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_defined = Column(Boolean, default=True)
    rule_text = Column(Text, nullable=False)  # Plaintext rules as per design spec
    version = Column(Integer, default=1)
    parent_rule_id = Column(Integer, ForeignKey('rules.id'), nullable=True)

    parent_rule = relationship("Rule", remote_side="Rule.id")
    plans = relationship("Plan", secondary="plan_rules", back_populates="rules", lazy="selectin")