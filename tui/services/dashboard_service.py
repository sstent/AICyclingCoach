
"""
Dashboard service for TUI application.
Provides dashboard data without HTTP dependencies.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workout import Workout
from backend.app.models.plan import Plan
from backend.app.models.garmin_sync_log import GarminSyncLog


class DashboardService:
    """Service for dashboard data operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def test_connection(self) -> None:
        """Test database connection by running a simple query."""
        try:
            result = await self.db.execute("SELECT 1")
            return result.scalar() == 1
        except Exception as e:
            raise Exception(f"Database connection test failed: {str(e)}")
    
    async def get_dashboard_data(self) -> Dict:
        """Get consolidated dashboard data."""
        try:
            # Test database connection first
            if not await self.test_connection():
                raise Exception("Database connection test failed")
            
            # Recent workouts (last 7 days)
            workout_result = await self.db.execute(
                select(Workout)
                .where(Workout.start_time >= datetime.now() - timedelta(days=7))
                .order_by(desc(Workout.start_time))
                .limit(5)
            )
            recent_workouts = workout_result.scalars().all()

            # Current active plan - Modified since Plan model doesn't have 'active' field
            plan_result = await self.db.execute(
                select(Plan)
                .order_by(desc(Plan.created_at))
                .limit(1)
            )
            current_plan = plan_result.scalar_one_or_none()

            # Sync status
            sync_result = await self.db.execute(
                select(GarminSyncLog)
                .order_by(desc(GarminSyncLog.created_at))
                .limit(1)
            )
            last_sync = sync_result.scalar_one_or_none()

            # Calculate metrics
            total_duration = sum(w.duration_seconds or 0 for w in recent_workouts)
            weekly_volume = total_duration / 3600 if total_duration else 0

            return {
                "recent_workouts": [
                    {
                        "id": w.id,
                        "activity_type": w.activity_type,
                        "start_time": w.start_time.isoformat() if w.start_time else None,
                        "duration_seconds": w.duration_seconds,
                        "distance_m": w.distance_m,
                        "avg_hr": w.avg_hr,
                        "avg_power": w.avg_power
                    } for w in recent_workouts
                ],
                "current_plan": {
                    "id": current_plan.id,
                    "version": current_plan.version,
                    "created_at": current_plan.created_at.isoformat() if current_plan.created_at else None
                } if current_plan else None,
                "last_sync": {
                    "last_sync_time": last_sync.last_sync_time.isoformat() if last_sync and last_sync.last_sync_time else None,
                    "activities_synced": last_sync.activities_synced if last_sync else 0,
                    "status": last_sync.status if last_sync else "never_synced",
                    "error_message": last_sync.error_message if last_sync else None
                } if last_sync else None,
                "metrics": {
                    "weekly_volume": weekly_volume,
                    "workout_count": len(recent_workouts),
                    "plan_progress": 0  # TODO: Calculate actual progress
                }
            }
            
        except Exception as e:
            raise Exception(f"Dashboard data error: {str(e)}")

    async def get_weekly_stats(self) -> Dict:
        """Get weekly workout statistics."""
        try:
            # Test database connection first
            if not await self.test_connection():
                raise Exception("Database connection test failed")
            
            week_start = datetime.now() - timedelta(days=7)
            
            workout_result = await self.db.execute(
                select(Workout)
                .where(Workout.start_time >= week_start)
            )
            workouts = workout_result.scalars().all()
            
            total_distance = sum(w.distance_m or 0 for w in workouts) / 1000  # Convert to km
            total_time = sum(w.duration_seconds or 0 for w in workouts) / 3600  # Convert to hours
            
            return {
                "workout_count": len(workouts),
                "total_distance_km": round(total_distance, 1),
                "total_time_hours": round(total_time, 1),
                "avg_distance_km": round(total_distance / len(workouts), 1) if workouts else 0,
                "avg_duration_hours": round(total_time / len(workouts), 1) if workouts else 0
            }
            
        except Exception as e:
            raise Exception(f"Weekly stats error: {str(e)}")