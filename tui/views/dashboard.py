"""
Dashboard view for AI Cycling Coach TUI.
Displays overview of recent workouts, plans, and key metrics.
"""
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, DataTable, LoadingIndicator
from textual.widget import Widget
from textual.reactive import reactive

from backend.app.database import AsyncSessionLocal
from tui.services.dashboard_service import DashboardService


class DashboardView(Widget):
    """Main dashboard view showing workout summary and stats."""
    
    # Reactive attributes to store data
    dashboard_data = reactive({})
    loading = reactive(True)
    
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
    
    .dashboard-column {
        width: 1fr;
        margin: 0 1;
    }
    
    .stats-container {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .stat-item {
        margin: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Static("AI Cycling Coach Dashboard", classes="view-title")
        
        if self.loading:
            yield LoadingIndicator(id="dashboard-loader")
        else:
            with ScrollableContainer():
                with Horizontal():
                    # Left column - Recent workouts
                    with Vertical(classes="dashboard-column"):
                        yield Static("Recent Workouts", classes="section-title")
                        workout_table = DataTable(id="recent-workouts")
                        workout_table.add_columns("Date", "Type", "Duration", "Distance", "Avg HR")
                        yield workout_table
                    
                    # Right column - Quick stats and current plan
                    with Vertical(classes="dashboard-column"):
                        # Weekly stats
                        with Container(classes="stats-container"):
                            yield Static("This Week", classes="section-title")
                            yield Static("Workouts: 0", id="week-workouts", classes="stat-item")
                            yield Static("Distance: 0 km", id="week-distance", classes="stat-item")
                            yield Static("Time: 0h 0m", id="week-time", classes="stat-item")
                        
                        # Active plan
                        with Container(classes="stats-container"):
                            yield Static("Current Plan", classes="section-title")
                            yield Static("No active plan", id="active-plan", classes="stat-item")
                        
                        # Sync status
                        with Container(classes="stats-container"):
                            yield Static("Garmin Sync", classes="section-title")
                            yield Static("Never synced", id="sync-status", classes="stat-item")
                            yield Static("", id="last-sync", classes="stat-item")
    
    async def on_mount(self) -> None:
        """Load dashboard data when mounted."""
        try:
            await self.load_dashboard_data()
        except Exception as e:
            self.log(f"Dashboard loading error: {e}", severity="error")
            # Show error state instead of loading indicator
            self.loading = False
            self.refresh()
    
    async def load_dashboard_data(self) -> None:
        """Load and display dashboard data."""
        try:
            async with AsyncSessionLocal() as db:
                dashboard_service = DashboardService(db)
                self.dashboard_data = await dashboard_service.get_dashboard_data()
                weekly_stats = await dashboard_service.get_weekly_stats()
                
                # Update the reactive data and stop loading
                self.loading = False
                self.refresh()
                
                # Populate the dashboard with data
                await self.populate_dashboard(weekly_stats)
                
        except Exception as e:
            self.log(f"Error loading dashboard data: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def populate_dashboard(self, weekly_stats: dict) -> None:
        """Populate dashboard widgets with loaded data."""
        try:
            # Update recent workouts table
            workout_table = self.query_one("#recent-workouts", DataTable)
            workout_table.clear()
            
            for workout in self.dashboard_data.get("recent_workouts", []):
                # Format datetime for display
                start_time = "N/A"
                if workout.get("start_time"):
                    try:
                        dt = datetime.fromisoformat(workout["start_time"].replace('Z', '+00:00'))
                        start_time = dt.strftime("%m/%d %H:%M")
                    except:
                        start_time = workout["start_time"][:10]  # Fallback to date only
                
                # Format duration
                duration = "N/A"
                if workout.get("duration_seconds"):
                    minutes = workout["duration_seconds"] // 60
                    duration = f"{minutes}min"
                
                # Format distance
                distance = "N/A"
                if workout.get("distance_m"):
                    distance = f"{workout['distance_m'] / 1000:.1f}km"
                
                # Format heart rate
                avg_hr = workout.get("avg_hr", "N/A")
                if avg_hr != "N/A":
                    avg_hr = f"{avg_hr}bpm"
                
                workout_table.add_row(
                    start_time,
                    workout.get("activity_type", "Unknown") or "Unknown",
                    duration,
                    distance,
                    str(avg_hr)
                )
            
            # Update weekly stats
            self.query_one("#week-workouts", Static).update(
                f"Workouts: {weekly_stats.get('workout_count', 0)}"
            )
            self.query_one("#week-distance", Static).update(
                f"Distance: {weekly_stats.get('total_distance_km', 0)}km"
            )
            self.query_one("#week-time", Static).update(
                f"Time: {weekly_stats.get('total_time_hours', 0):.1f}h"
            )
            
            # Update current plan
            current_plan = self.dashboard_data.get("current_plan")
            if current_plan:
                plan_text = f"Plan v{current_plan.get('version', 'N/A')}"
                if current_plan.get("created_at"):
                    try:
                        dt = datetime.fromisoformat(current_plan["created_at"].replace('Z', '+00:00'))
                        plan_text += f" ({dt.strftime('%m/%d/%Y')})"
                    except:
                        pass
                self.query_one("#active-plan", Static).update(plan_text)
            else:
                self.query_one("#active-plan", Static).update("No active plan")
            
            # Update sync status
            last_sync = self.dashboard_data.get("last_sync")
            if last_sync:
                status = last_sync.get("status", "unknown")
                activities_count = last_sync.get("activities_synced", 0)
                
                self.query_one("#sync-status", Static).update(
                    f"Status: {status.title()}"
                )
                
                if last_sync.get("last_sync_time"):
                    try:
                        dt = datetime.fromisoformat(last_sync["last_sync_time"].replace('Z', '+00:00'))
                        sync_time = dt.strftime("%m/%d %H:%M")
                        self.query_one("#last-sync", Static).update(
                            f"Last: {sync_time} ({activities_count} activities)"
                        )
                    except:
                        self.query_one("#last-sync", Static).update(
                            f"Activities: {activities_count}"
                        )
                else:
                    self.query_one("#last-sync", Static).update("")
            else:
                self.query_one("#sync-status", Static).update("Never synced")
                self.query_one("#last-sync", Static).update("")
                
        except Exception as e:
            self.log(f"Error populating dashboard: {e}", severity="error")
    
    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        # Trigger recomposition when loading state changes
        if hasattr(self, '_mounted') and self._mounted:
            self.refresh()