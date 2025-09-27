import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.models.workout import Workout
from backend.app.models.garmin_sync_log import GarminSyncLog
from backend.app.services.garmin import GarminAuthError, GarminAPIError
from datetime import datetime, timedelta
import asyncio

@pytest.mark.asyncio
async def test_successful_sync():
    """Test successful sync of new activities"""
    mock_db = AsyncMock()
    mock_garmin = AsyncMock()
    mock_garmin.get_activities.return_value = [{'activityId': '123', 'startTimeLocal': '2024-01-01T08:00:00', 'duration': 3600, 'distance': 10000, 'activityType': {'typeKey': 'running'}}]
    mock_garmin.get_activity_details.return_value = {'metrics': 'data'}
    
    with patch('backend.app.services.workout_sync.WorkoutSyncService.activity_exists', new_callable=AsyncMock) as mock_activity_exists:
        mock_activity_exists.return_value = False
        service = WorkoutSyncService(mock_db)
        service.garmin_service = mock_garmin
        
        result = await service.sync_recent_activities()
        
        assert result == 1
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_activity_exists.assert_awaited_once_with('123')


@pytest.mark.asyncio
async def test_duplicate_activity_handling():
    """Test skipping duplicate activities"""
    mock_db = AsyncMock()
    with patch('backend.app.services.workout_sync.WorkoutSyncService.activity_exists', new_callable=AsyncMock) as mock_activity_exists:
        mock_activity_exists.return_value = True
        mock_garmin = AsyncMock()
        mock_garmin.get_activities.return_value = [{'activityId': '123'}]
        
        service = WorkoutSyncService(mock_db)
        service.garmin_service = mock_garmin
        
        result = await service.sync_recent_activities()
        assert result == 0
        mock_activity_exists.assert_awaited_once_with('123')


@pytest.mark.asyncio
async def test_activity_detail_retry_logic():
    """Test retry logic for activity details"""
    mock_db = AsyncMock()
    mock_garmin = AsyncMock()
    mock_garmin.get_activities.return_value = [{'activityId': '123', 'startTimeLocal': '2024-01-01T08:00:00', 'duration': 3600, 'distance': 10000, 'activityType': {'typeKey': 'running'}}]
    mock_garmin.get_activity_details.side_effect = [GarminAPIError("Error"), {'metrics': 'data'}]
    
    with patch('backend.app.services.workout_sync.WorkoutSyncService.activity_exists', new_callable=AsyncMock) as mock_activity_exists:
        mock_activity_exists.return_value = False
        service = WorkoutSyncService(mock_db)
        service.garmin_service = mock_garmin
        
        result = await service.sync_recent_activities()
        assert mock_garmin.get_activity_details.call_count == 2
        assert result == 1
        mock_activity_exists.assert_awaited_once_with('123')


@pytest.mark.asyncio
async def test_auth_error_handling():
    """Test authentication error handling"""
    mock_db = AsyncMock()
    mock_garmin = AsyncMock()
    mock_garmin.get_activities.side_effect = GarminAuthError("Auth failed")
    
    service = WorkoutSyncService(mock_db)
    service.garmin_service = mock_garmin
    
    with pytest.raises(GarminAuthError):
        await service.sync_recent_activities()
    
    sync_log = mock_db.add.call_args[0][0]
    assert sync_log.status == "auth_error"

@pytest.mark.asyncio
async def test_get_sync_status():
    """Test retrieval of latest sync status"""
    mock_db = AsyncMock()
    mock_log = GarminSyncLog(status="success")
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_log
    
    service = WorkoutSyncService(mock_db)
    result = await service.get_latest_sync_status()
    
    assert result.status == "success"