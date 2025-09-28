import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.database import Base
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.services.garmin import GarminService, GarminAPIError, GarminAuthError
from backend.app.models.workout import Workout
from backend.app.models.garmin_sync_log import GarminSyncLog
from datetime import datetime, timedelta
import os

# --- Fixtures for Functional Testing ---

@pytest.fixture(name="async_engine")
def async_engine_fixture():
    """Provides an asynchronous engine for an in-memory SQLite database."""
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

@pytest.fixture(name="async_session")
async def async_session_fixture(async_engine):
    """Provides an asynchronous session for an in-memory SQLite database."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
    )
    async with AsyncSessionLocal() as session:
        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_garmin_service():
    """Mocks the GarminService for functional tests."""
    with patch('backend.app.services.workout_sync.GarminService', autospec=True) as MockGarminService:
        mock_instance = MockGarminService.return_value
        mock_instance.login = AsyncMock(return_value=True)
        mock_instance.get_activities = AsyncMock(return_value=[])
        mock_instance.get_activity_details = AsyncMock(return_value={})
        yield mock_instance

@pytest.fixture
def workout_sync_service(async_session: AsyncSession, mock_garmin_service: MagicMock) -> WorkoutSyncService:
    """Provides a WorkoutSyncService instance with a correctly resolved async session."""
    import asyncio
    session = asyncio.run(async_session.__anext__())
    service = WorkoutSyncService(db=session)
    service.garmin_service = mock_garmin_service
    return service

# --- Test Cases ---

@pytest.mark.asyncio
async def test_successful_sync_functional(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test successful synchronization of recent activities."""
    # Arrange
    mock_garmin_service.get_activities.return_value = [
        {
            'activityId': '1001',
            'activityType': {'typeKey': 'cycling'},
            'startTimeLocal': (datetime.now() - timedelta(days=1)).isoformat(),
            'duration': 3600,
            'distance': 50000,
            'averageHR': 150,
            'maxHR': 180,
            'avgPower': 200,
            'elevationGain': 500
        }
    ]
    mock_garmin_service.get_activity_details.return_value = {
        'avgPower': 200,
        'elevationGain': 500,
        'temperature': 25
    }

    # Act
    synced_count = await workout_sync_service.sync_recent_activities(days_back=7)

    # Assert
    assert synced_count == 1
    
    # Verify workout in DB
    workouts = (await async_session.execute(select(Workout))).scalars().all()
    assert len(workouts) == 1
    assert workouts[0].garmin_activity_id == '1001'
    assert workouts[0].activity_type == 'cycling'
    assert workouts[0].avg_power == 200
    assert 'temperature' in workouts[0].metrics

    # Verify sync log in DB
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == 'success'
    assert sync_logs[0].activities_synced == 1
    assert sync_logs[0].error_message is None

@pytest.mark.asyncio
async def test_sync_with_no_new_activities(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test synchronization when no new activities are found."""
    # Arrange
    mock_garmin_service.get_activities.return_value = [] # No activities

    # Act
    synced_count = await workout_sync_service.sync_recent_activities(days_back=7)

    # Assert
    assert synced_count == 0
    workouts = (await async_session.execute(select(Workout))).scalars().all()
    assert len(workouts) == 0
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == 'success'
    assert sync_logs[0].activities_synced == 0

@pytest.mark.asyncio
async def test_sync_with_authentication_error(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test synchronization failure due to Garmin authentication error."""
    # Arrange
    mock_garmin_service.get_activities.side_effect = GarminAuthError("Invalid credentials")

    # Act & Assert
    with pytest.raises(GarminAuthError):
        await workout_sync_service.sync_recent_activities(days_back=7)

    # Verify sync log in DB
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == 'auth_error'
    assert "Invalid credentials" in sync_logs[0].error_message

@pytest.mark.asyncio
async def test_sync_with_api_error(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test synchronization failure due to general Garmin API error."""
    # Arrange
    mock_garmin_service.get_activities.side_effect = GarminAPIError("Garmin service unavailable")

    # Act & Assert
    with pytest.raises(GarminAPIError):
        await workout_sync_service.sync_recent_activities(days_back=7)

    # Verify sync log in DB
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == 'api_error'
    assert "Garmin service unavailable" in sync_logs[0].error_message

@pytest.mark.asyncio
async def test_sync_with_activity_details_retry_success(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test successful retry of activity details fetch after initial failure."""
    # Arrange
    mock_garmin_service.get_activities.return_value = [
        {
            'activityId': '1002',
            'activityType': {'typeKey': 'running'},
            'startTimeLocal': (datetime.now() - timedelta(days=2)).isoformat(),
            'duration': 3000,
            'distance': 10000
        }
    ]
    # First call to get_activity_details fails, second succeeds
    mock_garmin_service.get_activity_details.side_effect = [
        GarminAPIError("Temporary network issue"),
        {'averageHR': 160, 'maxHR': 190}
    ]

    # Act
    # Mock asyncio.sleep to avoid actual delays during tests
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        synced_count = await workout_sync_service.sync_recent_activities(days_back=7)
        mock_sleep.assert_awaited_with(1) # First retry delay

    # Assert
    assert synced_count == 1
    workouts = (await async_session.execute(select(Workout))).scalars().all()
    assert len(workouts) == 1
    assert workouts[0].garmin_activity_id == '1002'
    assert workouts[0].avg_hr == 160
    assert mock_garmin_service.get_activity_details.call_count == 2
    
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == 'success'

@pytest.mark.asyncio
async def test_sync_with_activity_details_retry_failure(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test activity details fetch eventually fails after multiple retries."""
    # Arrange
    mock_garmin_service.get_activities.return_value = [
        {
            'activityId': '1003',
            'activityType': {'typeKey': 'swimming'},
            'startTimeLocal': (datetime.now() - timedelta(days=3)).isoformat(),
            'duration': 2000,
            'distance': 2000
        }
    ]
    # All calls to get_activity_details fail
    mock_garmin_service.get_activity_details.side_effect = [
        GarminAPIError("Service unavailable"),
        GarminAPIError("Service unavailable"),
        GarminAPIError("Service unavailable")
    ]

    # Act & Assert
    with pytest.raises(GarminAPIError), \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        await workout_sync_service.sync_recent_activities(days_back=7)
        assert mock_garmin_service.get_activity_details.call_count == 3
        mock_sleep.assert_awaited_with(4) # Last retry delay (2**(3-1))

    # Verify sync log in DB
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == 'api_error'
    assert "Service unavailable" in sync_logs[0].error_message
    
    # No workout should be saved
    workouts = (await async_session.execute(select(Workout))).scalars().all()
    assert len(workouts) == 0

@pytest.mark.asyncio
async def test_sync_with_duplicate_activities_in_garmin_feed(workout_sync_service: WorkoutSyncService, async_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test handling of duplicate activities appearing in the Garmin feed."""
    # Arrange
    # First sync: add activity 1004
    mock_garmin_service.get_activities.return_value = [
        {
            'activityId': '1004',
            'activityType': {'typeKey': 'cycling'},
            'startTimeLocal': (datetime.now() - timedelta(days=4)).isoformat(),
            'duration': 4000,
            'distance': 60000
        }
    ]
    mock_garmin_service.get_activity_details.return_value = {'averageHR': 140}
    await workout_sync_service.sync_recent_activities(days_back=7)

    # Second sync: activity 1004 is present again, plus a new activity 1005
    mock_garmin_service.get_activities.return_value = [
        {
            'activityId': '1004',
            'activityType': {'typeKey': 'cycling'},
            'startTimeLocal': (datetime.now() - timedelta(days=4)).isoformat(),
            'duration': 4000,
            'distance': 60000
        },
        {
            'activityId': '1005',
            'activityType': {'typeKey': 'running'},
            'startTimeLocal': (datetime.now() - timedelta(days=5)).isoformat(),
            'duration': 2500,
            'distance': 5000
        }
    ]
    mock_garmin_service.get_activity_details.return_value = {'averageHR': 130} # for activity 1005

    # Act
    synced_count = await workout_sync_service.sync_recent_activities(days_back=7)

    # Assert
    assert synced_count == 1 # Only 1005 should be synced
    workouts = (await async_session.execute(select(Workout))).scalars().all()
    assert len(workouts) == 2
    assert any(w.garmin_activity_id == '1004' for w in workouts)
    assert any(w.garmin_activity_id == '1005' for w in workouts)
    
    sync_logs = (await async_session.execute(select(GarminSyncLog))).scalars().all()
    assert len(sync_logs) == 2
    assert sync_logs[1].activities_synced == 1 # Second log should show 1 activity synced