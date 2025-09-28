import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select
from backend.app.database import Base
from backend.app.services.workout_sync import WorkoutSyncService
from backend.app.services.garmin import GarminService, GarminAPIError, GarminAuthError
from backend.app.models.workout import Workout
from backend.app.models.garmin_sync_log import GarminSyncLog, GarminSyncStatus
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from backend.app.config import Settings

# --- Completely Rewritten Fixtures ---

@pytest.fixture(scope="function")
def test_engine():
    """Create a test engine for each test function."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    return engine

@pytest.fixture(scope="function")
async def setup_database(test_engine):
    """Set up the database schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture
async def db_session(test_engine, setup_database):
    """Create a database session for testing."""
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    session = async_session_factory()
    yield session
    await session.close()

@pytest.fixture
def mock_garmin_service():
    """Mock the GarminService for testing."""
    mock_service = MagicMock(spec=GarminService)
    mock_service.authenticate = AsyncMock(return_value=True)
    mock_service.get_activities = AsyncMock(return_value=[])
    mock_service.get_activity_details = AsyncMock(return_value={})
    return mock_service

@pytest.fixture
def settings() -> Settings:
   """Load settings from .env file."""
   load_dotenv()
   return Settings()

@pytest.fixture
def real_garmin_service(settings: Settings) -> GarminService:
   """Return a real GarminService instance with credentials from settings."""
   if not settings.GARMIN_USERNAME or not settings.GARMIN_PASSWORD:
       pytest.skip("GARMIN_USERNAME and GARMIN_PASSWORD must be set in .env for functional tests.")
   return GarminService()

# --- Test Cases ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_successful_sync_functional(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test successful synchronization of recent activities."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
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
    synced_count = await service.sync_recent_activities(days_back=7)

    # Assert
    assert synced_count == 1
    
    # Verify workout in DB
    result = await db_session.execute(select(Workout))
    workouts = result.scalars().all()
    assert len(workouts) == 1
    assert workouts[0].garmin_activity_id == '1001'
    assert workouts[0].activity_type == 'cycling'
    assert workouts[0].avg_power == 200.0
    assert 'temperature' in workouts[0].metrics

    # Verify sync log in DB
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == GarminSyncStatus.COMPLETED
    assert sync_logs[0].activities_synced == 1
    assert sync_logs[0].error_message is None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_with_no_new_activities(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test synchronization when no new activities are found."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
    # Arrange
    mock_garmin_service.get_activities.return_value = []  # No activities

    # Act
    synced_count = await service.sync_recent_activities(days_back=7)

    # Assert
    assert synced_count == 0
    result = await db_session.execute(select(Workout))
    workouts = result.scalars().all()
    assert len(workouts) == 0
    
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == GarminSyncStatus.COMPLETED
    assert sync_logs[0].activities_synced == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_with_authentication_error(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test synchronization failure due to Garmin authentication error."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
    # Arrange
    mock_garmin_service.get_activities.side_effect = GarminAuthError("Invalid credentials")

    # Act & Assert
    with pytest.raises(GarminAuthError):
        await service.sync_recent_activities(days_back=7)

    # Verify sync log in DB
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == GarminSyncStatus.AUTH_FAILED
    assert "Invalid credentials" in sync_logs[0].error_message

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_with_api_error(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test synchronization failure due to general Garmin API error."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
    # Arrange
    mock_garmin_service.get_activities.side_effect = GarminAPIError("Garmin service unavailable")

    # Act & Assert
    with pytest.raises(GarminAPIError):
        await service.sync_recent_activities(days_back=7)

    # Verify sync log in DB
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == GarminSyncStatus.FAILED
    assert "Garmin service unavailable" in sync_logs[0].error_message

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_with_activity_details_retry_success(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test successful retry of activity details fetch after initial failure."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
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
        synced_count = await service.sync_recent_activities(days_back=7)
        mock_sleep.assert_awaited_with(1)  # First retry delay

    # Assert
    assert synced_count == 1
    result = await db_session.execute(select(Workout))
    workouts = result.scalars().all()
    assert len(workouts) == 1
    assert workouts[0].garmin_activity_id == '1002'
    assert workouts[0].avg_hr == 160
    assert mock_garmin_service.get_activity_details.call_count == 2
    
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == GarminSyncStatus.COMPLETED

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_with_activity_details_retry_failure(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test activity details fetch eventually fails after multiple retries."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
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
        await service.sync_recent_activities(days_back=7)
        assert mock_garmin_service.get_activity_details.call_count == 3
        mock_sleep.assert_awaited_with(4)  # Last retry delay (2**(3-1))

    # Verify sync log in DB
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 1
    assert sync_logs[0].status == GarminSyncStatus.FAILED
    assert "Service unavailable" in sync_logs[0].error_message
    
    # No workout should be saved
    result = await db_session.execute(select(Workout))
    workouts = result.scalars().all()
    assert len(workouts) == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_with_duplicate_activities_in_garmin_feed(db_session: AsyncSession, mock_garmin_service: MagicMock):
    """Test handling of duplicate activities appearing in the Garmin feed."""
    # Create service with the actual session
    service = WorkoutSyncService(db=db_session)
    service.garmin_service = mock_garmin_service
    
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
    await service.sync_recent_activities(days_back=7)

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
    mock_garmin_service.get_activity_details.return_value = {'averageHR': 130}  # for activity 1005

    # Act
    synced_count = await service.sync_recent_activities(days_back=7)

    # Assert
    assert synced_count == 1  # Only 1005 should be synced
    result = await db_session.execute(select(Workout))
    workouts = result.scalars().all()
    assert len(workouts) == 2
    assert any(w.garmin_activity_id == '1004' for w in workouts)
    assert any(w.garmin_activity_id == '1005' for w in workouts)
    
    result = await db_session.execute(select(GarminSyncLog))
    sync_logs = result.scalars().all()
    assert len(sync_logs) == 2
    assert sync_logs[1].activities_synced == 1  # Second log should show 1 activity synced

@pytest.mark.functional
@pytest.mark.asyncio
async def test_garmin_sync_with_real_creds(db_session: AsyncSession, real_garmin_service: GarminService):
   """
   Test a real Garmin sync. This is a functional test that makes a live API call.
   It requires GARMIN_USERNAME and GARMIN_PASSWORD to be set in the .env file.
   """
   # Arrange
   service = WorkoutSyncService(db=db_session)
   service.garmin_service = real_garmin_service

   # Act
   # We sync the last 1 day to keep the test fast
   synced_count = await service.sync_recent_activities(days_back=1)

   # Assert
   assert synced_count >= 0  # We can't know the exact count, but it should not fail

   # Verify sync log in DB
   result = await db_session.execute(select(GarminSyncLog).order_by(GarminSyncLog.id.desc()))
   latest_log = result.scalars().first()
   
   assert latest_log is not None
   assert latest_log.status == GarminSyncStatus.COMPLETED
   assert latest_log.activities_synced == synced_count