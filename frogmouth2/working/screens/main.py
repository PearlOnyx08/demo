from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Awaitable, Callable
from webbrowser import open as open_url

from httpx import URL
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Paste
from textual.screen import Screen
from textual.widgets import Footer, Markdown
from rich.syntax import Syntax  # ✅ Add syntax highlighting

from ..widgets import Navigation, Omnibox, Viewer
from ..widgets.navigation_panes import LocalFiles


class Main(Screen[None]):
    """The main screen for the application."""

    DEFAULT_CSS = """
    .focusable {
        border: blank;
    }

    .focusable:focus {
        border: heavy $accent !important;
    }

    Screen Tabs {
        border: blank;
        height: 5;
    }

    Screen Tabs:focus {
        border: heavy $accent !important;
        height: 5;
    }

    Screen TabbedContent TabPane {
        padding: 0 1;
        border: blank;
    }

    Screen TabbedContent TabPane:focus-within {
        border: heavy $accent !important;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Quit"),
        Binding("ctrl+n", "navigation", "Navigation"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        yield Omnibox(classes="focusable")
        with Horizontal():
            yield Navigation()
            yield Viewer(classes="focusable")
        yield Footer()

    def on_local_files_file_selected(self, event: LocalFiles.FileSelected) -> None:
        """Handle when a file is clicked in the directory tree."""
        file_path = event.file_path

        if file_path.suffix in {".py", ".js", ".html", ".md", ".txt", ".json"}:  # ✅ Add more as needed
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    file_content = file.read()

                if file_path.suffix in {".py", ".js", ".html", ".json"}:
                    # ✅ Use syntax highlighting for code files
                    syntax = Syntax(file_content, file_path.suffix.lstrip("."), theme="monokai", line_numbers=True)
                    self.query_one(Viewer).document.update(syntax)  # ✅ Render the `Syntax` widget properly

                else:
                    # ✅ For Markdown & text files, show normally
                    self.query_one(Viewer).document.update(file_content)  # ✅ Fix: Use `.document.update()`

            except Exception as e:
                self.app.log(f"Error opening file: {e}")
                self.query_one(Viewer).document.update(f"Error opening file: {file_path}\n\n{e}")  # ✅ Fix

    def action_navigation(self) -> None:
        """Toggle the availability of the navigation sidebar."""
        navigation = self.query_one(Navigation)
        navigation.toggle()
