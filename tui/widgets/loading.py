"""
Loading spinner components for TUI.
"""
from textual.widgets import Static
from rich.spinner import Spinner

class LoadingSpinner(Static):
    """Animated loading spinner component."""
    
    def __init__(self, text: str = "Loading...", spinner: str = "dots") -> None:
        super().__init__()
        self.spinner = Spinner(spinner, text=text)
        
    def on_mount(self) -> None:
        self.set_interval(0.1, self.update_spinner)
        
    def update_spinner(self) -> None:
        self.update(self.spinner)