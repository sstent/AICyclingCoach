"""
Workout view for AI Cycling Coach TUI.
Displays workout list, analysis, and import functionality.
"""
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, DataTable, Button, Input, TextArea, LoadingIndicator,
    TabbedContent, TabPane, Label, ProgressBar, Collapsible
)
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from typing import List, Dict, Optional

from backend.app.database import AsyncSessionLocal
from tui.services.workout_service import WorkoutService


class WorkoutMetricsChart(Widget):
    """ASCII-based workout metrics visualization."""
    
    def __init__(self, metrics_data: List[Dict]):
        super().__init__()
        self.metrics_data = metrics_data
    
    def compose(self) -> ComposeResult:
        """Create metrics chart view."""
        if not self.metrics_data:
            yield Static("No metrics data available")
            return
        
        # Create simple ASCII charts for key metrics
        yield Label("Workout Metrics Overview")
        
        # Heart Rate Chart (simple bar representation)
        hr_values = [m.get("heart_rate", 0) for m in self.metrics_data if m.get("heart_rate")]
        if hr_values:
            yield self.create_ascii_chart("Heart Rate (BPM)", hr_values, max_width=50)
        
        # Power Chart
        power_values = [m.get("power", 0) for m in self.metrics_data if m.get("power")]
        if power_values:
            yield self.create_ascii_chart("Power (W)", power_values, max_width=50)
        
        # Speed Chart
        speed_values = [m.get("speed", 0) for m in self.metrics_data if m.get("speed")]
        if speed_values:
            yield self.create_ascii_chart("Speed (km/h)", speed_values, max_width=50)
    
    def create_ascii_chart(self, title: str, values: List[float], max_width: int = 50) -> Static:
        """Create a simple ASCII bar chart."""
        if not values:
            return Static(f"{title}: No data")
        
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        
        # Create a simple representation
        chart_text = f"{title}:\n"
        chart_text += f"Min: {min_val:.1f} | Max: {max_val:.1f} | Avg: {avg_val:.1f}\n"
        
        # Simple histogram representation
        if max_val > min_val:
            normalized = [(v - min_val) / (max_val - min_val) for v in values[:20]]  # Take first 20 points
            chart_text += "["
            for norm_val in normalized:
                bar_length = int(norm_val * 10)
                chart_text += "█" * bar_length + "░" * (10 - bar_length) + " "
            chart_text += "]\n"
        
        return Static(chart_text)


class WorkoutAnalysisPanel(Widget):
    """Panel showing AI analysis of a workout."""
    
    def __init__(self, workout_data: Dict, analyses: List[Dict]):
        super().__init__()
        self.workout_data = workout_data
        self.analyses = analyses
    
    def compose(self) -> ComposeResult:
        """Create analysis panel layout."""
        yield Label("AI Analysis")
        
        if not self.analyses:
            yield Static("No analysis available for this workout.")
            yield Button("Analyze Workout", id="analyze-workout-btn", variant="primary")
            return
        
        # Show existing analyses
        with ScrollableContainer():
            for i, analysis in enumerate(self.analyses):
                with Collapsible(title=f"Analysis {i+1} - {analysis.get('analysis_type', 'Unknown')}"):
                    
                    # Feedback section
                    feedback = analysis.get('feedback', {})
                    if feedback:
                        yield Label("Feedback:")
                        feedback_text = self.format_feedback(feedback)
                        yield TextArea(feedback_text, read_only=True)
                    
                    # Suggestions section
                    suggestions = analysis.get('suggestions', {})
                    if suggestions:
                        yield Label("Suggestions:")
                        suggestions_text = self.format_suggestions(suggestions)
                        yield TextArea(suggestions_text, read_only=True)
                    
                    # Analysis metadata
                    created_at = analysis.get('created_at', '')
                    approved = analysis.get('approved', False)
                    
                    with Horizontal():
                        yield Static(f"Created: {created_at[:19] if created_at else 'Unknown'}")
                        if not approved:
                            yield Button("Approve", id=f"approve-analysis-{analysis['id']}", variant="success")
        
        # Button to run new analysis
        yield Button("Run New Analysis", id="analyze-workout-btn", variant="primary")
    
    def format_feedback(self, feedback: Dict) -> str:
        """Format feedback dictionary as readable text."""
        if isinstance(feedback, str):
            return feedback
        
        formatted = []
        for key, value in feedback.items():
            formatted.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)
    
    def format_suggestions(self, suggestions: Dict) -> str:
        """Format suggestions dictionary as readable text."""
        if isinstance(suggestions, str):
            return suggestions
        
        formatted = []
        for key, value in suggestions.items():
            formatted.append(f"• {key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)


class WorkoutView(Widget):
    """Workout management view."""
    
    # Reactive attributes
    workouts = reactive([])
    selected_workout = reactive(None)
    workout_analyses = reactive([])
    loading = reactive(True)
    sync_status = reactive({})
    
    DEFAULT_CSS = """
    .view-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    .workout-column {
        width: 1fr;
        margin: 0 1;
    }
    
    .sync-container {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .button-row {
        margin: 1 0;
    }
    
    .metrics-container {
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
    }
    """
    
    class WorkoutSelected(Message):
        """Message sent when a workout is selected."""
        def __init__(self, workout_id: int):
            super().__init__()
            self.workout_id = workout_id
    
    class AnalysisRequested(Message):
        """Message sent when analysis is requested."""
        def __init__(self, workout_id: int):
            super().__init__()
            self.workout_id = workout_id
    
    def compose(self) -> ComposeResult:
        """Create workout view layout."""
        yield Static("Workout Management", classes="view-title")
        
        if self.loading:
            yield LoadingIndicator(id="workouts-loader")
        else:
            with TabbedContent():
                with TabPane("Workout List", id="workout-list-tab"):
                    yield self.compose_workout_list()
                
                if self.selected_workout:
                    with TabPane("Workout Details", id="workout-details-tab"):
                        yield self.compose_workout_details()
    
    def compose_workout_list(self) -> ComposeResult:
        """Create workout list view."""
        with Container():
            # Sync section
            with Container(classes="sync-container"):
                yield Static("Garmin Sync", classes="section-title")
                yield Static("Status: Unknown", id="sync-status-text")
                
                with Horizontal(classes="button-row"):
                    yield Button("Sync Now", id="sync-garmin-btn", variant="primary")
                    yield Button("Check Status", id="check-sync-btn")
            
            # Workout filters and actions
            with Horizontal(classes="button-row"):
                yield Button("Refresh", id="refresh-workouts-btn")
                yield Input(placeholder="Filter workouts...", id="workout-filter")
                yield Button("Filter", id="filter-workouts-btn")
            
            # Workouts table
            workouts_table = DataTable(id="workouts-table")
            workouts_table.add_columns("Date", "Type", "Duration", "Distance", "Avg HR", "Avg Power", "Actions")
            yield workouts_table
    
    def compose_workout_details(self) -> ComposeResult:
        """Create workout details view."""
        workout = self.selected_workout
        if not workout:
            yield Static("No workout selected")
            return
        
        with ScrollableContainer():
            # Workout summary
            yield Static("Workout Summary", classes="section-title")
            yield self.create_workout_summary(workout)
            
            # Metrics visualization
            if workout.get('metrics'):
                with Container(classes="metrics-container"):
                    yield WorkoutMetricsChart(workout['metrics'])
            
            # Analysis section
            yield Static("AI Analysis", classes="section-title")
            yield WorkoutAnalysisPanel(workout, self.workout_analyses)
    
    def create_workout_summary(self, workout: Dict) -> Container:
        """Create workout summary display."""
        container = Container()
        
        # Basic workout info
        start_time = "Unknown"
        if workout.get("start_time"):
            try:
                dt = datetime.fromisoformat(workout["start_time"].replace('Z', '+00:00'))
                start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                start_time = workout["start_time"]
        
        duration = "Unknown"
        if workout.get("duration_seconds"):
            minutes = workout["duration_seconds"] // 60
            seconds = workout["duration_seconds"] % 60
            duration = f"{minutes}:{seconds:02d}"
        
        distance = "Unknown"
        if workout.get("distance_m"):
            distance = f"{workout['distance_m'] / 1000:.2f} km"
        
        summary_text = f"""
Activity Type: {workout.get('activity_type', 'Unknown')}
Start Time: {start_time}
Duration: {duration}
Distance: {distance}
Average Heart Rate: {workout.get('avg_hr', 'N/A')} BPM
Max Heart Rate: {workout.get('max_hr', 'N/A')} BPM
Average Power: {workout.get('avg_power', 'N/A')} W
Max Power: {workout.get('max_power', 'N/A')} W
Average Cadence: {workout.get('avg_cadence', 'N/A')} RPM
Elevation Gain: {workout.get('elevation_gain_m', 'N/A')} m
        """.strip()
        
        return Static(summary_text)
    
    async def on_mount(self) -> None:
        """Load workout data when mounted."""
        try:
            await self.load_workouts_data()
        except Exception as e:
            self.log(f"Workouts loading error: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def load_workouts_data(self) -> None:
        """Load workouts and sync status."""
        try:
            async with AsyncSessionLocal() as db:
                workout_service = WorkoutService(db)
                
                # Load workouts and sync status
                self.workouts = await workout_service.get_workouts(limit=50)
                self.sync_status = await workout_service.get_sync_status()
                
                # Update loading state
                self.loading = False
                self.refresh()
                
                # Populate UI elements
                await self.populate_workouts_table()
                await self.update_sync_status()
                
        except Exception as e:
            self.log(f"Error loading workouts data: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def populate_workouts_table(self) -> None:
        """Populate the workouts table."""
        try:
            workouts_table = self.query_one("#workouts-table", DataTable)
            workouts_table.clear()
            
            for workout in self.workouts:
                # Format date
                date_str = "Unknown"
                if workout.get("start_time"):
                    try:
                        dt = datetime.fromisoformat(workout["start_time"].replace('Z', '+00:00'))
                        date_str = dt.strftime("%m/%d %H:%M")
                    except:
                        date_str = workout["start_time"][:10]
                
                # Format duration
                duration_str = "N/A"
                if workout.get("duration_seconds"):
                    minutes = workout["duration_seconds"] // 60
                    duration_str = f"{minutes}min"
                
                # Format distance
                distance_str = "N/A"
                if workout.get("distance_m"):
                    distance_str = f"{workout['distance_m'] / 1000:.1f}km"
                
                workouts_table.add_row(
                    date_str,
                    workout.get("activity_type", "Unknown") or "Unknown",
                    duration_str,
                    distance_str,
                    f"{workout.get('avg_hr', 'N/A')} BPM" if workout.get('avg_hr') else "N/A",
                    f"{workout.get('avg_power', 'N/A')} W" if workout.get('avg_power') else "N/A",
                    "View | Analyze"
                )
                
        except Exception as e:
            self.log(f"Error populating workouts table: {e}", severity="error")
    
    async def update_sync_status(self) -> None:
        """Update sync status display."""
        try:
            status_text = self.query_one("#sync-status-text", Static)
            
            status = self.sync_status.get("status", "unknown")
            last_sync = self.sync_status.get("last_sync_time", "Never")
            activities_count = self.sync_status.get("activities_synced", 0)
            
            if last_sync and last_sync != "Never":
                try:
                    dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                    last_sync = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            status_display = f"Status: {status.title()} | Last Sync: {last_sync} | Activities: {activities_count}"
            
            if self.sync_status.get("error_message"):
                status_display += f" | Error: {self.sync_status['error_message']}"
            
            status_text.update(status_display)
            
        except Exception as e:
            self.log(f"Error updating sync status: {e}", severity="error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        try:
            if event.button.id == "refresh-workouts-btn":
                await self.refresh_workouts()
            elif event.button.id == "sync-garmin-btn":
                await self.sync_garmin_activities()
            elif event.button.id == "check-sync-btn":
                await self.check_sync_status()
            elif event.button.id == "analyze-workout-btn":
                await self.analyze_selected_workout()
            elif event.button.id.startswith("approve-analysis-"):
                analysis_id = int(event.button.id.split("-")[-1])
                await self.approve_analysis(analysis_id)
                
        except Exception as e:
            self.log(f"Button press error: {e}", severity="error")
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in workouts table."""
        try:
            if event.data_table.id == "workouts-table":
                # Get workout index from row selection
                row_index = event.row_key.value if hasattr(event.row_key, 'value') else event.cursor_row
                
                if 0 <= row_index < len(self.workouts):
                    selected_workout = self.workouts[row_index]
                    await self.show_workout_details(selected_workout)
                    
        except Exception as e:
            self.log(f"Row selection error: {e}", severity="error")
    
    async def show_workout_details(self, workout: Dict) -> None:
        """Show detailed view of a workout."""
        try:
            self.selected_workout = workout
            
            # Load analyses for this workout
            async with AsyncSessionLocal() as db:
                workout_service = WorkoutService(db)
                self.workout_analyses = await workout_service.get_workout_analyses(workout["id"])
            
            # Refresh to show the details tab
            self.refresh()
            
            # Switch to details tab
            tabs = self.query_one(TabbedContent)
            tabs.active = "workout-details-tab"
            
            # Post message that workout was selected
            self.post_message(self.WorkoutSelected(workout["id"]))
            
        except Exception as e:
            self.log(f"Error showing workout details: {e}", severity="error")
    
    async def refresh_workouts(self) -> None:
        """Refresh the workouts list."""
        self.loading = True
        self.refresh()
        await self.load_workouts_data()
    
    async def sync_garmin_activities(self) -> None:
        """Sync with Garmin Connect."""
        try:
            self.log("Starting Garmin sync...", severity="info")
            
            async with AsyncSessionLocal() as db:
                workout_service = WorkoutService(db)
                result = await workout_service.sync_garmin_activities(days_back=14)
                
                if result["status"] == "success":
                    self.log(f"Sync completed: {result['activities_synced']} activities", severity="info")
                else:
                    self.log(f"Sync failed: {result['message']}", severity="error")
                
                # Refresh sync status and workouts
                await self.check_sync_status()
                await self.refresh_workouts()
                
        except Exception as e:
            self.log(f"Error syncing Garmin activities: {e}", severity="error")
    
    async def check_sync_status(self) -> None:
        """Check current sync status."""
        try:
            async with AsyncSessionLocal() as db:
                workout_service = WorkoutService(db)
                self.sync_status = await workout_service.get_sync_status()
                await self.update_sync_status()
                
        except Exception as e:
            self.log(f"Error checking sync status: {e}", severity="error")
    
    async def analyze_selected_workout(self) -> None:
        """Analyze the currently selected workout."""
        if not self.selected_workout:
            self.log("No workout selected for analysis", severity="warning")
            return
        
        try:
            self.log("Starting workout analysis...", severity="info")
            
            async with AsyncSessionLocal() as db:
                workout_service = WorkoutService(db)
                result = await workout_service.analyze_workout(self.selected_workout["id"])
                
                self.log(f"Analysis completed: {result['message']}", severity="info")
                
                # Reload analyses for this workout
                self.workout_analyses = await workout_service.get_workout_analyses(self.selected_workout["id"])
                self.refresh()
                
                # Post message that analysis was requested
                self.post_message(self.AnalysisRequested(self.selected_workout["id"]))
                
        except Exception as e:
            self.log(f"Error analyzing workout: {e}", severity="error")
    
    async def approve_analysis(self, analysis_id: int) -> None:
        """Approve a workout analysis."""
        try:
            async with AsyncSessionLocal() as db:
                workout_service = WorkoutService(db)
                result = await workout_service.approve_analysis(analysis_id)
                
                self.log(f"Analysis approved: {result['message']}", severity="info")
                
                # Reload analyses to update approval status
                if self.selected_workout:
                    self.workout_analyses = await workout_service.get_workout_analyses(self.selected_workout["id"])
                    self.refresh()
                
        except Exception as e:
            self.log(f"Error approving analysis: {e}", severity="error")
    
    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        if hasattr(self, '_mounted') and self._mounted:
            self.refresh()