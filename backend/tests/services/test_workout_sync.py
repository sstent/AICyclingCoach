import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.services.garmin import GarminAPIError, GarminAuthError
from backend.app.models.workout import Workout
from backend.app.models.garmin_sync_log import GarminSyncLog
from datetime import datetime, timedelta
import asyncio

@pytest.mark.asyncio
async def test_successful_sync():
    """Test successful sync of new activities"""
    # Create proper async mock for database session
    mock_db = AsyncMock()
    mock_db.add = MagicMock() # add is synchronous
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Mock the activity_exists check to return False (no duplicates)
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)
    
    service = WorkoutSyncService(mock_db)
    
    # Mock the garmin service methods
    service.garmin_service.get_activities = AsyncMock(return_value=[
        {
            'activityId': '123456',
            'activityType': {'typeKey': 'cycling'},
            'startTimeLocal': '2024-01-15T08:00:00Z',
            'duration': 3600,
            'distance': 25000
        }
    ])
    
    service.garmin_service.get_activity_details = AsyncMock(return_value={
        'averageHR': 150,
        'maxHR': 180,
        'avgPower': 250,
        'elevationGain': 500
    })
    
    result = await service.sync_recent_activities(days_back=7)
    
    assert result == 1
    assert mock_db.add.call_count >= 2  # sync_log and workout
    mock_db.commit.assert_awaited()

@pytest.mark.asyncio
async def test_duplicate_activity_handling():
    """Test skipping duplicate activities"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    service = WorkoutSyncService(mock_db)
    
    # Mock activity_exists to return True (activity exists)
    service.activity_exists = AsyncMock(return_value=True)
    
    service.garmin_service.get_activities = AsyncMock(return_value=[
        {'activityId': '123456', 'startTimeLocal': '2024-01-15T08:00:00Z'}
    ])
    
    result = await service.sync_recent_activities()
    
    assert result == 0 # No new activities synced
    mock_db.commit.assert_awaited()

@pytest.mark.asyncio
async def test_activity_detail_retry_logic():
    """Test retry logic for activity details"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    service = WorkoutSyncService(mock_db)
    service.activity_exists = AsyncMock(return_value=False)
    
    service.garmin_service.get_activities = AsyncMock(return_value=[
        {
            'activityId': '123456',
            'activityType': {'typeKey': 'cycling'},
            'startTimeLocal': '2024-01-15T08:00:00Z',
            'duration': 3600
        }
    ])
    
    # First call fails, second succeeds
    service.garmin_service.get_activity_details = AsyncMock(
        side_effect=[
            GarminAPIError("Temporary failure"),
            {'averageHR': 150, 'maxHR': 180}
        ]
    )
    
    # Mock asyncio.sleep to avoid actual delays in tests
    with patch('asyncio.sleep', new_callable=AsyncMock):
        result = await service.sync_recent_activities()
    
    assert service.garmin_service.get_activity_details.call_count == 2
    assert result == 1

@pytest.mark.asyncio
async def test_auth_error_handling():
    """Test authentication error handling"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    service = WorkoutSyncService(mock_db)
    
    # Mock authentication failure
    service.garmin_service.get_activities = AsyncMock(
        side_effect=GarminAuthError("Authentication failed")
    )
    
    with pytest.raises(GarminAuthError):
        await service.sync_recent_activities()
    
    # Check that sync log was created with auth error status
    sync_log_calls = [call for call in mock_db.add.call_args_list 
                     if isinstance(call[0][0], GarminSyncLog)]
    assert len(sync_log_calls) >= 1
    sync_log = sync_log_calls[0][0][0]
    assert sync_log.status == "auth_error"

@pytest.mark.asyncio
async def test_api_error_handling():
    """Test API error handling"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    service = WorkoutSyncService(mock_db)
    
    service.garmin_service.get_activities = AsyncMock(
        side_effect=GarminAPIError("API rate limit exceeded")
    )
    
    with pytest.raises(GarminAPIError):
        await service.sync_recent_activities()
    
    # Check sync log status
    sync_log_calls = [call for call in mock_db.add.call_args_list 
                     if isinstance(call[0][0], GarminSyncLog)]
    sync_log = sync_log_calls[0][0][0]
    assert sync_log.status == "api_error"
    assert "rate limit" in sync_log.error_message.lower()

@pytest.mark.asyncio
async def test_get_sync_status():
    """Test retrieval of latest sync status"""
    mock_db = AsyncMock()
    mock_log = GarminSyncLog(
        status="success", 
        activities_synced=5,
        last_sync_time=datetime.now()
    )
    
    # Mock the database query
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=mock_log)
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    service = WorkoutSyncService(mock_db)
    result = await service.get_latest_sync_status()
    
    assert result.status == "success"
    assert result.activities_synced == 5
    mock_db.execute.assert_awaited_once()

@pytest.mark.asyncio
async def test_activity_exists_check():
    """Test the activity_exists helper method"""
    mock_db = AsyncMock()
    
    # Mock existing activity
    mock_workout = Workout(garmin_activity_id="123456")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=mock_workout)
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    service = WorkoutSyncService(mock_db)
    exists = await service.activity_exists("123456")
    
    assert exists is True
    mock_db.execute.assert_awaited_once()

@pytest.mark.asyncio
async def test_activity_does_not_exist():
    """Test activity_exists when activity doesn't exist"""
    mock_db = AsyncMock()
    
    # Mock no existing activity
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    service = WorkoutSyncService(mock_db)
    exists = await service.activity_exists("nonexistent")
    
    assert exists is False

@pytest.mark.asyncio
async def test_parse_activity_data():
    """Test parsing of Garmin activity data"""
    mock_db = AsyncMock()
    service = WorkoutSyncService(mock_db)
    
    activity_data = {
        'activityId': '987654321',
        'activityType': {'typeKey': 'cycling'},
        'startTimeLocal': '2024-01-15T08:30:00Z',
        'duration': 7200,
        'distance': 50000,
        'averageHR': 145,
        'maxHR': 175,
        'avgPower': 230,
        'maxPower': 450,
        'averageBikingCadenceInRevPerMinute': 85,
        'elevationGain': 800
    }
    
    result = await service.parse_activity_data(activity_data)
    
    assert result['garmin_activity_id'] == '987654321'
    assert result['activity_type'] == 'cycling'
    assert result['duration_seconds'] == 7200
    assert result['distance_m'] == 50000
    assert result['avg_hr'] == 145
    assert result['max_hr'] == 175
    assert result['avg_power'] == 230
    assert result['max_power'] == 450
    assert result['avg_cadence'] == 85
    assert result['elevation_gain_m'] == 800
    assert result['metrics'] == activity_data  # Full data stored as JSONB

@pytest.mark.asyncio
async def test_sync_with_network_timeout():
    """Test handling of network timeouts during sync"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    service = WorkoutSyncService(mock_db)
    
    # Simulate timeout error
    import asyncio
    service.garmin_service.get_activities = AsyncMock(
        side_effect=asyncio.TimeoutError("Request timed out")
    )
    
    with pytest.raises(Exception):  # Should raise the timeout error
        await service.sync_recent_activities()
    
    # Verify error was logged
    sync_log_calls = [call for call in mock_db.add.call_args_list 
                     if isinstance(call[0][0], GarminSyncLog)]
    sync_log = sync_log_calls[0][0][0]
    assert sync_log.status == "error"