from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.services.garmin import GarminService, GarminAPIError, GarminAuthError
from app.models.workout import Workout
from app.models.garmin_sync_log import GarminSyncLog
from app.models.garmin_sync_log import GarminSyncLog
from datetime import datetime, timedelta
import logging
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class WorkoutSyncService:
    """Service for syncing Garmin activities to database."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.garmin_service = GarminService()

    async def sync_recent_activities(self, days_back: int = 7) -> int:
        """Sync recent Garmin activities to database."""
        try:
            # Create sync log entry
            sync_log = GarminSyncLog(status="in_progress")
            self.db.add(sync_log)
            await self.db.commit()

            # Calculate start date
            start_date = datetime.now() - timedelta(days=days_back)

            # Fetch activities from Garmin
            activities = await self.garmin_service.get_activities(
                limit=50, start_date=start_date
            )

            synced_count = 0
            for activity in activities:
                activity_id = activity['activityId']
                if await self.activity_exists(activity_id):
                    continue

                # Get full activity details with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        details = await self.garmin_service.get_activity_details(activity_id)
                        break
                    except (GarminAPIError, GarminAuthError) as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(2 ** attempt)
                        logger.warning(f"Retrying activity details fetch for {activity_id}, attempt {attempt + 1}")

                # Merge basic activity data with detailed metrics
                full_activity = {**activity, **details}

                # Parse and create workout
                workout_data = await self.parse_activity_data(full_activity)
                workout = Workout(**workout_data)
                self.db.add(workout)
                synced_count += 1

            # Update sync log
            sync_log.status = "success"
            sync_log.activities_synced = synced_count
            sync_log.last_sync_time = datetime.now()

            await self.db.commit()
            logger.info(f"Successfully synced {synced_count} activities")
            return synced_count

        except GarminAuthError as e:
            sync_log.status = "auth_error"
            sync_log.error_message = str(e)
            await self.db.commit()
            logger.error(f"Garmin authentication failed: {str(e)}")
            raise
        except GarminAPIError as e:
            sync_log.status = "api_error"
            sync_log.error_message = str(e)
            await self.db.commit()
            logger.error(f"Garmin API error during sync: {str(e)}")
            raise
        except Exception as e:
            sync_log.status = "error"
            sync_log.error_message = str(e)
            await self.db.commit()
            logger.error(f"Unexpected error during sync: {str(e)}")
            raise

    async def get_latest_sync_status(self):
        """Get the most recent sync log entry"""
        result = await self.db.execute(
            select(GarminSyncLog)
            .order_by(desc(GarminSyncLog.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def activity_exists(self, garmin_activity_id: str) -> bool:
        """Check if activity already exists in database."""
        result = await self.db.execute(
            select(Workout).where(Workout.garmin_activity_id == garmin_activity_id)
        )
        return result.scalar_one_or_none() is not None

    async def parse_activity_data(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Garmin activity data into workout model format."""
        return {
            "garmin_activity_id": activity['activityId'],
            "activity_type": activity.get('activityType', {}).get('typeKey'),
            "start_time": datetime.fromisoformat(activity['startTimeLocal'].replace('Z', '+00:00')),
            "duration_seconds": activity.get('duration'),
            "distance_m": activity.get('distance'),
            "avg_hr": activity.get('averageHR'),
            "max_hr": activity.get('maxHR'),
            "avg_power": activity.get('avgPower'),
            "max_power": activity.get('maxPower'),
            "avg_cadence": activity.get('averageBikingCadenceInRevPerMinute'),
            "elevation_gain_m": activity.get('elevationGain'),
            "metrics": activity  # Store full Garmin data as JSONB
        }