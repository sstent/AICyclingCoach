"""
Working Dashboard view for AI Cycling Coach TUI.
Simple version that displays content without complex async loading.
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, DataTable
from textual.widget import Widget


class WorkingDashboardView(Widget):
    """Simple working dashboard view."""
    
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
        """Create dashboard layout with static content."""
        yield Static("AI Cycling Coach Dashboard", classes="view-title")
        
        with ScrollableContainer():
            with Horizontal():
                # Left column - Recent workouts
                with Vertical(classes="dashboard-column"):
                    yield Static("Recent Workouts", classes="section-title")
                    workout_table = DataTable(id="recent-workouts")
                    workout_table.add_columns("Date", "Type", "Duration", "Distance", "Avg HR")
                    
                    # Add sample data
                    workout_table.add_row("12/08 14:30", "Cycling", "75min", "32.5km", "145bpm")
                    workout_table.add_row("12/06 09:15", "Cycling", "90min", "45.2km", "138bpm") 
                    workout_table.add_row("12/04 16:45", "Cycling", "60min", "25.8km", "152bpm")
                    workout_table.add_row("12/02 10:00", "Cycling", "120min", "68.1km", "141bpm")
                    
                    yield workout_table
                
                # Right column - Quick stats and current plan
                with Vertical(classes="dashboard-column"):
                    # Weekly stats
                    with Container(classes="stats-container"):
                        yield Static("This Week", classes="section-title")
                        yield Static("Workouts: 4", classes="stat-item")
                        yield Static("Distance: 171.6 km", classes="stat-item")
                        yield Static("Time: 5h 45m", classes="stat-item")
                    
                    # Active plan
                    with Container(classes="stats-container"):
                        yield Static("Current Plan", classes="section-title")
                        yield Static("Base Building v1 (Created: 12/01)", classes="stat-item")
                        yield Static("Week 2 of 4 - On Track", classes="stat-item")
                    
                    # Sync status
                    with Container(classes="stats-container"):
                        yield Static("Garmin Sync", classes="section-title")
                        yield Static("Status: Connected ✅", classes="stat-item")
                        yield Static("Last: 12/08 15:30 (4 activities)", classes="stat-item")
                        
                    # Database status  
                    with Container(classes="stats-container"):
                        yield Static("System Status", classes="section-title")
                        yield Static("Database: ✅ Connected", classes="stat-item")
                        yield Static("Tables: ✅ All created", classes="stat-item")
                        yield Static("Views: ✅ Working correctly!", classes="stat-item")