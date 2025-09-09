import os
import asyncio
from typing import Dict, Any, List, Optional
import httpx
import json
from app.services.prompt_manager import PromptManager
from app.models.workout import Workout
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered analysis and plan generation."""

    def __init__(self, db_session):
        self.db = db_session
        self.prompt_manager = PromptManager(db_session)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("AI_MODEL", "anthropic/claude-3-sonnet-20240229")
        self.base_url = "https://openrouter.ai/api/v1"

    async def analyze_workout(self, workout: Workout, plan: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze a workout using AI and generate feedback."""
        prompt_template = await self.prompt_manager.get_active_prompt("workout_analysis")

        if not prompt_template:
            raise ValueError("No active workout analysis prompt found")

        # Build context from workout data
        workout_context = {
            "activity_type": workout.activity_type,
            "duration_minutes": workout.duration_seconds / 60 if workout.duration_seconds else 0,
            "distance_km": workout.distance_m / 1000 if workout.distance_m else 0,
            "avg_hr": workout.avg_hr,
            "avg_power": workout.avg_power,
            "elevation_gain": workout.elevation_gain_m,
            "planned_workout": plan
        }

        prompt = prompt_template.format(**workout_context)

        response = await self._make_ai_request(prompt)
        return self._parse_workout_analysis(response)

    async def generate_plan(self, rules: List[Dict], goals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a training plan using AI."""
        prompt_template = await self.prompt_manager.get_active_prompt("plan_generation")

        context = {
            "rules": rules,
            "goals": goals,
            "current_fitness_level": goals.get("fitness_level", "intermediate")
        }

        prompt = prompt_template.format(**context)
        response = await self._make_ai_request(prompt)
        return self._parse_plan_response(response)

    async def parse_rules_from_natural_language(self, natural_language: str) -> Dict[str, Any]:
        """Parse natural language rules into structured format."""
        prompt_template = await self.prompt_manager.get_active_prompt("rule_parsing")
        prompt = prompt_template.format(user_rules=natural_language)

        response = await self._make_ai_request(prompt)
        return self._parse_rules_response(response)

    async def evolve_plan(self, evolution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve a training plan using AI based on workout analysis."""
        prompt_template = await self.prompt_manager.get_active_prompt("plan_evolution")
        
        if not prompt_template:
            raise ValueError("No active plan evolution prompt found")

        prompt = prompt_template.format(**evolution_context)
        response = await self._make_ai_request(prompt)
        return self._parse_plan_response(response)

    async def _make_ai_request(self, prompt: str) -> str:
        """Make async request to OpenRouter API with retry logic."""
        async with httpx.AsyncClient() as client:
            for attempt in range(3):  # Simple retry logic
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 2000,
                        },
                        timeout=30.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                except Exception as e:
                    if attempt == 2:  # Last attempt
                        logger.error(f"AI request failed after 3 attempts: {str(e)}")
                        raise AIServiceError(f"AI request failed after 3 attempts: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def _parse_workout_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI response for workout analysis."""
        try:
            # Assume AI returns JSON
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:-3]
            return json.loads(clean_response)
        except json.JSONDecodeError:
            return {"raw_analysis": response, "structured": False}

    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for plan generation."""
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:-3]
            return json.loads(clean_response)
        except json.JSONDecodeError:
            return {"raw_plan": response, "structured": False}

    def _parse_rules_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for rule parsing."""
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:-3]
            return json.loads(clean_response)
        except json.JSONDecodeError:
            return {"raw_rules": response, "structured": False}


class AIServiceError(Exception):
    """Raised when AI service requests fail."""
    pass