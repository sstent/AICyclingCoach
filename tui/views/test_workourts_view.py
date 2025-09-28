"""
Comprehensive pytest tests for WorkoutView TUI component.
Tests async data loading, service calls, and UI interactions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from textual.app import App
from textual.widgets import DataTable, Static, Button, TabbedContent, Collapsible
from tui.widgets.loading import LoadingSpinner

from tui.views.workouts import WorkoutView, WorkoutMetricsChart, WorkoutAnalysisPanel
from tui.services.workout_service import WorkoutService


# Mock data fixtures
@pytest.fixture
def mock_workouts():
    """Sample workout data for testing."""
    return [
        {
            "id": 1,
            "garmin_activity_id": "123456789",
            "activity_type": "cycling",
            "start_time": "2024-01-15T14:30:00Z",
            "duration_seconds": 4500,
            "distance_m": 32500,
            "avg_hr": 145,
            "max_hr": 165,
            "avg_power": 180,
            "max_power": 320,
            "avg_cadence": 85,
            "elevation_gain_m": 450
        },
        {
            "id": 2,
            "garmin_activity_id": "987654321",
            "activity_type": "running",
            "start_time": "2024-01-14T09:15:00Z",
            "duration_seconds": 2700,
            "distance_m": 8000,
            "avg_hr": 155,
            "max_hr": 175,
            "avg_power": None,
            "max_power": None,
            "avg_cadence": 180,
            "elevation_gain_m": 120
        }
    ]


@pytest.fixture
def mock_sync_status():
    """Sample sync status data for testing."""
    return {
        "status": "connected",
        "last_sync_time": "2024-01-15T15:00:00Z",
        "activities_synced": 25,
        "error_message": None
    }


@pytest.fixture
def mock_workout_analyses():
    """Sample workout analysis data for testing."""
    return [
        {
            "id": 1,
            "workout_id": 1,
            "analysis_type": "performance",
            "feedback": {
                "effort_level": "moderate",
                "pacing": "consistent",
                "heart_rate_zones": "well distributed"
            },
            "suggestions": {
                "recovery": "Take an easy day tomorrow",
                "training": "Focus on interval training next week"
            },
            "approved": False,
            "created_at": "2024-01-15T16:00:00Z"
        }
    ]


@pytest.fixture
def mock_workout_service():
    """Mock WorkoutService with all required methods."""
    service = AsyncMock(spec=WorkoutService)
    service.get_workouts = AsyncMock()
    service.get_sync_status = AsyncMock()
    service.get_workout_analyses = AsyncMock()
    service.sync_garmin_activities = AsyncMock()
    service.analyze_workout = AsyncMock()
    service.approve_analysis = AsyncMock()
    return service


class TestWorkoutView:
    """Test suite for WorkoutView component."""

    @pytest.mark.asyncio
    async def test_workout_view_initialization(self):
        """Test WorkoutView initializes with correct default state."""
        async with App().run_test() as pilot:
            view = WorkoutView()
            await pilot.app.mount(view)
            assert view.workouts == []
            assert view.selected_workout is None
            assert view.workout_analyses == []
            assert view.loading is True
            assert view.sync_status == {}
            assert view.error_message is None

    @pytest.mark.asyncio
    async def test_load_workouts_data_success(self, mock_workouts, mock_sync_status):
        """Test successful loading of workouts data."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)

            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.get_workouts.return_value = mock_workouts
                mock_service.get_sync_status.return_value = mock_sync_status
                mock_service_class.return_value = mock_service
                
                # Call the method
                result = await workout_view._load_workouts_data()
                
                # Verify results
                workouts, sync_status = result
                assert workouts == mock_workouts
                assert sync_status == mock_sync_status
                
                # Verify service calls
                mock_service.get_workouts.assert_called_once_with(limit=50)
                mock_service.get_sync_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_workouts_data_database_error(self):
        """Test handling of database errors during workout loading."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local:
                # Setup mock to raise exception
                mock_session_local.return_value.__aenter__.side_effect = Exception("Database connection failed")
                
                # Should raise the exception
                with pytest.raises(Exception) as exc_info:
                    await workout_view._load_workouts_data()
                
                assert "Database connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_workouts_with_timeout(self, mock_workouts, mock_sync_status):
        """Test workout loading with timeout functionality."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            # Mock the actual loading method to return quickly
            with patch.object(workout_view, '_load_workouts_data') as mock_load:
                mock_load.return_value = (mock_workouts, mock_sync_status)
                
                # Should complete successfully within timeout
                result = await workout_view._load_workouts_with_timeout()
                workouts, sync_status = result
                
                assert workouts == mock_workouts
                assert sync_status == mock_sync_status
    
    @pytest.mark.asyncio
    async def test_load_workouts_timeout_error(self):
        """Test timeout handling during workout loading."""
        import asyncio
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            # Mock the actual loading method to hang
            async def slow_load():
                await asyncio.sleep(0.1)  # Longer than timeout
                return [], {}
            
            workout_view.LOAD_TIMEOUT = 0.01

            with patch.object(workout_view, '_load_workouts_data', side_effect=slow_load):
                with pytest.raises(Exception) as exc_info:
                    await workout_view._load_workouts_with_timeout()
                
                assert "timed out" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_on_workouts_loaded_success(self, mock_workouts, mock_sync_status):
        """Test successful handling of loaded workout data."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.loading = True
            workout_view.error_message = "Previous error"
            
            # Mock the UI update methods
            with patch.object(workout_view, 'refresh') as mock_refresh, \
                 patch.object(workout_view, 'populate_workouts_table') as mock_populate, \
                 patch.object(workout_view, 'update_sync_status') as mock_update_sync:
                
                # Call the method
                workout_view.on_workouts_loaded((mock_workouts, mock_sync_status))
                
                # Verify state updates
                assert workout_view.workouts == mock_workouts
                assert workout_view.sync_status == mock_sync_status
                assert workout_view.loading is False
                assert workout_view.error_message is None
                
                # Verify UI method calls
                mock_refresh.assert_called_once_with(layout=True)
                mock_populate.assert_called_once()
                mock_update_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_workouts_loaded_error_handling(self):
        """Test error handling in on_workouts_loaded."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.loading = True
            
            # Mock refresh to raise exception
            with patch.object(workout_view, 'refresh', side_effect=Exception("UI Error")):
                try:
                    # Should handle the exception gracefully
                    workout_view.on_workouts_loaded(([], {}))
                except Exception:
                    # The exception is caught and handled inside the method
                    pass
                
                # Should still update loading state and set error
                assert workout_view.loading is False
                assert "Failed to process loaded data" in str(workout_view.error_message)
    
    @pytest.mark.asyncio
    async def test_populate_workouts_table(self, mock_workouts):
        """Test populating the workouts table with data."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.workouts = mock_workouts
            
            # Mock the DataTable widget
            mock_table = MagicMock(spec=DataTable)
            
            with patch.object(workout_view, 'query_one', return_value=mock_table):
                await workout_view.populate_workouts_table()
                
                # Verify table was cleared and populated
                mock_table.clear.assert_called_once()
                assert mock_table.add_row.call_count == len(mock_workouts)
                
                # Check first workout data formatting
                first_call_args = mock_table.add_row.call_args_list[0][0]
                assert "01/15 14:30" in first_call_args[0]
                assert "cycling" in first_call_args[1]
                assert "75min" in first_call_args[2]
                assert "32.5km" in first_call_args[3]
                assert "145 BPM" in first_call_args[4]
                assert "180 W" in first_call_args[5]
    
    @pytest.mark.asyncio
    async def test_update_sync_status(self, mock_sync_status):
        """Test updating sync status display."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.sync_status = mock_sync_status
            
            # Mock the Status widget
            mock_status_text = MagicMock(spec=Static)
            
            with patch.object(workout_view, 'query_one', return_value=mock_status_text):
                await workout_view.update_sync_status()
                
                # Verify status text was updated
                mock_status_text.update.assert_called_once()
                update_text = mock_status_text.update.call_args[0][0]
                
                assert "Connected" in update_text
                assert "2024-01-15 15:00" in update_text
                assert "25" in update_text
    
    @pytest.mark.asyncio
    async def test_sync_garmin_activities_success(self):
        """Test successful Garmin sync operation."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.sync_garmin_activities.return_value = {
                    "status": "success",
                    "activities_synced": 5,
                    "message": "Sync completed"
                }
                mock_service_class.return_value = mock_service
                
                # Mock the refresh methods
                with patch.object(workout_view, 'check_sync_status') as mock_check_sync, \
                     patch.object(workout_view, 'refresh_workouts') as mock_refresh_workouts:
                    
                    await workout_view.sync_garmin_activities()
                    
                    # Verify service call
                    mock_service.sync_garmin_activities.assert_called_once_with(days_back=14)
                    
                    # Verify UI refresh calls
                    mock_check_sync.assert_called_once()
                    mock_refresh_workouts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_garmin_activities_failure(self):
        """Test handling of Garmin sync failure."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.sync_garmin_activities.return_value = {
                    "status": "error",
                    "activities_synced": 0,
                    "message": "Authentication failed"
                }
                mock_service_class.return_value = mock_service
                
                # Mock the refresh methods
                with patch.object(workout_view, 'check_sync_status') as mock_check_sync, \
                     patch.object(workout_view, 'refresh_workouts') as mock_refresh_workouts:
                    
                    await workout_view.sync_garmin_activities()
                    
                    # Should still call refresh methods even on failure
                    mock_check_sync.assert_called_once()
                    mock_refresh_workouts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_selected_workout_success(self, mock_workouts, mock_workout_analyses):
        """Test successful workout analysis."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.selected_workout = mock_workouts[0]
            
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.analyze_workout.return_value = {
                    "status": "success",
                    "message": "Analysis completed"
                }
                mock_service.get_workout_analyses.return_value = mock_workout_analyses
                mock_service_class.return_value = mock_service
                
                # Mock refresh and message posting
                with patch.object(workout_view, 'refresh') as mock_refresh, \
                     patch.object(workout_view, 'post_message') as mock_post_message:
                    
                    await workout_view.analyze_selected_workout()
                    
                    # Verify service calls
                    mock_service.analyze_workout.assert_called_once_with(1)  # workout ID
                    mock_service.get_workout_analyses.assert_called_once_with(1)
                    
                    # Verify UI updates
                    assert workout_view.workout_analyses == mock_workout_analyses
                    mock_refresh.assert_called()
                    
                    # Verify message posting
                    assert mock_post_message.called
                    message = mock_post_message.call_args[0][0]
                    assert hasattr(message, 'workout_id')
                    assert message.workout_id == 1
    
    @pytest.mark.asyncio
    async def test_analyze_selected_workout_no_selection(self):
        """Test workout analysis when no workout is selected."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.selected_workout = None
            
            # Should not raise exception, just log warning
            await workout_view.analyze_selected_workout()
            
            # No service calls should be made
            # (This would be verified by not mocking any services)
    
    @pytest.mark.asyncio
    async def test_approve_analysis_success(self, mock_workouts):
        """Test successful analysis approval."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.selected_workout = mock_workouts[0]
            
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.approve_analysis.return_value = {
                    "status": "success",
                    "message": "Analysis approved"
                }
                mock_service.get_workout_analyses.return_value = []
                mock_service_class.return_value = mock_service
                
                # Mock refresh
                with patch.object(workout_view, 'refresh') as mock_refresh:
                    
                    await workout_view.approve_analysis(1)
                    
                    # Verify service calls
                    mock_service.approve_analysis.assert_called_once_with(1)
                    mock_service.get_workout_analyses.assert_called_once_with(1)
                    
                    # Verify UI refresh
                    mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_workout_details(self, mock_workouts, mock_workout_analyses):
        """Test showing workout details view."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.get_workout_analyses.return_value = mock_workout_analyses
                mock_service_class.return_value = mock_service
                
                # Mock TabbedContent widget
                mock_tabs = MagicMock(spec=TabbedContent)
                
                with patch.object(workout_view, 'refresh') as mock_refresh, \
                     patch.object(workout_view, 'query_one', return_value=mock_tabs), \
                     patch.object(workout_view, 'post_message') as mock_post_message:
                    
                    await workout_view.show_workout_details(mock_workouts[0])
                    
                    # Verify state updates
                    assert workout_view.selected_workout == mock_workouts[0]
                    assert workout_view.workout_analyses == mock_workout_analyses
                    
                    # Verify service call
                    mock_service.get_workout_analyses.assert_called_once_with(1)
                    
                    # Verify UI updates
                    mock_refresh.assert_called()
                    assert mock_tabs.active == "workout-details-tab"
                    
                    # Verify message posting
                    mock_post_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_watch_loading_state_change(self):
        """Test reactive response to loading state changes."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view._mounted = True
            
            with patch.object(workout_view, 'refresh') as mock_refresh:
                # Trigger loading state change
                workout_view.loading = False
                workout_view.watch_loading(False)
                
                # Should trigger refresh
                mock_refresh.assert_called()
    
    @pytest.mark.asyncio
    async def test_watch_error_message_change(self):
        """Test reactive response to error message changes."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view._mounted = True
            
            with patch.object(workout_view, 'refresh') as mock_refresh:
                # Trigger error message change
                error_msg = "Test error"
                workout_view.error_message = error_msg
                workout_view.watch_error_message(error_msg)
                
                # Should trigger refresh
                mock_refresh.assert_called()
    
    @pytest.mark.asyncio
    async def test_button_pressed_refresh_workouts(self):
        """Test refresh workouts button press."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            # Mock button and refresh method
            mock_button = MagicMock()
            mock_button.id = "refresh-workouts-btn"
            
            with patch.object(workout_view, 'refresh_workouts') as mock_refresh:
                event = Button.Pressed(mock_button)
                await workout_view.on_button_pressed(event)
                
                mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_button_pressed_sync_garmin(self):
        """Test sync Garmin button press."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            # Mock button and sync method
            mock_button = MagicMock()
            mock_button.id = "sync-garmin-btn"
            
            with patch.object(workout_view, 'sync_garmin_activities') as mock_sync:
                event = Button.Pressed(mock_button)
                await workout_view.on_button_pressed(event)
                
                mock_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_button_pressed_retry_loading(self):
        """Test retry loading button press."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.error_message = "Previous error"
            
            # Mock button and load_data method
            mock_button = MagicMock()
            mock_button.id = "retry-loading-btn"
            
            with patch.object(workout_view, 'load_data') as mock_load_data:
                event = Button.Pressed(mock_button)
                await workout_view.on_button_pressed(event)
                
                # Should clear error and reload
                assert workout_view.error_message is None
                mock_load_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_data_table_row_selection(self, mock_workouts):
        """Test row selection in workouts table."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            workout_view.workouts = mock_workouts
            
            # Mock table and event
            mock_table = MagicMock(spec=DataTable)
            mock_table.id = "workouts-table"
            
            # Mock event with row selection
            event = MagicMock()
            event.data_table = mock_table
            event.cursor_row = 0
            event.row_key = MagicMock()
            event.row_key.value = 0
            
            with patch.object(workout_view, 'show_workout_details') as mock_show_details:
                await workout_view.on_data_table_row_selected(event)
                
                # Should show details for first workout
                mock_show_details.assert_called_once_with(mock_workouts[0])
    
    @pytest.mark.asyncio
    async def test_integration_full_workflow(self, mock_workouts, mock_sync_status, mock_workout_analyses):
        """Test complete workflow integration."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            with patch('tui.views.workouts.AsyncSessionLocal') as mock_session_local, \
                 patch('tui.views.workouts.WorkoutService') as mock_service_class:
                
                # Setup mocks
                mock_db = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_db
                
                mock_service = AsyncMock()
                mock_service.get_workouts.return_value = mock_workouts
                mock_service.get_sync_status.return_value = mock_sync_status
                mock_service.get_workout_analyses.return_value = mock_workout_analyses
                mock_service.analyze_workout.return_value = {
                    "status": "success",
                    "message": "Analysis completed"
                }
                mock_service_class.return_value = mock_service
                
                # Mock UI methods
                with patch.object(workout_view, 'refresh'), \
                     patch.object(workout_view, 'populate_workouts_table'), \
                     patch.object(workout_view, 'update_sync_status'), \
                     patch.object(workout_view, 'query_one'), \
                     patch.object(workout_view, 'post_message'):
                    
                    # 1. Load initial data
                    result = await workout_view._load_workouts_data()
                    workouts, sync_status = result
                    workout_view.on_workouts_loaded((workouts, sync_status))
                    
                    # 2. Show workout details
                    await workout_view.show_workout_details(workouts[0])
                    
                    # 3. Analyze workout
                    await workout_view.analyze_selected_workout()
                    
                    # Verify full workflow executed
                    assert workout_view.workouts == mock_workouts
                    assert workout_view.sync_status == mock_sync_status
                    assert workout_view.selected_workout == mock_workouts[0]
                    assert workout_view.workout_analyses == mock_workout_analyses
                    assert workout_view.loading is False
                    assert workout_view.error_message is None

    @pytest.mark.asyncio
    async def test_compose_with_error(self):
        """Test the compose method when an error message is set."""
        class TestApp(App):
            def compose(self):
                workout_view = WorkoutView()
                workout_view.error_message = "A critical error occurred"
                workout_view.loading = False
                yield workout_view

        app = TestApp()
        async with app.run_test() as pilot:
            # Check for error display and retry button
            assert pilot.app.query_one(Static)
            assert "A critical error occurred" in str(pilot.app.query_one(Static).render())
            assert pilot.app.query_one("#retry-loading-btn", Button)
            # Ensure loading spinner is not present
            assert not pilot.app.query(LoadingSpinner)

    @pytest.mark.asyncio
    async def test_populate_workouts_table_with_malformed_data(self):
        """Test populating the table with malformed or missing data."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            malformed_workouts = [
                {
                    "id": 1,
                    "start_time": "Invalid-Date",
                    "duration_seconds": None,
                    "distance_m": "Not a number",
                    "avg_hr": None,
                    "avg_power": None
                }
            ]
            workout_view.workouts = malformed_workouts
            
            mock_table = MagicMock(spec=DataTable)
            
            with patch.object(workout_view, 'query_one', return_value=mock_table):
                await workout_view.populate_workouts_table()
                
                mock_table.clear.assert_called_once()
                assert mock_table.add_row.call_count == 1
                
                # Check that it fell back to default/graceful values
                call_args = mock_table.add_row.call_args[0]
                assert "Invalid-Date" in call_args[0]  # Date fallback
                assert "Unknown" in call_args[1]         # Activity type fallback
                assert "N/A" in call_args[2]             # Duration fallback
                assert "N/A" in call_args[3]             # Distance fallback

    @pytest.mark.asyncio
    async def test_button_pressed_check_sync(self):
        """Test check sync status button press."""
        async with App().run_test() as pilot:
            workout_view = WorkoutView()
            await pilot.app.mount(workout_view)
            mock_button = MagicMock()
            mock_button.id = "check-sync-btn"
            
            with patch.object(workout_view, 'check_sync_status') as mock_check_sync:
                event = Button.Pressed(mock_button)
                await workout_view.on_button_pressed(event)
                
                mock_check_sync.assert_called_once()

class TestWorkoutMetricsChart:
    """Test suite for the WorkoutMetricsChart widget."""

    def test_chart_creation_with_data(self):
        """Test ASCII chart generation with valid data."""
        metrics_data = [
            {"heart_rate": 150, "power": 200, "speed": 30},
            {"heart_rate": 160, "power": 220, "speed": 32},
        ]
        chart = WorkoutMetricsChart(metrics_data)
        
        # Simple check to ensure it produces a Static widget with content
        static_widget = chart.create_ascii_chart("Test", [10, 20])
        assert isinstance(static_widget, Static)
        assert "Min: 10.0" in str(static_widget.render())

    def test_chart_creation_no_data(self):
        """Test ASCII chart generation with no data."""
        chart = WorkoutMetricsChart([])
        static_widget = chart.create_ascii_chart("Test", [])
        assert "No data" in str(static_widget.render())

class TestWorkoutAnalysisPanel:
    """Test suite for the WorkoutAnalysisPanel widget."""

    def test_format_feedback(self):
        """Test the formatting of feedback data."""
        panel = WorkoutAnalysisPanel(workout_data={}, analyses=[])
        feedback_dict = {"effort_level": "high", "pacing": "good"}
        formatted = panel.format_feedback(feedback_dict)
        assert "Effort Level: high" in formatted
        assert "Pacing: good" in formatted

    def test_format_suggestions(self):
        """Test the formatting of suggestions data."""
        panel = WorkoutAnalysisPanel(workout_data={}, analyses=[])
        suggestions_dict = {"next_workout": "easy spin", "focus_on": "cadence"}
        formatted = panel.format_suggestions(suggestions_dict)
        assert "• Next Workout: easy spin" in formatted
        assert "• Focus On: cadence" in formatted

    @pytest.mark.asyncio
    async def test_compose_with_analysis(self, mock_workout_analyses):
        """Test panel composition with existing analysis."""
        async with App().run_test() as pilot:
            panel = WorkoutAnalysisPanel(workout_data={}, analyses=mock_workout_analyses)
            await pilot.app.mount(panel)
            # Check that it creates a Collapsible widget when analysis is present
            assert panel.query(Collapsible)

    @pytest.mark.asyncio
    async def test_compose_no_analysis(self):
        """Test panel composition without any analysis."""
        async with App().run_test() as pilot:
            panel = WorkoutAnalysisPanel(workout_data={}, analyses=[])
            await pilot.app.mount(panel)
            # Check that it shows a "No analysis" message and an "Analyze" button
            assert "No analysis available" in str(panel.query_one(Static).render())
            assert panel.query_one("#analyze-workout-btn", Button)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])