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

    async def generate_plan(self, rules_text: str, goals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a training plan using AI with plaintext rules as per design spec."""
        prompt_template = await self.prompt_manager.get_active_prompt("plan_generation")

        context = {
            "rules_text": rules_text,  # Use plaintext rules directly
            "goals": goals,
            "current_fitness_level": goals.get("fitness_level", "intermediate")
        }

        prompt = prompt_template.format(**context)
        response = await self._make_ai_request(prompt)
        return self._parse_plan_response(response)

    async def generate_training_plan(self, rules_text: str, goals: Dict[str, Any], preferred_routes: List[int]) -> Dict[str, Any]:
        """Generate a training plan using AI with plaintext rules as per design specification."""
        prompt_template = await self.prompt_manager.get_active_prompt("training_plan_generation")
        if not prompt_template:
            # Fallback to general plan generation prompt
            prompt_template = await self.prompt_manager.get_active_prompt("plan_generation")

        context = {
            "rules_text": rules_text,  # Use plaintext rules directly without parsing
            "goals": goals,
            "preferred_routes": preferred_routes,
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
        parsed_rules = self._parse_rules_response(response)
        
        # Add confidence scoring to the parsed rules
        parsed_rules = self._add_confidence_scoring(parsed_rules)
        
        return parsed_rules

    def _add_confidence_scoring(self, parsed_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Add confidence scoring to parsed rules based on parsing quality."""
        confidence_score = self._calculate_confidence_score(parsed_rules)
        
        # Add confidence score to the parsed rules
        if isinstance(parsed_rules, dict):
            parsed_rules["_confidence"] = confidence_score
            parsed_rules["_parsing_quality"] = self._get_parsing_quality(confidence_score)
        
        return parsed_rules

    def _calculate_confidence_score(self, parsed_rules: Dict[str, Any]) -> float:
        """Calculate confidence score based on parsing quality."""
        if not isinstance(parsed_rules, dict):
            return 0.5  # Default confidence for non-dict responses
        
        score = 0.0
        # Score based on presence of key cycling training rule fields
        key_fields = {
            "max_rides_per_week": 0.3,
            "min_rest_between_hard": 0.2,
            "max_duration_hours": 0.2,
            "weather_constraints": 0.3,
            "intensity_limits": 0.2,
            "schedule_constraints": 0.2
        }
        
        for field, weight in key_fields.items():
            if parsed_rules.get(field) is not None:
                score += weight
        
        return min(score, 1.0)

    def _get_parsing_quality(self, confidence_score: float) -> str:
        """Get parsing quality description based on confidence score."""
        if confidence_score >= 0.8:
            return "excellent"
        elif confidence_score >= 0.6:
            return "good"
        elif confidence_score >= 0.4:
            return "fair"
        else:
            return "poor"

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