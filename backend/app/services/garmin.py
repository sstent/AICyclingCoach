import os
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GarminConnectService:
    """Service for interacting with Garmin Connect API."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.username = os.getenv("GARMIN_USERNAME")
        self.password = os.getenv("GARMIN_PASSWORD")
        self.session_dir = Path("data/sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.client: Optional[Garmin] = None

    async def _get_garmin_client(self) -> Garmin:
        """Get or create a Garmin client instance."""
        if self.client:
            return self.client

        self.client = Garmin()
        return self.client

    async def authenticate(self) -> bool:
        """Authenticate with Garmin Connect and persist session."""
        client = await self._get_garmin_client()
        try:
            logger.debug("Attempting to resume existing Garmin session.")
            await asyncio.to_thread(client.login, str(self.session_dir))
            logger.info("Successfully loaded existing Garmin session.")
        except (FileNotFoundError, GarminConnectAuthenticationError, GarminConnectConnectionError):
            logger.debug("No existing Garmin session found or session invalid.")
            logger.info("Attempting fresh authentication with Garmin Connect.")
            if not self.username or not self.password:
                logger.error("Garmin username or password not set in environment variables.")
                raise GarminAuthError("Garmin username or password not configured.")
            try:
                logger.debug(f"Attempting to log in with username: {self.username}")
                # The login method of python-garminconnect returns (token1, token2) on successful login
                # and handles MFA internally if prompt_mfa is provided.
                await asyncio.to_thread(client.login, self.username, self.password)
                await asyncio.to_thread(client.garth.dump, str(self.session_dir)) # Save tokens using garth.dump
                logger.info("Successfully authenticated and saved new Garmin session.")
            except Exception as e:
                logger.error(f"Garmin fresh authentication failed: {e}", exc_info=True)
                raise GarminAuthError(f"Authentication failed: {e}")
        return True

    async def get_activities(self, limit: int = 10, start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch recent activities from Garmin Connect."""
        await self.authenticate()
        client = await self._get_garmin_client()

        # Convert start_date to YYYY-MM-DD string as required by garminconnect.get_activities_by_date
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date_str = datetime.now().strftime("%Y-%m-%d")

        try:
            logger.debug(f"Fetching Garmin activities with limit={limit}, start_date={start_date_str}.")
            activities = await asyncio.to_thread(
                client.get_activities_by_date,
                start_date_str,
                end_date_str,
                limit=limit
            )
            logger.info(f"Successfully fetched {len(activities)} activities from Garmin.")
            logger.debug(f"Garmin activities data: {activities}")
            return activities or []
        except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
            logger.error(f"Failed to fetch activities from Garmin: {e}", exc_info=True)
            raise GarminAPIError(f"Failed to fetch activities: {e}")
        except GarminConnectAuthenticationError as e:
            logger.error(f"Garmin authentication failed while fetching activities: {e}", exc_info=True)
            raise GarminAuthError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching activities from Garmin: {e}", exc_info=True)
            raise GarminAPIError(f"Unexpected error: {e}")

    async def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed activity data including metrics."""
        await self.authenticate()
        client = await self._get_garmin_client()

        try:
            logger.debug(f"Fetching detailed data for activity ID: {activity_id}.")
            details = await asyncio.to_thread(
                client.get_activity_details, activity_id
            )
            logger.info(f"Successfully fetched details for activity ID: {activity_id}.")
            logger.debug(f"Garmin activity {activity_id} details: {details}")
            return details
        except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
            logger.error(f"Failed to fetch activity details for {activity_id}: {e}", exc_info=True)
            raise GarminAPIError(f"Failed to fetch activity details: {e}")
        except GarminConnectAuthenticationError as e:
            logger.error(f"Garmin authentication failed while fetching activity details: {e}", exc_info=True)
            raise GarminAuthError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching activity details for {activity_id}: {e}", exc_info=True)
            raise GarminAPIError(f"Unexpected error: {e}")


class GarminAuthError(Exception):
    """Raised when Garmin authentication fails."""
    pass


class GarminAPIError(Exception):
    """Raised when Garmin API calls fail."""
    pass