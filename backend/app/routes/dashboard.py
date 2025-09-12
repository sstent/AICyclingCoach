from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.models.workout import Workout
from backend.app.models.plan import Plan
from backend.app.models.garmin_sync_log import GarminSyncLog
from sqlalchemy import select, desc
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """Get consolidated dashboard data"""
    try:
        # Recent workouts (last 7 days)
        workout_result = await db.execute(
            select(Workout)
            .where(Workout.start_time >= datetime.now() - timedelta(days=7))
            .order_by(desc(Workout.start_time))
            .limit(5)
        )
        recent_workouts = [w.to_dict() for w in workout_result.scalars().all()]

        # Current active plan
        plan_result = await db.execute(
            select(Plan)
            .where(Plan.active == True)
            .order_by(desc(Plan.created_at))
        )
        current_plan = plan_result.scalar_one_or_none()

        # Sync status
        sync_result = await db.execute(
            select(GarminSyncLog)
            .order_by(desc(GarminSyncLog.created_at))
            .limit(1)
        )
        last_sync = sync_result.scalar_one_or_none()

        return {
            "recent_workouts": recent_workouts,
            "current_plan": current_plan.to_dict() if current_plan else None,
            "last_sync": last_sync.to_dict() if last_sync else None,
            "metrics": {
                "weekly_volume": sum(w.duration_seconds for w in recent_workouts) / 3600,
                "plan_progress": current_plan.progress if current_plan else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data error: {str(e)}")