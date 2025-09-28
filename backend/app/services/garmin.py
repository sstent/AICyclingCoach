import os
from pathlib import Path
import garth
from garth.exc import GarthException
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class GarminService:
    """Service for interacting with Garmin Connect API."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.username = os.getenv("GARMIN_USERNAME")
        self.password = os.getenv("GARMIN_PASSWORD")
        self.session_dir = Path("data/sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)

    async def authenticate(self) -> bool:
        """Authenticate with Garmin Connect and persist session."""
        try:
            await asyncio.to_thread(garth.resume, self.session_dir)
            logger.info("Loaded existing Garmin session")
        except (FileNotFoundError, GarthException):
            logger.warning("No existing session found. Attempting fresh authentication.")
            if not self.username or not self.password:
                logger.error("Garmin username or password not set in environment variables.")
                raise GarminAuthError("Garmin username or password not configured.")
            try:
                await asyncio.to_thread(garth.login, self.username, self.password)
                await asyncio.to_thread(garth.save, self.session_dir)
                logger.info("Successfully authenticated with Garmin Connect")
            except Exception as e:
                logger.error(f"Garmin authentication failed: {str(e)}")
                raise GarminAuthError(f"Authentication failed: {str(e)}")
        return True

    async def get_activities(self, limit: int = 10, start_date: datetime = None) -> List[Dict[str, Any]]:
        """Fetch recent activities from Garmin Connect."""
        await self.authenticate()

        if not start_date:
            start_date = datetime.now() - timedelta(days=7)

        try:
            activities = await asyncio.to_thread(
                garth.connectapi,
                "/activity-service/activity/activities",
                params={"limit": limit, "start": start_date.strftime("%Y-%m-%d")},
            )
            logger.info(f"Fetched {len(activities)} activities from Garmin")
            return activities or []
        except Exception as e:
            logger.error(f"Failed to fetch activities: {str(e)}")
            raise GarminAPIError(f"Failed to fetch activities: {str(e)}")

    async def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed activity data including metrics."""
        await self.authenticate()

        try:
            details = await asyncio.to_thread(
                garth.connectapi, f"/activity-service/activity/{activity_id}"
            )
            logger.info(f"Fetched details for activity {activity_id}")
            return details
        except Exception as e:
            logger.error(f"Failed to fetch activity details for {activity_id}: {str(e)}")
            raise GarminAPIError(f"Failed to fetch activity details: {str(e)}")


class GarminAuthError(Exception):
    """Raised when Garmin authentication fails."""
    pass


class GarminAPIError(Exception):
    """Raised when Garmin API calls fail."""
    pass