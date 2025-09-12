from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.app.database import get_db
from backend.app.models.prompt import Prompt
from backend.app.schemas.prompt import Prompt as PromptSchema, PromptCreate, PromptUpdate
from backend.app.services.prompt_manager import PromptManager

router = APIRouter()


@router.get("/", response_model=List[PromptSchema])
async def read_prompts(db: AsyncSession = Depends(get_db)):
    """Get all prompts."""
    result = await db.execute(select(Prompt))
    return result.scalars().all()


@router.get("/{prompt_id}", response_model=PromptSchema)
async def read_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific prompt by ID."""
    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/", response_model=PromptSchema)
async def create_prompt(
    prompt: PromptCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prompt version."""
    prompt_manager = PromptManager(db)
    new_prompt = await prompt_manager.create_prompt_version(
        action_type=prompt.action_type,
        prompt_text=prompt.prompt_text,
        model=prompt.model
    )
    return new_prompt


@router.get("/active/{action_type}")
async def get_active_prompt(
    action_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the active prompt for a specific action type."""
    prompt_manager = PromptManager(db)
    prompt_text = await prompt_manager.get_active_prompt(action_type)
    if not prompt_text:
        raise HTTPException(status_code=404, detail=f"No active prompt found for {action_type}")
    return {"action_type": action_type, "prompt_text": prompt_text}


@router.get("/history/{action_type}", response_model=List[PromptSchema])
async def get_prompt_history(
    action_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the version history for a specific action type."""
    prompt_manager = PromptManager(db)
    prompts = await prompt_manager.get_prompt_history(action_type)
    return prompts


@router.post("/{prompt_id}/activate")
async def activate_prompt_version(
    prompt_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Activate a specific prompt version."""
    prompt_manager = PromptManager(db)
    success = await prompt_manager.activate_prompt_version(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"message": "Prompt version activated successfully"}