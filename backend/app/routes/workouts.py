from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.workout import Workout
from app.models.analysis import Analysis
from app.models.garmin_sync_log import GarminSyncLog
from app.models.plan import Plan
from app.schemas.workout import Workout as WorkoutSchema, WorkoutSyncStatus, WorkoutMetric
from app.schemas.analysis import Analysis as AnalysisSchema
from app.schemas.plan import Plan as PlanSchema
from app.services.workout_sync import WorkoutSyncService
from app.services.ai_service import AIService
from app.services.plan_evolution import PlanEvolutionService

router = APIRouter()


@router.get("/", response_model=List[WorkoutSchema])
async def read_workouts(db: AsyncSession = Depends(get_db)):
    """Get all workouts."""
    result = await db.execute(select(Workout))
    return result.scalars().all()


@router.get("/{workout_id}", response_model=WorkoutSchema)
async def read_workout(workout_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific workout by ID."""
    workout = await db.get(Workout, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout

@router.get("/{workout_id}/metrics", response_model=list[WorkoutMetric])
async def get_workout_metrics(
    workout_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get time-series metrics for a workout"""
    workout = await db.get(Workout, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    if not workout.metrics:
        return []
        
    return workout.metrics


@router.post("/sync")
async def trigger_garmin_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger background sync of recent Garmin activities."""
    sync_service = WorkoutSyncService(db)
    background_tasks.add_task(sync_service.sync_recent_activities, days_back=14)
    return {"message": "Garmin sync started"}


@router.get("/sync-status", response_model=WorkoutSyncStatus)
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """Get the latest sync status."""
    result = await db.execute(
        select(GarminSyncLog).order_by(GarminSyncLog.created_at.desc()).limit(1)
    )
    sync_log = result.scalar_one_or_none()
    if not sync_log:
        return WorkoutSyncStatus(status="never_synced")
    return sync_log


@router.post("/{workout_id}/analyze")
async def analyze_workout(
    workout_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger AI analysis of a specific workout."""
    workout = await db.get(Workout, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    ai_service = AIService(db)
    background_tasks.add_task(
        analyze_and_store_workout,
        db, workout, ai_service
    )

    return {"message": "Analysis started", "workout_id": workout_id}


async def analyze_and_store_workout(db: AsyncSession, workout: Workout, ai_service: AIService):
    """Background task to analyze workout and store results."""
    try:
        # Get current plan if workout is associated with one
        plan = None
        if workout.plan_id:
            plan = await db.get(Plan, workout.plan_id)

        # Analyze workout
        analysis_result = await ai_service.analyze_workout(workout, plan.jsonb_plan if plan else None)

        # Store analysis
        analysis = Analysis(
            workout_id=workout.id,
            jsonb_feedback=analysis_result.get("feedback", {}),
            suggestions=analysis_result.get("suggestions", {})
        )
        db.add(analysis)
        await db.commit()

    except Exception as e:
        # Log error but don't crash the background task
        print(f"Error analyzing workout {workout.id}: {str(e)}")


@router.get("/{workout_id}/analyses", response_model=List[AnalysisSchema])
async def read_workout_analyses(workout_id: int, db: AsyncSession = Depends(get_db)):
    """Get all analyses for a specific workout."""
    workout = await db.get(Workout, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    return workout.analyses


@router.post("/analyses/{analysis_id}/approve")
async def approve_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Approve analysis suggestions and trigger plan evolution."""
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis.approved = True

    # Trigger plan evolution if suggestions exist and workout has a plan
    if analysis.suggestions and analysis.workout.plan_id:
        evolution_service = PlanEvolutionService(db)
        current_plan = await db.get(Plan, analysis.workout.plan_id)
        if current_plan:
            new_plan = await evolution_service.evolve_plan_from_analysis(
                analysis, current_plan
            )
            await db.commit()
            return {"message": "Analysis approved", "new_plan_id": new_plan.id if new_plan else None}

    await db.commit()
    return {"message": "Analysis approved"}


@router.get("/plans/{plan_id}/evolution", response_model=List["PlanSchema"])
async def get_plan_evolution(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get full evolution history for a plan."""
    evolution_service = PlanEvolutionService(db)
    plans = await evolution_service.get_plan_evolution_history(plan_id)
    if not plans:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plans