from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.plan import Plan as PlanModel
from backend.app.models.rule import Rule
from backend.app.schemas.plan import PlanCreate, Plan as PlanSchema, PlanGenerationRequest, PlanGenerationResponse
from backend.app.dependencies import get_ai_service
from backend.app.services.ai_service import AIService
from uuid import UUID, uuid4
from datetime import datetime
from typing import List

router = APIRouter(prefix="/plans", tags=["Training Plans"])

@router.post("/", response_model=PlanSchema)
async def create_plan(
    plan: PlanCreate,
    db: AsyncSession = Depends(get_db)
):
    # Create plan
    db_plan = PlanModel(
        jsonb_plan=plan.jsonb_plan,
        version=plan.version,
        parent_plan_id=plan.parent_plan_id
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

@router.get("/{plan_id}", response_model=PlanSchema)
async def read_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    plan = await db.get(PlanModel, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.get("/", response_model=List[PlanSchema])
async def read_plans(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PlanModel))
    return result.scalars().all()

@router.put("/{plan_id}", response_model=PlanSchema)
async def update_plan(
    plan_id: UUID,
    plan: PlanCreate,
    db: AsyncSession = Depends(get_db)
):
    db_plan = await db.get(PlanModel, plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Update plan fields
    db_plan.jsonb_plan = plan.jsonb_plan
    db_plan.version = plan.version
    db_plan.parent_plan_id = plan.parent_plan_id
    
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    plan = await db.get(PlanModel, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    await db.delete(plan)
    await db.commit()
    return {"detail": "Plan deleted"}

@router.post("/generate", response_model=PlanGenerationResponse)
async def generate_plan(
    request: PlanGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Generate a new training plan using AI based on provided goals and rule set.
    """
    try:
        # Get all rules from the provided rule IDs
        rules = []
        for rule_id in request.rule_ids:
            rule = await db.get(Rule, rule_id)
            if not rule:
                raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")
            rules.append(rule.jsonb_rules)
        
        # Generate plan using AI service
        generated_plan = await ai_service.generate_training_plan(
            rule_set=rules,  # Pass all rules as a list
            goals=request.goals.model_dump(),
            preferred_routes=request.preferred_routes
        )
        
        # Create a Plan object for the response
        plan_obj = PlanSchema(
            id=uuid4(),  # Generate a proper UUID
            jsonb_plan=generated_plan,
            version=1,
            parent_plan_id=None,
            created_at=datetime.utcnow()
        )
        
        # Create response with generated plan
        response = PlanGenerationResponse(
            plan=plan_obj,
            generation_metadata={
                "status": "success",
                "generated_at": datetime.utcnow().isoformat(),
                "rule_ids": [str(rule_id) for rule_id in request.rule_ids]
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan: {str(e)}"
        )