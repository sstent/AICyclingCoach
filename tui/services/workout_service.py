"""
Enhanced workout service with debugging for TUI application.
"""
from typing import Dict, List, Optional
from sqlalchemy import select, desc, text
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
        """Get all workouts with enhanced debugging."""
        try:
            print(f"WorkoutService.get_workouts: Starting query with limit={limit}")
            
            # First, let's check if the table exists and has data
            count_result = await self.db.execute(text("SELECT COUNT(*) FROM workouts"))
            total_count = count_result.scalar()
            print(f"WorkoutService.get_workouts: Total workouts in database: {total_count}")
            
            if total_count == 0:
                print("WorkoutService.get_workouts: No workouts found in database")
                return []
            
            # Build the query
            query = select(Workout).order_by(desc(Workout.start_time))
            if limit:
                query = query.limit(limit)
                
            print(f"WorkoutService.get_workouts: Executing query: {query}")
            
            # Execute the query
            result = await self.db.execute(query)
            print("WorkoutService.get_workouts: Query executed successfully")
            
            # Get all workouts
            workouts = result.scalars().all()
            print(f"WorkoutService.get_workouts: Retrieved {len(workouts)} workout objects")
            
            # Convert to dictionaries
            workout_dicts = []
            for i, w in enumerate(workouts):
                print(f"WorkoutService.get_workouts: Processing workout {i+1}: ID={w.id}, Type={w.activity_type}")
                workout_dict = {
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
                }
                workout_dicts.append(workout_dict)
            
            print(f"WorkoutService.get_workouts: Returning {len(workout_dicts)} workouts")
            return workout_dicts
            
        except Exception as e:
            # Enhanced error logging
            import traceback
            print(f"WorkoutService.get_workouts: ERROR: {str(e)}")
            print(f"WorkoutService.get_workouts: Traceback: {traceback.format_exc()}")
            
            # Log error properly
            import logging
            logging.error(f"Error fetching workouts: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    async def debug_database_connection(self) -> Dict:
        """Debug method to check database connection and table status."""
        debug_info = {}
        try:
            # Check database connection
            result = await self.db.execute(text("SELECT 1"))
            debug_info["connection"] = "OK"
            
            # Check if workouts table exists
            table_check = await self.db.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='workouts'")
            )
            table_exists = table_check.fetchone()
            debug_info["workouts_table_exists"] = bool(table_exists)
            
            if table_exists:
                # Get table schema
                schema_result = await self.db.execute(text("PRAGMA table_info(workouts)"))
                schema = schema_result.fetchall()
                debug_info["workouts_schema"] = [dict(row._mapping) for row in schema]
                
                # Get row count
                count_result = await self.db.execute(text("SELECT COUNT(*) FROM workouts"))
                debug_info["workouts_count"] = count_result.scalar()
                
                # Get sample data if any
                if debug_info["workouts_count"] > 0:
                    sample_result = await self.db.execute(text("SELECT * FROM workouts LIMIT 3"))
                    sample_data = sample_result.fetchall()
                    debug_info["sample_workouts"] = [dict(row._mapping) for row in sample_data]
            
            return debug_info
            
        except Exception as e:
            import traceback
            debug_info["error"] = str(e)
            debug_info["traceback"] = traceback.format_exc()
            return debug_info
    
    # ... rest of the methods remain the same ...
    
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