"""
Functional tests for Garmin authentication and workout syncing.
These tests verify the end-to-end functionality of Garmin integration.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.garmin import GarminConnectService as GarminService, GarminAuthError, GarminAPIError
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.models.workout import Workout
from backend.app.models.garmin_sync_log import GarminSyncLog


@pytest.fixture
async def garmin_service():
    """Create GarminService instance for testing."""
    service = GarminService()
    yield service


@pytest.fixture
async def workout_sync_service(db_session: AsyncSession):
    """Create WorkoutSyncService instance for testing."""
    service = WorkoutSyncService(db_session)
    yield service


class TestGarminAuthentication:
    """Test Garmin Connect authentication functionality."""

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'test@example.com',
        'GARMIN_PASSWORD': 'testpass123'
    })
    @patch('garminconnect.Garmin')
    async def test_successful_authentication(self, mock_client_class, garmin_service):
        """Test successful authentication with valid credentials."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=(None, None))
        mock_client.save = MagicMock()
        mock_client_class.return_value = mock_client

        # Test authentication
        result = await garmin_service.authenticate()

        assert result is True
        mock_client.login.assert_awaited_once_with('test@example.com', 'testpass123')
        mock_client.save.assert_called_once()

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'invalid@example.com',
        'GARMIN_PASSWORD': 'wrongpass'
    })
    @patch('garminconnect.Garmin')
    async def test_failed_authentication(self, mock_client_class, garmin_service):
        """Test authentication failure with invalid credentials."""
        # Setup mock client to raise exception
        mock_client = MagicMock()
        mock_client.login = AsyncMock(side_effect=Exception("Invalid credentials"))
        mock_client_class.return_value = mock_client

        # Test authentication
        with pytest.raises(GarminAuthError, match="Authentication failed"):
            await garmin_service.authenticate()

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'test@example.com',
        'GARMIN_PASSWORD': 'testpass123'
    })
    @patch('garminconnect.Garmin')
    async def test_session_reuse(self, mock_client_class, garmin_service):
        """Test that existing sessions are reused."""
        # Setup mock client with load method
        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=(None, None)) # Login handles loading from tokenstore
        mock_client_class.return_value = mock_client

        # Test authentication
        result = await garmin_service.authenticate()

        assert result is True
        mock_client.login.assert_awaited_once_with(tokenstore=garmin_service.session_dir)
        mock_client.save.assert_not_called()


class TestWorkoutSyncing:
    """Test workout synchronization functionality."""

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'test@example.com',
        'GARMIN_PASSWORD': 'testpass123'
    })
    @patch('garminconnect.Garmin')
    async def test_successful_sync_recent_activities(self, mock_client_class, workout_sync_service, db_session):
        """Test successful synchronization of recent activities."""
        # Setup mock Garmin client
        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=True)
        mock_client.save = MagicMock()

        # Mock activity data
        mock_activities = [
            {
                'activityId': '12345',
                'startTimeLocal': '2024-01-15T08:00:00.000Z',
                'activityType': {'typeKey': 'cycling'},
                'duration': 3600.0,
                'distance': 25000.0,
                'averageHR': 140.0,
                'maxHR': 170.0,
                'avgPower': 200.0,
                'maxPower': 350.0,
                'averageBikingCadenceInRevPerMinute': 85.0,
                'elevationGain': 500.0
            }
        ]

        # Mock detailed activity data
        mock_details = {
            'activityId': '12345',
            'startTimeLocal': '2024-01-15T08:00:00.000Z',
            'activityType': {'typeKey': 'cycling'},
            'duration': 3600.0,
            'distance': 25000.0,
            'averageHR': 140.0,
            'maxHR': 170.0,
            'avgPower': 200.0,
            'maxPower': 350.0,
            'averageBikingCadenceInRevPerMinute': 85.0,
            'elevationGain': 500.0
        }

        mock_client.get_activities_by_date = MagicMock(return_value=mock_activities)
        mock_client.get_activity_details = MagicMock(return_value=mock_details)
        mock_client_class.return_value = mock_client

        # Test sync
        synced_count = await workout_sync_service.sync_recent_activities(days_back=7)

        assert synced_count == 1

        # Verify workout was created
        workout_result = await db_session.execute(
            select(Workout).where(Workout.garmin_activity_id == '12345')
        )
        workout = workout_result.scalar_one_or_none()
        assert workout is not None
        assert workout.activity_type == 'cycling'
        assert workout.duration_seconds == 3600.0
        assert workout.distance_m == 25000.0

        # Verify sync log was created
        sync_log_result = await db_session.execute(
            select(GarminSyncLog).order_by(GarminSyncLog.created_at.desc())
        )
        sync_log = sync_log_result.scalar_one_or_none()
        assert sync_log is not None
        assert sync_log.status == 'success'
        assert sync_log.activities_synced == 1

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'test@example.com',
        'GARMIN_PASSWORD': 'testpass123'
    })
    @patch('garth.Client')
    async def test_sync_with_duplicate_activities(self, mock_client_class, workout_sync_service, db_session):
        """Test that duplicate activities are not synced again."""
        # First, create an existing workout
        existing_workout = Workout(
            garmin_activity_id='12345',
            activity_type='cycling',
            start_time=datetime.now(),
            duration_seconds=3600.0,
            distance_m=25000.0
        )
        db_session.add(existing_workout)
        await db_session.commit()

        # Setup mock Garmin client
        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=True)
        mock_client.save = MagicMock()

        # Mock activity data (same as existing)
        mock_activities = [
            {
                'activityId': '12345',
                'startTimeLocal': '2024-01-15T08:00:00.000Z',
                'activityType': {'typeKey': 'cycling'},
                'duration': 3600.0,
                'distance': 25000.0
            }
        ]

        mock_client.get_activities_by_date = MagicMock(return_value=mock_activities)
        mock_client_class.return_value = mock_client

        # Test sync
        synced_count = await workout_sync_service.sync_recent_activities(days_back=7)

        assert synced_count == 0  # No new activities synced

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'invalid@example.com',
        'GARMIN_PASSWORD': 'wrongpass'
    })
    @patch('garminconnect.Garmin')
    async def test_sync_with_auth_failure(self, mock_client_class, workout_sync_service, db_session):
        """Test sync failure due to authentication error."""
        # Setup mock client to fail authentication
        mock_client = MagicMock()
        mock_client.login = AsyncMock(side_effect=Exception("Invalid credentials"))
        mock_client_class.return_value = mock_client

        # Test sync
        with pytest.raises(GarminAuthError):
            await workout_sync_service.sync_recent_activities(days_back=7)

        # Verify sync log shows failure
        sync_log_result = await db_session.execute(
            select(GarminSyncLog).order_by(GarminSyncLog.created_at.desc())
        )
        sync_log = sync_log_result.scalar_one_or_none()
        assert sync_log is not None
        assert sync_log.status == 'auth_error'

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'test@example.com',
        'GARMIN_PASSWORD': 'testpass123'
    })
    @patch('garminconnect.Garmin')
    async def test_sync_with_api_error(self, mock_client_class, workout_sync_service, db_session):
        """Test sync failure due to API error."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=True)
        mock_client.save = MagicMock()
        mock_client.get_activities_by_date = MagicMock(side_effect=Exception("API rate limit exceeded"))
        mock_client_class.return_value = mock_client

        # Test sync
        with pytest.raises(GarminAPIError):
            await workout_sync_service.sync_recent_activities(days_back=7)

        # Verify sync log shows API error
        sync_log_result = await db_session.execute(
            select(GarminSyncLog).order_by(GarminSyncLog.created_at.desc())
        )
        sync_log = sync_log_result.scalar_one_or_none()
        assert sync_log is not None
        assert sync_log.status == 'api_error'
        assert 'API rate limit' in sync_log.error_message


class TestErrorHandling:
    """Test error handling in Garmin integration."""

    @patch.dict(os.environ, {
        'GARMIN_USERNAME': 'test@example.com',
        'GARMIN_PASSWORD': 'testpass123'
    })
    @patch('garminconnect.Garmin')
    async def test_activity_detail_fetch_retry(self, mock_client_class, workout_sync_service, db_session):
        """Test retry logic when fetching activity details fails."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=True)
        mock_client.save = MagicMock()

        mock_activities = [
            {
                'activityId': '12345',
                'startTimeLocal': '2024-01-15T08:00:00.000Z',
                'activityType': {'typeKey': 'cycling'},
                'duration': 3600.0,
                'distance': 25000.0
            }
        ]

        mock_client.get_activities_by_date = MagicMock(return_value=mock_activities)
        # First two calls fail, third succeeds
        mock_client.get_activity_details = MagicMock(side_effect=[
            Exception("Temporary error"),
            Exception("Temporary error"),
            {
                'activityId': '12345',
                'startTimeLocal': '2024-01-15T08:00:00.000Z',
                'activityType': {'typeKey': 'cycling'},
                'duration': 3600.0,
                'distance': 25000.0,
                'averageHR': 140.0,
                'maxHR': 170.0
            }
        ])
        mock_client_class.return_value = mock_client

        # Test sync
        synced_count = await workout_sync_service.sync_recent_activities(days_back=7)

        assert synced_count == 1
        # Verify get_activity was called 3 times (initial + 2 retries)
        assert mock_client.get_activity_details.call_count == 3