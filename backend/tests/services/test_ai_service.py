import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai_service import AIService, AIServiceError
from app.models.workout import Workout
import json

@pytest.mark.asyncio
async def test_analyze_workout_success():
    """Test successful workout analysis with valid API response"""
    mock_db = MagicMock()
    mock_prompt = MagicMock()
    mock_prompt.format.return_value = "test prompt"
    
    ai_service = AIService(mock_db)
    ai_service.prompt_manager.get_active_prompt = AsyncMock(return_value=mock_prompt)
    
    test_response = json.dumps({
        "performance_summary": "Good workout",
        "suggestions": ["More recovery"]
    })
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": test_response}}]}
        )
        
        workout = Workout(activity_type="cycling", duration_seconds=3600)
        result = await ai_service.analyze_workout(workout)
        
        assert "performance_summary" in result
        assert len(result["suggestions"]) == 1

@pytest.mark.asyncio
async def test_generate_plan_success():
    """Test plan generation with structured response"""
    mock_db = MagicMock()
    ai_service = AIService(mock_db)
    ai_service.prompt_manager.get_active_prompt = AsyncMock(return_value="Plan prompt: {rules} {goals}")
    
    test_plan = {
        "weeks": [{"workouts": ["ride"]}],
        "focus": "endurance"
    }
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": json.dumps(test_plan)}}]}
        )
        
        result = await ai_service.generate_plan([], {})
        assert "weeks" in result
        assert result["focus"] == "endurance"

@pytest.mark.asyncio
async def test_api_retry_logic():
    """Test API request retries on failure"""
    mock_db = MagicMock()
    ai_service = AIService(mock_db)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.side_effect = Exception("API failure")
        
        with pytest.raises(AIServiceError):
            await ai_service._make_ai_request("test")
            
        assert mock_post.call_count == 3

@pytest.mark.asyncio
async def test_invalid_json_handling():
    """Test graceful handling of invalid JSON responses"""
    mock_db = MagicMock()
    ai_service = AIService(mock_db)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "invalid{json"}}]}
        )
        
        result = await ai_service.parse_rules_from_natural_language("test")
        assert "raw_rules" in result
        assert not result["structured"]

@pytest.mark.asyncio
async def test_code_block_parsing():
    """Test extraction of JSON from code blocks"""
    mock_db = MagicMock()
    ai_service = AIService(mock_db)
    
    test_response = "```json\n" + json.dumps({"max_rides": 4}) + "\n```"
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": test_response}}]}
        )
        
        result = await ai_service.evolve_plan({})
        assert "max_rides" in result
        assert result["max_rides"] == 4