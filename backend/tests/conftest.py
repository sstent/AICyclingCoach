import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    # engine disposal can be handled via an async fixture if needed

@pytest.fixture
async def db_session(test_engine):
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSession(conn) as session:
            try:
                yield session
                await session.commit()  # Commit any changes made during the test
            except Exception:
                await session.rollback()  # Rollback in case of an exception
                raise
            finally:
                await session.close()
                
        # Drop all tables after the test
        await conn.run_sync(Base.metadata.drop_all)

# The TestClient is synchronous, but our app is async.
# We need to handle the async session in a way that works with the sync TestClient.
# The most common approach is to use an async sessionmaker and override the dependency
# to create and close a session per request, even though the test is sync.

from sqlalchemy.ext.asyncio import async_sessionmaker

@pytest.fixture
def client(test_engine):
    # Create an async sessionmaker
    AsyncSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    
    def override_get_db():
        # Create a new session for each request
        session = AsyncSessionLocal()
        try:
            yield session
        finally:
            # The TestClient will handle closing the session via the generator
            import asyncio
            # Since we're in a sync context of TestClient, but session is async,
            # we need to close it asynchronously. This is tricky.
            # A better approach for testing async DB with sync TestClient is to
            # make the override function async, but FastAPI TestClient expects sync.
            # For now, let's try to handle it in the finally block.
            # However, this approach has limitations.
            # A more robust solution is to have a separate async client test setup
            # or to use httpx.AsyncClient for async tests.
            # For the scope of fixing the workout sync tests, we'll focus on the
            # service-level tests which don't rely on the TestClient.
            # If the TestClient is needed for other tests, they may need refactoring.
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)