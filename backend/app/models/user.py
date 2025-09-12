from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    
    # Note: Relationship removed as Plan model doesn't have user_id field
    # plans = relationship("Plan", back_populates="user")