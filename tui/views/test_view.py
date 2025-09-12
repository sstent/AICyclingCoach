"""
Simple test view to verify TUI framework functionality.
"""
from textual.app import ComposeResult
from textual.widgets import Static
from textual.widget import Widget

class TestView(Widget):
    """Test view with static content to verify TUI rendering."""
    
    def compose(self) -> ComposeResult:
        yield Static("TUI Framework Test", classes="view-title")
        yield Static("This is a simple test view to verify TUI functionality.")
        yield Static("If you see this text, the TUI framework is working correctly.")
        yield Static("Check marks: [✓] Text rendering [✓] Basic layout")
        
    def on_mount(self) -> None:
        self.log("TestView mounted successfully")
