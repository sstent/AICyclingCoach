from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.services.garmin import GarminConnectService as GarminService, GarminAPIError, GarminAuthError
from backend.app.models.workout import Workout
from backend.app.models.garmin_sync_log import GarminSyncLog, GarminSyncStatus
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
        logger.info(f"Starting Garmin activity sync for the last {days_back} days.")
        sync_log = None  # Initialize sync_log
        try:
            # Create sync log entry
            sync_log = GarminSyncLog(status=GarminSyncStatus.IN_PROGRESS)
            self.db.add(sync_log)
            await self.db.commit()
            await self.db.refresh(sync_log)  # Refresh to get the generated ID

            logger.debug(f"Created new GarminSyncLog with ID: {sync_log.id}")

            # Calculate start date
            start_date = datetime.now() - timedelta(days=days_back)
            logger.debug(f"Fetching activities from Garmin starting from: {start_date}")

            # Fetch activities from Garmin
            activities = await self.garmin_service.get_activities(
                limit=50, start_date=start_date, end_date=datetime.now()
            )
            logger.debug(f"Found {len(activities)} activities from Garmin.")

            synced_count = 0
            for activity in activities:
                activity_id = str(activity['activityId'])
                logger.debug(f"Processing activity ID: {activity_id}")
                if await self.activity_exists(activity_id):
                    logger.debug(f"Activity {activity_id} already exists in DB, skipping.")
                    continue

                # Get full activity details with retry logic
                max_retries = 3
                details = None
                for attempt in range(max_retries):
                    try:
                        logger.debug(f"Attempt {attempt + 1} to fetch details for activity {activity_id}")
                        details = await self.garmin_service.get_activity_details(activity_id)
                        logger.debug(f"Successfully fetched details for activity {activity_id}.")
                        break
                    except (GarminAPIError, GarminAuthError) as e:
                        logger.warning(f"Failed to fetch details for {activity_id} (attempt {attempt + 1}/{max_retries}): {e}")
                        if attempt == max_retries - 1:
                            logger.error(f"Max retries reached for activity {activity_id}. Skipping details fetch.", exc_info=True)
                            raise
                        await asyncio.sleep(2 ** attempt)
                
                if details is None:
                    logger.warning(f"Skipping activity {activity_id} due to failure in fetching details.")
                    continue

                # Merge basic activity data with detailed metrics
                full_activity = {**activity, **details}
                logger.debug(f"Merged activity data for {activity_id}.")

                # Parse and create workout
                workout_data = await self.parse_activity_data(full_activity)
                workout = Workout(**workout_data)
                self.db.add(workout)
                synced_count += 1
                logger.debug(f"Added workout {workout.garmin_activity_id} to session.")

            # Update sync log
            sync_log.status = GarminSyncStatus.COMPLETED
            sync_log.activities_synced = synced_count
            sync_log.last_sync_time = datetime.now()

            await self.db.commit()
            logger.info(f"Successfully synced {synced_count} activities.")
            return synced_count

        except GarminAuthError as e:
            logger.error(f"Garmin authentication failed during sync: {e}", exc_info=True)
            if sync_log:
                sync_log.status = GarminSyncStatus.AUTH_FAILED
                sync_log.error_message = str(e)
                await self.db.commit()
            raise
        except GarminAPIError as e:
            logger.error(f"Garmin API error during sync: {e}", exc_info=True)
            if sync_log:
                sync_log.status = GarminSyncStatus.FAILED
                sync_log.error_message = str(e)
                await self.db.commit()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Garmin sync: {e}", exc_info=True)
            if sync_log:
                sync_log.status = GarminSyncStatus.FAILED
                sync_log.error_message = str(e)
                await self.db.commit()
            raise

    async def get_latest_sync_status(self):
        """Get the most recent sync log entry."""
        logger.debug("Fetching latest Garmin sync status.")
        result = await self.db.execute(
            select(GarminSyncLog)
            .order_by(desc(GarminSyncLog.created_at))
            .limit(1)
        )
        status = result.scalar_one_or_none()
        logger.debug(f"Latest sync status: {status.status if status else 'None'}")
        return status

    async def activity_exists(self, garmin_activity_id: str) -> bool:
        """Check if activity already exists in database."""
        logger.debug(f"Checking if activity {garmin_activity_id} exists in database.")
        result = await self.db.execute(
            select(Workout).where(Workout.garmin_activity_id == garmin_activity_id)
        )
        exists = result.scalar_one_or_none() is not None
        logger.debug(f"Activity {garmin_activity_id} exists: {exists}")
        return exists

    async def parse_activity_data(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Garmin activity data into workout model format."""
        logger.debug(f"Parsing activity data for Garmin activity ID: {activity.get('activityId')}")
        return {
            "garmin_activity_id": str(activity['activityId']),
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