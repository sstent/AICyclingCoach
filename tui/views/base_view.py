from textual.app import ComposeResult
from textual.widget import Widget
from textual.worker import Worker, get_current_worker
from textual import work, on
import sys
from typing import Callable, Any, Coroutine, Optional
from tui.widgets.error_modal import ErrorModal

class BaseView(Widget):
    """Base view class with async utilities that all views should inherit from."""
    
    def run_async(self, coro: Coroutine, callback: Callable[[Any], None] = None) -> Worker:
        """Run an async task in the background with proper error handling."""
        sys.stdout.write("BaseView.run_async: START\n")
        worker = self.run_worker(
            self._async_wrapper(coro, callback),
            exclusive=True,
            group="db_operations"
        )
        sys.stdout.write("BaseView.run_async: END\n")
        return worker
    
    async def _async_wrapper(self, coro: Coroutine, callback: Callable[[Any], None] = None) -> None:
        """Wrapper for async operations with cancellation support."""
        sys.stdout.write("BaseView._async_wrapper: START\n")
        try:
            sys.stdout.write("BaseView._async_wrapper: Before await coro\n")
            result = await coro
            sys.stdout.write("BaseView._async_wrapper: After await coro\n")
            if callback:
                sys.stdout.write("BaseView._async_wrapper: Calling callback\n")
                self.call_after_refresh(callback, result)
        except Exception as e:
            sys.stdout.write(f"BaseView._async_wrapper: ERROR: {str(e)}\n")
            self.log(f"Async operation failed: {str(e)}", severity="error")
            self.app.bell()
            self.call_after_refresh(
                self.show_error,
                str(e),
                lambda: self.run_async(coro, callback)
            )
        finally:
            sys.stdout.write("BaseView._async_wrapper: FINALLY\n")
            worker = get_current_worker()
            if worker and worker.is_cancelled:
                sys.stdout.write("BaseView._async_wrapper: Worker cancelled\n")
                self.log("Async operation cancelled")

    def show_error(self, message: str, retry_action: Optional[Callable] = None) -> None:
        """Display error modal with retry option."""
        self.app.push_screen(ErrorModal(message, retry_action))