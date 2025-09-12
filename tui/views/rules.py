"""
Rules view for AI Cycling Coach TUI.
Displays training rules, rule creation and editing.
"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Placeholder
from textual.widget import Widget


class RuleView(Widget):
    """Training rules management view."""
    
    def compose(self) -> ComposeResult:
        """Create rules view layout."""
        with Container():
            yield Static("Training Rules", classes="view-title")
            yield Placeholder("Rule creation and editing will be displayed here")