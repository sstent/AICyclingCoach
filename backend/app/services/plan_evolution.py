from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.services.ai_service import AIService
from backend.app.models.analysis import Analysis
from backend.app.models.plan import Plan
import logging

logger = logging.getLogger(__name__)


class PlanEvolutionService:
    """Service for evolving training plans based on workout analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService(db)

    async def evolve_plan_from_analysis(
        self,
        analysis: Analysis,
        current_plan: Plan
    ) -> Plan:
        """Create a new plan version based on workout analysis."""
        if not analysis.approved:
            return None

        suggestions = analysis.suggestions
        if not suggestions:
            return None

        # Generate new plan incorporating suggestions
        evolution_context = {
            "current_plan": current_plan.jsonb_plan,
            "workout_analysis": analysis.jsonb_feedback,
            "suggestions": suggestions,
            "evolution_type": "workout_feedback"
        }

        new_plan_data = await self.ai_service.evolve_plan(evolution_context)

        # Create new plan version
        new_plan = Plan(
            jsonb_plan=new_plan_data,
            version=current_plan.version + 1,
            parent_plan_id=current_plan.id
        )

        self.db.add(new_plan)
        await self.db.commit()
        await self.db.refresh(new_plan)

        logger.info(f"Created new plan version {new_plan.version} from analysis {analysis.id}")
        return new_plan

    async def get_plan_evolution_history(self, plan_id: int) -> list[Plan]:
        """Get the evolution history for a plan."""
        result = await self.db.execute(
            select(Plan)
            .where(
                (Plan.id == plan_id) |
                (Plan.parent_plan_id == plan_id)
            )
            .order_by(Plan.version)
        )
        return result.scalars().all()

    async def get_current_active_plan(self) -> Plan:
        """Get the most recent active plan."""
        result = await self.db.execute(
            select(Plan)
            .order_by(Plan.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()