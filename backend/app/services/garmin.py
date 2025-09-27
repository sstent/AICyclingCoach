import os
from pathlib import Path
import garth
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
        logger.debug(f"GarminService initialized with username: {self.username is not None}, password: {self.password is not None}")
        self.client: Optional[garth.Client] = None
        self.session_dir = Path("data/sessions")

        # Ensure session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

    async def authenticate(self) -> bool:
        """Authenticate with Garmin Connect and persist session."""
        if not self.client:
            self.client = garth.Client()

        try:
            # Try to load existing session
            await asyncio.to_thread(self.client.load, self.session_dir)
            logger.info("Loaded existing Garmin session")
            return True
        except Exception as e:
            logger.warning(f"Failed to load existing Garmin session: {e}. Attempting fresh authentication.")
            # Fresh authentication required
            if not self.username or not self.password:
                logger.error("Garmin username or password not set in environment variables.")
                raise GarminAuthError("Garmin username or password not configured.")
            try:
                await asyncio.to_thread(self.client.login, self.username, self.password)
                await asyncio.to_thread(self.client.save, self.session_dir)
                logger.info("Successfully authenticated with Garmin Connect")
                return True
            except Exception as e:
                logger.error(f"Garmin authentication failed: {str(e)}")
                raise GarminAuthError(f"Authentication failed: {str(e)}")

    async def get_activities(self, limit: int = 10, start_date: datetime = None) -> List[Dict[str, Any]]:
        """Fetch recent activities from Garmin Connect."""
        if not self.client:
            await self.authenticate()

        if not start_date:
            start_date = datetime.now() - timedelta(days=7)

        try:
            activities = await asyncio.to_thread(self.client.get_activities, limit=limit, start=start_date)
            logger.info(f"Fetched {len(activities)} activities from Garmin")
            return activities
        except Exception as e:
            logger.error(f"Failed to fetch activities: {str(e)}")
            raise GarminAPIError(f"Failed to fetch activities: {str(e)}")

    async def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed activity data including metrics."""
        if not self.client:
            await self.authenticate()

        try:
            details = await asyncio.to_thread(self.client.get_activity, activity_id)
            logger.info(f"Fetched details for activity {activity_id}")
            return details
        except Exception as e:
            logger.error(f"Failed to fetch activity details for {activity_id}: {str(e)}")
            raise GarminAPIError(f"Failed to fetch activity details: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if we have a valid authenticated session."""
        return self.client is not None


class GarminAuthError(Exception):
    """Raised when Garmin authentication fails."""
    pass


class GarminAPIError(Exception):
    """Raised when Garmin API calls fail."""
    pass