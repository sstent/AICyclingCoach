import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Use SQLite database in data directory
DATA_DIR = Path("data")
DATABASE_PATH = DATA_DIR / "cycling_coach.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATABASE_PATH}")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """Initialize the database by creating all tables."""
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Import all models to ensure they are registered
    from .models import (
        user, rule, plan, plan_rule, workout,
        analysis, route, section, garmin_sync_log, prompt
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)