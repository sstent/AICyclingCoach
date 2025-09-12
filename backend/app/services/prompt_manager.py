from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from backend.app.models.prompt import Prompt
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Service for managing AI prompts with versioning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_prompt(self, action_type: str, model: str = None) -> str:
        """Get the active prompt for a specific action type."""
        query = select(Prompt).where(
            Prompt.action_type == action_type,
            Prompt.active == True
        )
        if model:
            query = query.where(Prompt.model == model)

        result = await self.db.execute(query.order_by(Prompt.version.desc()))
        prompt = result.scalar_one_or_none()
        return prompt.prompt_text if prompt else None

    async def create_prompt_version(
        self,
        action_type: str,
        prompt_text: str,
        model: str = None
    ) -> Prompt:
        """Create a new version of a prompt."""
        # Deactivate previous versions
        await self.db.execute(
            update(Prompt)
            .where(Prompt.action_type == action_type)
            .values(active=False)
        )

        # Get next version number
        result = await self.db.execute(
            select(func.max(Prompt.version))
            .where(Prompt.action_type == action_type)
        )
        max_version = result.scalar() or 0

        # Create new prompt
        new_prompt = Prompt(
            action_type=action_type,
            model=model,
            prompt_text=prompt_text,
            version=max_version + 1,
            active=True
        )

        self.db.add(new_prompt)
        await self.db.commit()
        await self.db.refresh(new_prompt)

        logger.info(f"Created new prompt version {new_prompt.version} for {action_type}")
        return new_prompt

    async def get_prompt_history(self, action_type: str) -> list[Prompt]:
        """Get all versions of prompts for an action type."""
        result = await self.db.execute(
            select(Prompt)
            .where(Prompt.action_type == action_type)
            .order_by(Prompt.version.desc())
        )
        return result.scalars().all()

    async def activate_prompt_version(self, prompt_id: int) -> bool:
        """Activate a specific prompt version."""
        # First deactivate all prompts for this action type
        prompt = await self.db.get(Prompt, prompt_id)
        if not prompt:
            return False

        await self.db.execute(
            update(Prompt)
            .where(Prompt.action_type == prompt.action_type)
            .values(active=False)
        )

        # Activate the specific version
        prompt.active = True
        await self.db.commit()

        logger.info(f"Activated prompt version {prompt.version} for {prompt.action_type}")
        return True