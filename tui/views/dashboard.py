"""
Fixed Dashboard view for AI Cycling Coach TUI.
Displays overview of recent workouts, plans, and key metrics.
"""
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, DataTable, LoadingIndicator
from textual.widget import Widget
from textual.reactive import reactive
from textual import work

try:
    from backend.app.database import AsyncSessionLocal
    from tui.services.dashboard_service import DashboardService
except ImportError as e:
    raise ImportError(f"Critical import error: {e}. Check service dependencies.")


class DashboardView(Widget):
    """Main dashboard view showing workout summary and stats."""
    
    # Reactive attributes to store data - set init=False to prevent immediate refresh
    dashboard_data = reactive({}, init=False)
    loading = reactive(True, init=False)
    error_message = reactive("", init=False)
    
    # Add unique identifier for debugging
    debug_id = reactive("", init=False)
    
    # Track if we've mounted to prevent refresh before mount
    _mounted = False
    
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
    
    .error-container {
        border: solid $error;
        padding: 1;
        margin: 1 0;
        color: $error;
    }
    .error-title {
        text-style: bold;
        margin-bottom: 1;
    }
    .error-subtitle {
        text-style: underline;
        margin: 1 0 0 1;
    }
    .error-item {
        margin: 0 0 0 2;
    }
    .error-spacer {
        height: 1;
    }
    .error-action {
        margin-top: 1;
        text-style: bold;
    }
    
    .loading-overlay {
        align: right top;
        offset: 1 1;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        self.log(f"[DashboardView] compose called | debug_id={self.debug_id} | loading={self.loading} | error={self.error_message}")
        yield Static("AI Cycling Coach Dashboard", classes="view-title")
        # Always show the structure - use conditional content
        if self.error_message:
            with Container(classes="error-container"):
                yield Static(f"Error: {self.error_message}", classes="error-title")
                yield Static("Possible causes:", classes="error-subtitle")
                yield Static("- Database connection issue", classes="error-item")
                yield Static("- Service dependency missing", classes="error-item")
                yield Static("- Invalid configuration", classes="error-item")
                yield Static("", classes="error-spacer")
                yield Static("Troubleshooting steps:", classes="error-subtitle")
                yield Static("- Check database configuration", classes="error-item")
                yield Static("- Verify backend services are running", classes="error-item")
                yield Static("- View logs for details", classes="error-item")
                yield Static("", classes="error-spacer")
                yield Static("Click Refresh to try again", classes="error-action")
        elif self.loading and not self.dashboard_data:
            # Initial load - full screen loader
            yield LoadingIndicator(id="dashboard-loader")
        else:
            # Show content with optional refresh indicator
            if self.loading:
                with Container(classes="loading-overlay"):
                    yield LoadingIndicator()
                    yield Static("Refreshing...")
            yield from self._compose_dashboard_content()
    
    
    def _compose_dashboard_content(self) -> ComposeResult:
        """Compose the main dashboard content."""
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
def on_mount(self) -> None:
    """Load dashboard data when mounted."""
    # Generate unique debug ID for this instance
    import uuid
    self.debug_id = str(uuid.uuid4())[:8]
    self.log(f"[DashboardView] on_mount called | debug_id={self.debug_id}")
    self._mounted = True
    
    # Use @work decorator for async operations
    self.load_dashboard_data()

    
    @work(exclusive=True)
    async def load_dashboard_data(self) -> None:
        """Load and display dashboard data."""
        self.log(f"[DashboardView] load_dashboard_data started | debug_id={self.debug_id}")
        try:
            self.loading = True
            self.error_message = ""
            
            try:
                # Explicitly check imports again in case of lazy loading
                from backend.app.database import AsyncSessionLocal
                from tui.services.dashboard_service import DashboardService
            except ImportError as e:
                self.log(f"[DashboardView] Import error in load_dashboard_data: {e} | debug_id={self.debug_id}", severity="error")
                self.error_message = f"Service dependency error: {e}"
                self.loading = False
                return
                
            async with AsyncSessionLocal() as db:
                self.log(f"[DashboardView] Database session opened | debug_id={self.debug_id}")
                dashboard_service = DashboardService(db)
                
                # Log service initialization
                self.log(f"[DashboardView] DashboardService created | debug_id={self.debug_id}")
                
                dashboard_data = await dashboard_service.get_dashboard_data()
                weekly_stats = await dashboard_service.get_weekly_stats()
                
                # Log data retrieval
                self.log(f"[DashboardView] Data retrieved | debug_id={self.debug_id} | workouts={len(dashboard_data.get('recent_workouts', []))} | weekly_stats={weekly_stats}")
                
                # Update reactive data
                self.dashboard_data = dashboard_data
                self.loading = False
                
                # Force recomposition after data is loaded
                await self.call_after_refresh(self.populate_dashboard, weekly_stats)
                
        except Exception as e:
            self.log(f"[DashboardView] Error loading dashboard data: {e} | debug_id={self.debug_id}", severity="error")
            self.error_message = str(e)
            self.loading = False
        finally:
            self.log(f"[DashboardView] load_dashboard_data completed | debug_id={self.debug_id}")
    
    async def populate_dashboard(self, weekly_stats: dict) -> None:
        """Populate dashboard widgets with loaded data."""
        self.log(f"[DashboardView] populate_dashboard started | debug_id={self.debug_id}")
        if self.loading or self.error_message:
            self.log(f"[DashboardView] populate_dashboard skipped - loading={self.loading}, error={self.error_message} | debug_id={self.debug_id}")
            return
            
        try:
            # Update recent workouts table
            try:
                self.log(f"[DashboardView] Updating workout table | debug_id={self.debug_id}")
                workout_table = self.query_one("#recent-workouts", DataTable)
                workout_table.clear()
                
                for workout in self.dashboard_data.get("recent_workouts", []):
                    # Format datetime for display
                    start_time = "N/A"
                    if workout.get("start_time"):
                        try:
                            dt = datetime.fromisoformat(workout["start_time"].replace('Z', '+00:00'))
                            start_time = dt.strftime("%m/%d %H:%M")
                        except Exception:
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
                self.log(f"[DashboardView] Workout table updated with {len(self.dashboard_data.get('recent_workouts', []))} rows | debug_id={self.debug_id}")
            except Exception as e:
                self.log(f"[DashboardView] Error updating workout table: {e} | debug_id={self.debug_id}", severity="error")
            
            # Update weekly stats
            try:
                self.log(f"[DashboardView] Updating weekly stats | debug_id={self.debug_id}")
                self.query_one("#week-workouts", Static).update(
                    f"Workouts: {weekly_stats.get('workout_count', 0)}"
                )
                self.query_one("#week-distance", Static).update(
                    f"Distance: {weekly_stats.get('total_distance_km', 0)}km"
                )
                self.query_one("#week-time", Static).update(
                    f"Time: {weekly_stats.get('total_time_hours', 0):.1f}h"
                )
                self.log(f"[DashboardView] Weekly stats updated | debug_id={self.debug_id}")
            except Exception as e:
                self.log(f"[DashboardView] Error updating stats: {e} | debug_id={self.debug_id}", severity="error")
            
            # Update current plan
            try:
                self.log(f"[DashboardView] Updating current plan | debug_id={self.debug_id}")
                current_plan = self.dashboard_data.get("current_plan")
                if current_plan:
                    plan_text = f"Plan v{current_plan.get('version', 'N/A')}"
                    if current_plan.get("created_at"):
                        try:
                            dt = datetime.fromisoformat(current_plan["created_at"].replace('Z', '+00:00'))
                            plan_text += f" ({dt.strftime('%m/%d/%Y')})"
                        except Exception:
                            pass
                    self.query_one("#active-plan", Static).update(plan_text)
                else:
                    self.query_one("#active-plan", Static).update("No active plan")
                self.log(f"[DashboardView] Current plan updated | debug_id={self.debug_id}")
            except Exception as e:
                self.log(f"[DashboardView] Error updating plan: {e} | debug_id={self.debug_id}", severity="error")
            
            # Update sync status
            try:
                self.log(f"[DashboardView] Updating sync status | debug_id={self.debug_id}")
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
                        except Exception:
                            self.query_one("#last-sync", Static).update(
                                f"Activities: {activities_count}"
                            )
                    else:
                        self.query_one("#last-sync", Static).update("")
                else:
                    self.query_one("#sync-status", Static).update("Never synced")
                    self.query_one("#last-sync", Static).update("")
                self.log(f"[DashboardView] Sync status updated | debug_id={self.debug_id}")
            except Exception as e:
                self.log(f"[DashboardView] Error updating sync status: {e} | debug_id={self.debug_id}", severity="error")
                
        except Exception as e:
            self.log(f"[DashboardView] Error populating dashboard: {e} | debug_id={self.debug_id}", severity="error")
            self.error_message = f"Failed to populate dashboard: {e}"
        finally:
            self.log(f"[DashboardView] populate_dashboard completed | debug_id={self.debug_id}")
    
    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        self.log(f"[DashboardView] watch_loading: loading={loading} | debug_id={self.debug_id}")
        # Force recomposition when loading state changes
        if self.is_mounted:
            self.call_after_refresh(self._refresh_view)
    
    def watch_error_message(self, error_message: str) -> None:
        """React to error message changes."""
        self.log(f"[DashboardView] watch_error_message: error_message={error_message} | debug_id={self.debug_id}")
        if self.is_mounted:
            self.call_after_refresh(self._refresh_view)
    
    async def _refresh_view(self) -> None:
        """Force view refresh by recomposing."""
        self.log(f"[DashboardView] _refresh_view called | debug_id={self.debug_id}")
        self.refresh(layout=True)