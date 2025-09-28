#!/usr/bin/env python3
"""
AI Cycling Coach - CLI TUI Application
Entry point for the terminal-based cycling training coach.
"""
import argparse
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Optional
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, DataTable,
    Placeholder, TabbedContent, TabPane
)
from textual.logging import TextualHandler
from textual import on

from backend.app.config import settings
from backend.app.database import init_db
# Use working dashboard with static content
from tui.views.dashboard_working import WorkingDashboardView as DashboardView
from tui.views.workouts import WorkoutView
from tui.views.plans import PlanView
from tui.views.rules import RuleView
from tui.views.routes import RouteView
from backend.app.database import AsyncSessionLocal
from tui.services.workout_service import WorkoutService


class CyclingCoachApp(App):
    """Main TUI application for AI Cycling Coach."""
    
    CSS = """
    .title {
        text-align: center;
        color: $accent;
        text-style: bold;
        padding: 1;
    }
    
    .sidebar {
        width: 20;
        background: $surface;
    }
    
    .main-content {
        background: $background;
    }
    
    .nav-button {
        width: 100%;
        height: 3;
        margin: 1 0;
    }
    
    .nav-button.-active {
        background: $accent;
        color: $text;
    }

    TabbedContent {
        height: 1fr;
        width: 1fr;
    }

    TabPane {
        height: 1fr;
        width: 1fr;
    }
    """
    
    TITLE = "AI Cycling Coach"
    SUB_TITLE = "Terminal Training Interface"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view = "dashboard"
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for the TUI application."""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Set up logger
        logger = logging.getLogger("cycling_coach")
        logger.setLevel(logging.INFO)
        
        # Add Textual handler for TUI-compatible logging
        textual_handler = TextualHandler()
        logger.addHandler(textual_handler)
        
        # Add file handler
        # Add file handler for rotating logs
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "app.log", maxBytes=1024 * 1024 * 5, backupCount=5  # 5MB
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)
    
    def compose(self) -> ComposeResult:
        """Create the main application layout."""
        sys.stdout.write("CyclingCoachApp.compose: START\n")
        yield Header()
        
        with Container():
            with Horizontal():
                # Sidebar navigation
                with Vertical(classes="sidebar"):
                    yield Static("Navigation", classes="title")
                    yield Button("Dashboard", id="nav-dashboard", classes="nav-button")
                    yield Button("Workouts", id="nav-workouts", classes="nav-button")
                    yield Button("Plans", id="nav-plans", classes="nav-button")
                    yield Button("Rules", id="nav-rules", classes="nav-button")
                    yield Button("Routes", id="nav-routes", classes="nav-button")
                    yield Button("Settings", id="nav-settings", classes="nav-button")
                    yield Button("Quit", id="nav-quit", classes="nav-button")
                
                # Main content area
                with Container(classes="main-content"):
                    with TabbedContent(id="main-tabs"):
                        with TabPane("Dashboard", id="dashboard-tab"):
                            yield DashboardView(id="dashboard-view")
                        
                        with TabPane("Workouts", id="workouts-tab"):
                            yield WorkoutView(id="workout-view")
                        
                        with TabPane("Plans", id="plans-tab"):
                            yield PlanView(id="plan-view")
                        
                        with TabPane("Rules", id="rules-tab"):
                            yield RuleView(id="rule-view")
                        
                        with TabPane("Routes", id="routes-tab"):
                            yield RouteView(id="route-view")
        
        yield Footer()
        sys.stdout.write("CyclingCoachApp.compose: END\n")

    async def on_mount(self) -> None:
        """Initialize the application when mounted."""
        sys.stdout.write("CyclingCoachApp.on_mount: START\n")
        # Set initial active navigation and tab
        self.query_one("#nav-dashboard").add_class("-active")
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs:
            tabs.active = "dashboard-tab"
            sys.stdout.write("CyclingCoachApp.on_mount: Activated dashboard-tab\n")
        sys.stdout.write("CyclingCoachApp.on_mount: END\n")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button presses."""
        button_id = event.button.id
        
        if button_id == "nav-quit":
            self.exit()
            return
        
        # Handle navigation
        nav_mapping = {
            "nav-dashboard": "dashboard-tab",
            "nav-workouts": "workouts-tab", 
            "nav-plans": "plans-tab",
            "nav-rules": "rules-tab",
            "nav-routes": "routes-tab",
        }
        
        if button_id in nav_mapping:
            # Update active tab
            tabs = self.query_one("#main-tabs")
            tabs.active = nav_mapping[button_id]
            
            # Update navigation button styles
            for nav_button in self.query("Button"):
                nav_button.remove_class("-active")
            event.button.add_class("-active")

    @on(TabbedContent.TabActivated)
    async def on_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        sys.stdout.write(f"CyclingCoachApp.on_tab_activated: Tab {event.pane.id} activated\n")
        """Handle tab activation to load data for the active tab."""
        if event.pane.id == "workouts-tab":
            workout_view = self.query_one("#workout-view", WorkoutView)
            sys.stdout.write("CyclingCoachApp.on_tab_activated: Calling workout_view.load_data()\n")
            workout_view.load_data()

    def action_quit(self) -> None:
        self.exit()

async def init_db_async():
    try:
        await init_db()
        sys.stdout.write("Database initialized successfully\n")
    except Exception as e:
        sys.stdout.write(f"Database initialization failed: {e}\n")
        sys.exit(1)

async def list_workouts_cli():
    """Display workouts in CLI format without starting TUI."""
    try:
        # Initialize database
        await init_db_async()

        # Get workouts using WorkoutService
        async with AsyncSessionLocal() as db:
            workout_service = WorkoutService(db)
            workouts = await workout_service.get_workouts(limit=50)

        if not workouts:
            print("No workouts found.")
            return

        # Print header
        print("AI Cycling Coach - Workouts")
        print("=" * 80)
        print(f"{'Date':<12} {'Type':<15} {'Duration':<10} {'Distance':<10} {'Avg HR':<8} {'Avg Power':<10}")
        print("-" * 80)

        # Print each workout
        for workout in workouts:
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

            # Format heart rate
            hr_str = "N/A"
            if workout.get("avg_hr"):
                hr_str = f"{workout['avg_hr']} BPM"

            # Format power
            power_str = "N/A"
            if workout.get("avg_power"):
                power_str = f"{workout['avg_power']} W"

            print(f"{date_str:<12} {workout.get('activity_type', 'Unknown')[:14]:<15} {duration_str:<10} {distance_str:<10} {hr_str:<8} {power_str:<10}")

        print(f"\nTotal workouts: {len(workouts)}")

    except Exception as e:
        print(f"Error listing workouts: {e}")
        sys.exit(1)

def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="AI Cycling Coach - Terminal Training Interface")
    parser.add_argument("--list-workouts", action="store_true",
                       help="List all workouts in CLI format and exit")

    args = parser.parse_args()

    # Handle CLI commands that don't need TUI
    if args.list_workouts:
        asyncio.run(list_workouts_cli())
        return

    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "gpx").mkdir(exist_ok=True)
    (data_dir / "sessions").mkdir(exist_ok=True)

    # Initialize database BEFORE starting the app
    asyncio.run(init_db_async())

    # Run the TUI application
    sys.stdout.write("main(): Initializing CyclingCoachApp\n")
    app = CyclingCoachApp()
    sys.stdout.write("main(): CyclingCoachApp initialized. Running app.run()\n")
    app.run()
    sys.stdout.write("main(): app.run() finished.\n")


if __name__ == "__main__":
    main()
