from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.services.ai_service import AIService
from typing import AsyncGenerator


async def get_ai_service(db: AsyncSession = Depends(get_db)) -> AIService:
    """Get AI service instance with database dependency."""
    return AIService(db)