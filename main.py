#!/usr/bin/env python3
"""
AI Cycling Coach - CLI TUI Application
Entry point for the terminal-based cycling training coach.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, DataTable, 
    Placeholder, TabbedContent, TabPane
)
from textual.logging import TextualHandler

from backend.app.config import settings
from backend.app.database import init_db
from tui.views.dashboard import DashboardView
from tui.views.workouts import WorkoutView
from tui.views.plans import PlanView
from tui.views.rules import RuleView
from tui.views.routes import RouteView


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
        file_handler = logging.FileHandler(logs_dir / "app.log")
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
    
    def compose(self) -> ComposeResult:
        """Create the main application layout."""
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
    
    async def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Initialize database
        try:
            await init_db()
            self.log("Database initialized successfully")
        except Exception as e:
            self.log(f"Database initialization failed: {e}", severity="error")
            self.exit(1)
        
        # Set initial active navigation
        self.query_one("#nav-dashboard").add_class("-active")
    
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
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


async def main():
    """Main entry point for the CLI application."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "gpx").mkdir(exist_ok=True)
    (data_dir / "sessions").mkdir(exist_ok=True)
    
    # Run the TUI application
    app = CyclingCoachApp()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())