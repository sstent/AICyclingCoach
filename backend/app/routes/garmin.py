from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.dependencies import verify_api_key
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.database import get_db

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/sync")
async def trigger_garmin_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger background sync of Garmin activities"""
    sync_service = WorkoutSyncService(db)
    background_tasks.add_task(sync_service.sync_recent_activities, days_back=14)
    return {"message": "Garmin sync started"}

@router.get("/sync-status")
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """Get latest sync status"""
    sync_service = WorkoutSyncService(db)
    return await sync_service.get_latest_sync_status()