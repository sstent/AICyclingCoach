"""
Plan service for TUI application.
Manages training plans and plan generation without HTTP dependencies.
"""
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.plan import Plan
from backend.app.models.rule import Rule
from backend.app.services.ai_service import AIService
from backend.app.services.plan_evolution import PlanEvolutionService


class PlanService:
    """Service for training plan operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_plans(self) -> List[Dict]:
        """Get all training plans."""
        try:
            result = await self.db.execute(
                select(Plan).order_by(desc(Plan.created_at))
            )
            plans = result.scalars().all()
            
            return [
                {
                    "id": p.id,
                    "version": p.version,
                    "parent_plan_id": p.parent_plan_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "plan_data": p.jsonb_plan
                } for p in plans
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching plans: {str(e)}")
    
    async def get_plan(self, plan_id: int) -> Optional[Dict]:
        """Get a specific plan by ID."""
        try:
            plan = await self.db.get(Plan, plan_id)
            if not plan:
                return None
                
            return {
                "id": plan.id,
                "version": plan.version,
                "parent_plan_id": plan.parent_plan_id,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "plan_data": plan.jsonb_plan
            }
            
        except Exception as e:
            raise Exception(f"Error fetching plan {plan_id}: {str(e)}")
    
    async def create_plan(self, plan_data: Dict, version: int = 1, parent_plan_id: Optional[int] = None) -> Dict:
        """Create a new training plan."""
        try:
            db_plan = Plan(
                jsonb_plan=plan_data,
                version=version,
                parent_plan_id=parent_plan_id
            )
            self.db.add(db_plan)
            await self.db.commit()
            await self.db.refresh(db_plan)
            
            return {
                "id": db_plan.id,
                "version": db_plan.version,
                "parent_plan_id": db_plan.parent_plan_id,
                "created_at": db_plan.created_at.isoformat() if db_plan.created_at else None,
                "plan_data": db_plan.jsonb_plan
            }
            
        except Exception as e:
            raise Exception(f"Error creating plan: {str(e)}")
    
    async def update_plan(self, plan_id: int, plan_data: Dict, version: Optional[int] = None) -> Dict:
        """Update an existing plan."""
        try:
            db_plan = await self.db.get(Plan, plan_id)
            if not db_plan:
                raise Exception("Plan not found")
            
            db_plan.jsonb_plan = plan_data
            if version is not None:
                db_plan.version = version
            
            await self.db.commit()
            await self.db.refresh(db_plan)
            
            return {
                "id": db_plan.id,
                "version": db_plan.version,
                "parent_plan_id": db_plan.parent_plan_id,
                "created_at": db_plan.created_at.isoformat() if db_plan.created_at else None,
                "plan_data": db_plan.jsonb_plan
            }
            
        except Exception as e:
            raise Exception(f"Error updating plan: {str(e)}")
    
    async def delete_plan(self, plan_id: int) -> Dict:
        """Delete a plan."""
        try:
            plan = await self.db.get(Plan, plan_id)
            if not plan:
                raise Exception("Plan not found")
            
            await self.db.delete(plan)
            await self.db.commit()
            
            return {"message": "Plan deleted successfully"}
            
        except Exception as e:
            raise Exception(f"Error deleting plan: {str(e)}")
    
    async def generate_plan(self, rule_ids: List[int], goals: Dict, preferred_routes: Optional[List[str]] = None) -> Dict:
        """Generate a new training plan using AI."""
        try:
            # Get all rules from the provided rule IDs
            rules = []
            for rule_id in rule_ids:
                rule = await self.db.get(Rule, rule_id)
                if not rule:
                    raise Exception(f"Rule with ID {rule_id} not found")
                rules.append(rule.rule_text)
            
            # Generate plan using AI service
            ai_service = AIService(self.db)
            generated_plan = await ai_service.generate_training_plan(
                rule_set=rules,
                goals=goals,
                preferred_routes=preferred_routes or []
            )
            
            # Create and store the plan
            plan_dict = await self.create_plan(generated_plan, version=1)
            
            return {
                "plan": plan_dict,
                "generation_metadata": {
                    "status": "success",
                    "rule_ids": rule_ids,
                    "goals": goals
                }
            }
            
        except Exception as e:
            raise Exception(f"Error generating plan: {str(e)}")
    
    async def get_plan_evolution_history(self, plan_id: int) -> List[Dict]:
        """Get full evolution history for a plan."""
        try:
            evolution_service = PlanEvolutionService(self.db)
            plans = await evolution_service.get_plan_evolution_history(plan_id)
            
            if not plans:
                raise Exception("Plan not found")
                
            return [
                {
                    "id": p.id,
                    "version": p.version,
                    "parent_plan_id": p.parent_plan_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "plan_data": p.jsonb_plan
                } for p in plans
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching plan evolution: {str(e)}")
    
    async def get_current_plan(self) -> Optional[Dict]:
        """Get the most recent active plan."""
        try:
            result = await self.db.execute(
                select(Plan).order_by(desc(Plan.created_at)).limit(1)
            )
            plan = result.scalar_one_or_none()
            
            if not plan:
                return None
                
            return {
                "id": plan.id,
                "version": plan.version,
                "parent_plan_id": plan.parent_plan_id,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "plan_data": plan.jsonb_plan
            }
            
        except Exception as e:
            raise Exception(f"Error fetching current plan: {str(e)}")