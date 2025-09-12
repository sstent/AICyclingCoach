import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.services.plan_evolution import PlanEvolutionService
from backend.app.models.plan import Plan
from backend.app.models.analysis import Analysis
from datetime import datetime

@pytest.mark.asyncio
async def test_evolve_plan_with_valid_analysis():
    """Test plan evolution with approved analysis and suggestions"""
    mock_db = AsyncMock()
    mock_plan = Plan(
        id=1,
        version=1,
        jsonb_plan={"weeks": []},
        parent_plan_id=None
    )
    mock_analysis = Analysis(
        approved=True,
        jsonb_feedback={"suggestions": ["More recovery"]}
    )
    
    service = PlanEvolutionService(mock_db)
    service.ai_service.evolve_plan = AsyncMock(return_value={"weeks": [{"recovery": True}]})
    
    result = await service.evolve_plan_from_analysis(mock_analysis, mock_plan)
    
    assert result.version == 2
    assert result.parent_plan_id == 1
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_evolution_skipped_for_unapproved_analysis():
    """Test plan evolution is skipped for unapproved analysis"""
    mock_db = AsyncMock()
    mock_analysis = Analysis(approved=False)
    
    service = PlanEvolutionService(mock_db)
    result = await service.evolve_plan_from_analysis(mock_analysis, MagicMock())
    
    assert result is None

@pytest.mark.asyncio
async def test_evolution_history_retrieval():
    """Test getting plan evolution history"""
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalars.return_value = [
        Plan(version=1), Plan(version=2)
    ]
    
    service = PlanEvolutionService(mock_db)
    history = await service.get_plan_evolution_history(1)
    
    assert len(history) == 2
    assert history[0].version == 1