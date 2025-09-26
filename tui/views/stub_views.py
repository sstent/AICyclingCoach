"""
Stub views for Plans, Rules, and Routes.
These can be expanded later following the same async loading pattern.
"""
from textual.app import ComposeResult
from textual.widgets import Static
from tui.views.base_view import BaseView


class PlanView(BaseView):
    """Training plan management view."""
    
    def compose(self) -> ComposeResult:
        """Create plan view layout."""
        yield Static("Training Plans")
        yield Static("Coming soon - this will show your training plans")
    
    def load_data_if_needed(self) -> None:
        """Load plan data if needed."""
        # Implement similar to WorkoutView when ready
        pass


class RuleView(BaseView):
    """Training rule management view."""
    
    def compose(self) -> ComposeResult:
        """Create rule view layout."""
        yield Static("Training Rules")
        yield Static("Coming soon - this will show your training rules")
    
    def load_data_if_needed(self) -> None:
        """Load rule data if needed."""
        # Implement similar to WorkoutView when ready
        pass


class RouteView(BaseView):
    """Route management view."""
    
    def compose(self) -> ComposeResult:
        """Create route view layout."""
        yield Static("Routes")
        yield Static("Coming soon - this will show your routes")
    
    def load_data_if_needed(self) -> None:
        """Load route data if needed."""
        # Implement similar to WorkoutView when ready
        pass