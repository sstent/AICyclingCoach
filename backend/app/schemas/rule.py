from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class NaturalLanguageRuleRequest(BaseModel):
    """Request schema for natural language rule parsing."""
    natural_language_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Natural language rule description"
    )
    rule_name: str = Field(..., min_length=1, max_length=100, description="Rule set name")
    
    @field_validator('natural_language_text')
    @classmethod
    def validate_text_content(cls, v):
        required_keywords = ['ride', 'week', 'hour', 'day', 'rest', 'training']
        if not any(keyword in v.lower() for keyword in required_keywords):
            raise ValueError("Text must contain training-related keywords")
        return v

class ParsedRuleResponse(BaseModel):
    """Response schema for parsed rules."""
    parsed_rules: Dict[str, Any] = Field(..., description="Structured rule data")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Parsing confidence")
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")
    validation_errors: List[str] = Field(default=[], description="Validation errors")
    rule_name: str = Field(..., description="Rule set name")

class RuleBase(BaseModel):
    """Base rule schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    user_defined: bool = Field(True, description="Whether rule is user-defined")
    rule_text: str = Field(..., min_length=10, description="Plaintext rule description")
    version: int = Field(1, ge=1, description="Rule version")
    parent_rule_id: Optional[UUID] = Field(None, description="Parent rule for versioning")

class RuleCreate(RuleBase):
    pass

class Rule(RuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}