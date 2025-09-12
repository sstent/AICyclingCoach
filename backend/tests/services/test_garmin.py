import pytest
from unittest.mock import AsyncMock, patch
from backend.app.services.garmin import GarminService
from backend.app.models.garmin_sync_log import GarminSyncStatus
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_garmin_authentication_success(db_session):
    """Test successful Garmin Connect authentication"""
    with patch('garth.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.login = AsyncMock(return_value=True)
        
        service = GarminService(db_session)
        result = await service.authenticate("test_user", "test_pass")
        
        assert result is True
        mock_instance.login.assert_awaited_once_with("test_user", "test_pass")

@pytest.mark.asyncio
async def test_garmin_authentication_failure(db_session):
    """Test authentication failure handling"""
    with patch('garth.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.login = AsyncMock(side_effect=Exception("Invalid credentials"))
        
        service = GarminService(db_session)
        result = await service.authenticate("bad_user", "wrong_pass")
        
        assert result is False
        log_entry = db_session.query(GarminSyncLog).first()
        assert log_entry.status == GarminSyncStatus.AUTH_FAILED

@pytest.mark.asyncio
async def test_activity_sync(db_session):
    """Test successful activity synchronization"""
    with patch('garth.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.connectapi = AsyncMock(return_value=[
            {"activityId": 123, "startTime": "2024-01-01T08:00:00"}
        ])
        
        service = GarminService(db_session)
        await service.sync_activities()
        
        # Verify workout created
        workout = db_session.query(Workout).first()
        assert workout.garmin_activity_id == 123
        # Verify sync log updated
        log_entry = db_session.query(GarminSyncLog).first()
        assert log_entry.status == GarminSyncStatus.COMPLETED

@pytest.mark.asyncio
async def test_rate_limiting_handling(db_session):
    """Test API rate limit error handling"""
    with patch('garth.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.connectapi = AsyncMock(side_effect=Exception("Rate limit exceeded"))
        
        service = GarminService(db_session)
        result = await service.sync_activities()
        
        assert result is False
        log_entry = db_session.query(GarminSyncLog).first()
        assert log_entry.status == GarminSyncStatus.FAILED
        assert "Rate limit" in log_entry.error_message

@pytest.mark.asyncio
async def test_session_persistence(db_session):
    """Test session cookie persistence"""
    service = GarminService(db_session)
    
    # Store session
    await service.store_session({"token": "test123"})
    session = await service.load_session()
    
    assert session == {"token": "test123"}
    assert Path("/app/data/sessions/garmin_session.pickle").exists()