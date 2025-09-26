"""
Base view class for TUI application with common async utilities.
"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.worker import Worker, get_current_worker
from textual import work, on
from typing import Callable, Any, Coroutine, Optional
from tui.widgets.error_modal import ErrorModal

class BaseView(Widget):
    """Base view class with async utilities that all views should inherit from."""
    
    def run_async(self, coro: Coroutine, callback: Callable[[Any], None] = None) -> Worker:
        """Run an async task in the background with proper error handling."""
        worker = self.run_worker(
            self._async_wrapper(coro, callback),
            exclusive=True,
            group="db_operations"
        )
        return worker
    
    async def _async_wrapper(self, coro: Coroutine, callback: Callable[[Any], None] = None) -> None:
        """Wrapper for async operations with cancellation support."""
        try:
            result = await coro
            if callback:
                self.call_after_refresh(callback, result)
        except Exception as e:
            self.log(f"Async operation failed: {str(e)}", severity="error")
            self.app.bell()
            self.call_after_refresh(
                self.show_error,
                str(e),
                lambda: self.run_async(coro, callback)
            )
        finally:
            worker = get_current_worker()
            if worker and worker.is_cancelled:
                self.log("Async operation cancelled")

    def show_error(self, message: str, retry_action: Optional[Callable] = None) -> None:
        """Display error modal with retry option."""
        self.app.push_screen(ErrorModal(message, retry_action))