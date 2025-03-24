from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Callable
from webbrowser import open as open_url

from httpx import URL, AsyncClient, HTTPStatusError, RequestError
from markdown_it import MarkdownIt
from mdit_py_plugins import front_matter
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import var
from textual.widgets import Markdown, Static, Footer  # Make sure to import Footer

from rich.syntax import Syntax
from rich.traceback import Traceback
from ..dialogs import ErrorDialog
from ..utility.advertising import APPLICATION_TITLE, USER_AGENT

__version__ = "1.0.0"  # Define the version here

PLACEHOLDER = f"""\
# {APPLICATION_TITLE} {__version__}

Welcome to {APPLICATION_TITLE}!
"""

class History:
    """Holds the browsing history for the viewer."""

    MAXIMUM_HISTORY_LENGTH: Final[int] = 256

    def __init__(self, history: list[Path | URL] | None = None) -> None:
        self._history: deque[Path | URL] = deque(
            history or [], maxlen=self.MAXIMUM_HISTORY_LENGTH
        )
        self._current: int = max(len(self._history) - 1, 0)

    @property
    def location(self) -> Path | URL | None:
        try:
            return self._history[self._current]
        except IndexError:
            return None

    def remember(self, location: Path | URL) -> None:
        self._history.append(location)
        self._current = len(self._history) - 1

    def back(self) -> bool:
        if self._current:
            self._current -= 1
            return True
        return False

    def forward(self) -> bool:
        if self._current < len(self._history) - 1:
            self._current += 1
            return True
        return False

class Viewer(VerticalScroll, can_focus=True, can_focus_children=True):
    """The markdown viewer class."""

    DEFAULT_CSS = """
    Viewer {
        width: 1fr;
        scrollbar-gutter: stable;
    }
    """

    BINDINGS = [
        Binding("w,k", "scroll_up", "", show=False),
        Binding("s,j", "scroll_down", "", show=False),
        Binding("space", "page_down", "", show=False),
        Binding("b", "page_up", "", show=False),
    ]

    history: var[History] = var(History)
    viewing_location: var[bool] = var(False)

    def compose(self) -> ComposeResult:
        """Compose the markdown viewer."""
        yield Static("Click on a file to view its contents.", id="intro-message")  # Message at the start
        yield Footer()
        yield Static(id="code", expand=True)  # This Static widget will hold the syntax-highlighted code

    @property
    def document(self) -> Static:
        """The Static widget to show the code content."""
        return self.query_one("#code")  # Query by ID to get the correct Static widget

    @property
    def location(self) -> Path | URL | None:
        return self.history.location if self.viewing_location else None

    def show_syntax(self, syntax: Syntax) -> None:
        """Display the syntax-highlighted code in the viewer."""
        self.viewing_location = False
        self.document.update(syntax)  # Update the Static widget with the syntax-highlighted code
        self.scroll_home(animate=False)

    def show(self, content: str) -> None:
        """Show regular text content in the viewer."""
        self.viewing_location = False
        self.document.update(content)  # Update the Static widget with the regular content
        self.scroll_home(animate=False)

    def visit_code_file(self, file_path: Path) -> None:
        """Handle when a code file is selected and display it."""
        try:
            syntax = Syntax.from_path(
                file_path,
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark" if self.current_theme.dark else "github-light",
            )
            self.show_syntax(syntax)  # Show syntax-highlighted code
        except Exception as e:
            self.show(f"Error opening file: {file_path}\n{str(e)}")  # Show error message if file can't be opened

    def visit(self, location: Path | URL, remember: bool = True) -> None:
        if isinstance(location, Path):
            self.visit_code_file(location)  # Visit code file if it's a path
        elif isinstance(location, URL):
            self._remote_load(location, remember)

    def reload(self) -> None:
        """Reload the current location."""
        if self.location is not None:
            self.visit(self.location, False)

    def load_history(self, history: list[Path | URL]) -> None:
        self.history = History(history)

    def delete_history(self, history_id: int) -> None:
        try:
            del self.history[history_id]
        except IndexError:
            pass

    def clear_history(self) -> None:
        self.load_history([])
