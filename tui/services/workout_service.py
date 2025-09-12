"""
Workout service for TUI application.
Manages workout data, analysis, and Garmin sync without HTTP dependencies.
"""
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workout import Workout
from backend.app.models.analysis import Analysis
from backend.app.models.garmin_sync_log import GarminSyncLog
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.services.ai_service import AIService


class WorkoutService:
    """Service for workout operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_workouts(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all workouts."""
        try:
            query = select(Workout).order_by(desc(Workout.start_time))
            if limit:
                query = query.limit(limit)
                
            result = await self.db.execute(query)
            workouts = result.scalars().all()
            
            return [
                {
                    "id": w.id,
                    "garmin_activity_id": w.garmin_activity_id,
                    "activity_type": w.activity_type,
                    "start_time": w.start_time.isoformat() if w.start_time else None,
                    "duration_seconds": w.duration_seconds,
                    "distance_m": w.distance_m,
                    "avg_hr": w.avg_hr,
                    "max_hr": w.max_hr,
                    "avg_power": w.avg_power,
                    "max_power": w.max_power,
                    "avg_cadence": w.avg_cadence,
                    "elevation_gain_m": w.elevation_gain_m
                } for w in workouts
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching workouts: {str(e)}")
    
    async def get_workout(self, workout_id: int) -> Optional[Dict]:
        """Get a specific workout by ID."""
        try:
            workout = await self.db.get(Workout, workout_id)
            if not workout:
                return None
                
            return {
                "id": workout.id,
                "garmin_activity_id": workout.garmin_activity_id,
                "activity_type": workout.activity_type,
                "start_time": workout.start_time.isoformat() if workout.start_time else None,
                "duration_seconds": workout.duration_seconds,
                "distance_m": workout.distance_m,
                "avg_hr": workout.avg_hr,
                "max_hr": workout.max_hr,
                "avg_power": workout.avg_power,
                "max_power": workout.max_power,
                "avg_cadence": workout.avg_cadence,
                "elevation_gain_m": workout.elevation_gain_m,
                "metrics": workout.metrics
            }
            
        except Exception as e:
            raise Exception(f"Error fetching workout {workout_id}: {str(e)}")
    
    async def get_workout_metrics(self, workout_id: int) -> List[Dict]:
        """Get time-series metrics for a workout."""
        try:
            workout = await self.db.get(Workout, workout_id)
            if not workout or not workout.metrics:
                return []
                
            return workout.metrics
            
        except Exception as e:
            raise Exception(f"Error fetching workout metrics: {str(e)}")
    
    async def sync_garmin_activities(self, days_back: int = 14) -> Dict:
        """Trigger Garmin sync in background."""
        try:
            sync_service = WorkoutSyncService(self.db)
            result = await sync_service.sync_recent_activities(days_back=days_back)
            
            return {
                "message": "Garmin sync completed",
                "activities_synced": result.get("activities_synced", 0),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "message": f"Garmin sync failed: {str(e)}",
                "activities_synced": 0,
                "status": "error"
            }
    
    async def get_sync_status(self) -> Dict:
        """Get the latest sync status."""
        try:
            result = await self.db.execute(
                select(GarminSyncLog).order_by(desc(GarminSyncLog.created_at)).limit(1)
            )
            sync_log = result.scalar_one_or_none()
            
            if not sync_log:
                return {"status": "never_synced"}
                
            return {
                "status": sync_log.status,
                "last_sync_time": sync_log.last_sync_time.isoformat() if sync_log.last_sync_time else None,
                "activities_synced": sync_log.activities_synced,
                "error_message": sync_log.error_message
            }
            
        except Exception as e:
            raise Exception(f"Error fetching sync status: {str(e)}")
    
    async def analyze_workout(self, workout_id: int) -> Dict:
        """Trigger AI analysis of a specific workout."""
        try:
            workout = await self.db.get(Workout, workout_id)
            if not workout:
                raise Exception("Workout not found")

            ai_service = AIService(self.db)
            analysis_result = await ai_service.analyze_workout(workout, None)
            
            # Store analysis
            analysis = Analysis(
                workout_id=workout.id,
                jsonb_feedback=analysis_result.get("feedback", {}),
                suggestions=analysis_result.get("suggestions", {})
            )
            self.db.add(analysis)
            await self.db.commit()

            return {
                "message": "Analysis completed",
                "workout_id": workout_id,
                "analysis_id": analysis.id,
                "feedback": analysis_result.get("feedback", {}),
                "suggestions": analysis_result.get("suggestions", {})
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing workout: {str(e)}")
    
    async def get_workout_analyses(self, workout_id: int) -> List[Dict]:
        """Get all analyses for a specific workout."""
        try:
            workout = await self.db.get(Workout, workout_id)
            if not workout:
                raise Exception("Workout not found")

            result = await self.db.execute(
                select(Analysis).where(Analysis.workout_id == workout_id)
            )
            analyses = result.scalars().all()
            
            return [
                {
                    "id": a.id,
                    "analysis_type": a.analysis_type,
                    "feedback": a.jsonb_feedback,
                    "suggestions": a.suggestions,
                    "approved": a.approved,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                } for a in analyses
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching workout analyses: {str(e)}")
    
    async def approve_analysis(self, analysis_id: int) -> Dict:
        """Approve analysis suggestions."""
        try:
            analysis = await self.db.get(Analysis, analysis_id)
            if not analysis:
                raise Exception("Analysis not found")

            analysis.approved = True
            await self.db.commit()
            
            return {
                "message": "Analysis approved",
                "analysis_id": analysis_id
            }
            
        except Exception as e:
            raise Exception(f"Error approving analysis: {str(e)}")