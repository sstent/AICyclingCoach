from fastapi import HTTPException, Header, status
import os

async def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """Dependency to verify API key header"""
    expected_key = os.getenv("API_KEY")
    if not expected_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )