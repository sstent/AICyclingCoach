"""
Error modal component for TUI.
"""
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Container, Vertical
from textual import on

class ErrorModal(ModalScreen):
    """Modal dialog for displaying errors with retry capability."""
    
    def __init__(self, message: str, retry_action: callable = None):
        super().__init__()
        self.message = message
        self.retry_action = retry_action
        
    def compose(self) -> ComposeResult:
        with Vertical(id="error-dialog"):
            yield Static(f"⚠️ {self.message}", id="error-message")
            with Container(id="error-buttons"):
                if self.retry_action:
                    yield Button("Retry", variant="error", id="retry-btn")
                yield Button("Dismiss", variant="primary", id="dismiss-btn")

    @on(Button.Pressed, "#retry-btn")
    def on_retry(self):
        if self.retry_action:
            self.dismiss()
            self.retry_action()

    @on(Button.Pressed, "#dismiss-btn")
    def on_dismiss(self):
        self.dismiss()