import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from backend.app.services.garmin import GarminConnectService as GarminService, GarminAuthError, GarminAPIError
from backend.app.models.garmin_sync_log import GarminSyncStatus
from datetime import datetime, timedelta
import garth # Import garth for type hinting

@pytest.fixture
def mock_env_vars():
    with patch.dict(os.environ, {"GARMIN_USERNAME": "test_user", "GARMIN_PASSWORD": "test_password"}):
        yield

def create_garmin_client_mock():
    mock_client_instance = MagicMock(spec=GarminService) # Use GarminService (which is GarminConnectService)
    mock_client_instance.authenticate = AsyncMock(return_value=True)
    mock_client_instance.get_activities = AsyncMock(return_value=[])
    mock_client_instance.get_activity_details = AsyncMock(return_value={})
    mock_client_instance.is_authenticated = MagicMock(return_value=True)
    return mock_client_instance

@pytest.mark.asyncio
async def test_garmin_authentication_success(db_session, mock_env_vars):
    """Test successful Garmin Connect authentication"""
    with patch('backend.app.services.garmin.garth.Client') as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.load.side_effect = FileNotFoundError
        service = GarminService(db_session)
        result = await service.authenticate()
        assert result is True
        mock_instance.login.assert_called_once_with(os.getenv("GARMIN_USERNAME"), os.getenv("GARMIN_PASSWORD"))
        mock_instance.save.assert_called_once_with(service.session_dir)

@pytest.mark.asyncio
async def test_garmin_authentication_failure(db_session, mock_env_vars):
    """Test authentication failure handling"""
    with patch('backend.app.services.garmin.garth.Client') as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.load.side_effect = FileNotFoundError
        mock_instance.login.side_effect = Exception("Invalid credentials")
        service = GarminService(db_session)
        with pytest.raises(GarminAuthError):
            await service.authenticate()
        mock_instance.login.assert_called_once_with(os.getenv("GARMIN_USERNAME"), os.getenv("GARMIN_PASSWORD"))
        mock_instance.save.assert_not_called()

@pytest.mark.asyncio
async def test_garmin_authentication_load_session_success(db_session, mock_env_vars):
    """Test successful loading of existing Garmin session"""
    with patch('backend.app.services.garmin.garth.Client') as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.load.side_effect = None
        service = GarminService(db_session)
        result = await service.authenticate()
        assert result is True
        mock_instance.load.assert_called_once_with(service.session_dir)
        mock_instance.login.assert_not_called()
        mock_instance.save.assert_not_called()

@pytest.mark.asyncio
async def test_garmin_authentication_missing_credentials(db_session):
    """Test authentication failure when credentials are missing"""
    with patch.dict(os.environ, {"GARMIN_USERNAME": "", "GARMIN_PASSWORD": ""}):
        with patch('backend.app.services.garmin.garth.Client') as mock_client_class:
            mock_instance = mock_client_class.return_value
            mock_instance.load.side_effect = FileNotFoundError
            service = GarminService(db_session)
            with pytest.raises(GarminAuthError, match="Garmin username or password not configured."):
                await service.authenticate()
            mock_instance.login.assert_not_called()
            mock_instance.save.assert_not_called()

@pytest.mark.asyncio
async def test_activity_sync(db_session, mock_env_vars):
    """Test successful activity synchronization"""
    with patch('backend.app.services.garmin.garth.Client', new_callable=create_garth_client_mock) as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.get_activities.return_value = [
            {"activityId": 123, "startTime": "2024-01-01T08:00:00"}
        ]
        service = GarminService(db_session)
        service.client = mock_instance
        activities = await service.get_activities()
        assert len(activities) == 1
        assert activities[0]["activityId"] == 123
        mock_instance.get_activities.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limiting_handling(db_session, mock_env_vars):
    """Test API rate limit error handling"""
    with patch('backend.app.services.garmin.garth.Client', new_callable=create_garth_client_mock) as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.get_activities.side_effect = Exception("Rate limit exceeded")
        service = GarminService(db_session)
        service.client = mock_instance
        with pytest.raises(GarminAPIError):
            await service.get_activities()
        mock_instance.get_activities.assert_called_once()

@pytest.mark.asyncio
async def test_get_activity_details_success(db_session, mock_env_vars):
    """Test successful retrieval of activity details."""
    with patch('backend.app.services.garmin.garth.Client', new_callable=create_garth_client_mock) as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.get_activity.return_value = {"activityId": 123, "details": "data"}
        service = GarminService(db_session)
        service.client = mock_instance
        details = await service.get_activity_details("123")
        assert details["activityId"] == 123
        mock_instance.get_activity.assert_called_once_with("123")

@pytest.mark.asyncio
async def test_get_activity_details_failure(db_session, mock_env_vars):
    """Test failure in retrieving activity details."""
    with patch('backend.app.services.garmin.garth.Client', new_callable=create_garth_client_mock) as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.get_activity.side_effect = Exception("Activity not found")
        service = GarminService(db_session)
        service.client = mock_instance
        with pytest.raises(GarminAPIError, match="Failed to fetch activity details"):
            await service.get_activity_details("123")
        mock_instance.get_activity.assert_called_once_with("123")

@pytest.mark.asyncio
async def test_is_authenticated(db_session):
    """Test is_authenticated method"""
    service = GarminService(db_session)
    assert service.is_authenticated() is False
    service.client = MagicMock()
    assert service.is_authenticated() is True