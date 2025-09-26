from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
class BasicApp(App):
  def compose(self) -> ComposeResult:
    yield Header()
    yield Static("Hello, Textual!")
    yield Footer()

if __name__ == "__main__":
  app = BasicApp()
  app.run()
