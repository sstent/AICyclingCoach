from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.rule import Rule
from backend.app.schemas.rule import RuleCreate, Rule as RuleSchema, NaturalLanguageRuleRequest, ParsedRuleResponse
from backend.app.dependencies import get_ai_service
from backend.app.services.ai_service import AIService
from uuid import UUID
from typing import List

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.post("/", response_model=RuleSchema)
async def create_rule(
    rule: RuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new rule set (plaintext) as per design specification."""
    db_rule = Rule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@router.get("/", response_model=List[RuleSchema])
async def list_rules(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List rule sets as specified in design document."""
    query = select(Rule)
    if active_only:
        # For now, return all rules. Later we can add an 'active' field
        pass
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{rule_id}", response_model=RuleSchema)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get specific rule set."""
    rule = await db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.put("/{rule_id}", response_model=RuleSchema)
async def update_rule(
    rule_id: UUID,
    rule: RuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update rule set - creates new version as per design spec."""
    db_rule = await db.get(Rule, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Create new version instead of updating in place
    new_version = Rule(
        name=rule.name,
        description=rule.description,
        user_defined=rule.user_defined,
        rule_text=rule.rule_text,
        version=db_rule.version + 1,
        parent_rule_id=db_rule.id
    )
    
    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)
    return new_version

@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete rule set."""
    rule = await db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    return {"detail": "Rule deleted"}

@router.post("/parse-natural-language", response_model=ParsedRuleResponse)
async def parse_natural_language_rules(
    request: NaturalLanguageRuleRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Parse natural language training rules into structured format using AI.
    This helps users create rules but the final rule_text is stored as plaintext.
    """
    try:
        # Parse rules using AI service - this creates structured data for validation
        parsed_rules = await ai_service.parse_rules_from_natural_language(request.natural_language_text)
        
        # Simple validation - just check for basic completeness
        suggestions = []
        if len(request.natural_language_text.split()) < 10:
            suggestions.append("Consider providing more detailed rules")
        
        response = ParsedRuleResponse(
            parsed_rules=parsed_rules,
            confidence_score=0.8,  # Simplified confidence
            suggestions=suggestions,
            validation_errors=[],  # Simplified - no complex validation
            rule_name=request.rule_name
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse natural language rules: {str(e)}"
        )