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
    """The markdown and code viewer class."""

    DEFAULT_CSS = """
    Viewer {
        width: 1fr;
        scrollbar-gutter: stable;
    }
    """

    history: var[History] = var(History)
    viewing_location: var[bool] = var(False)

    def compose(self) -> ComposeResult:
        yield Markdown(PLACEHOLDER, id="markdown-view")
        yield Static(id="code-view", expand=True)

    @property
    def markdown_view(self) -> Markdown:
        return self.query_one("#markdown-view")

    @property
    def code_view(self) -> Static:
        return self.query_one("#code-view")

    @property
    def location(self) -> Path | URL | None:
        return self.history.location if self.viewing_location else None

    def show_markdown(self, markdown: str) -> None:
        self.viewing_location = True
        self.markdown_view.update(markdown)
        self.markdown_view.display = True
        self.code_view.display = False
        self.scroll_home(animate=False)

    def show_syntax(self, syntax: Syntax) -> None:
        self.viewing_location = False
        self.code_view.update(syntax)
        self.markdown_view.display = False
        self.code_view.display = True
        self.scroll_home(animate=False)

    def show_text(self, content: str) -> None:
        self.viewing_location = False
        self.code_view.update(content)
        self.markdown_view.display = False
        self.code_view.display = True
        self.scroll_home(animate=False)

    def visit_code_file(self, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding='utf-8')
            syntax = Syntax(
                content,
                file_path.suffix.lstrip("."),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="monokai",
            )
            self.show_syntax(syntax)
        except Exception as e:
            self.show_text(f"Error opening file: {file_path}\n{str(e)}")


    def visit_markdown_file(self, file_path: Path) -> None:
        try:
            markdown = file_path.read_text(encoding='utf-8')
            self.show_markdown(markdown)
        except Exception as e:
            self.show_text(f"Error opening file: {file_path}\n{str(e)}")

    def visit(self, location: Path | URL, remember: bool = True) -> None:
        if remember:
            self.history.remember(location)

        if isinstance(location, Path):
            if location.suffix in {".md", ".markdown"}:
                self.visit_markdown_file(location)
            elif location.suffix in {".txt"}:
                self.show_text(location.read_text())
            else:
                self.visit_code_file(location)
        elif isinstance(location, URL):
            self._remote_load(location, remember)

    def reload(self) -> None:
        if self.location is not None:
            self.visit(self.location, False)

    def load_history(self, history: list[Path | URL]) -> None:
        self.history = History(history)

    def delete_history(self, history_id: int) -> None:
        try:
            del self.history._history[history_id]
        except IndexError:
            pass

    def clear_history(self) -> None:
        self.load_history([])
        
    def scroll_to_block(self, block_id: str) -> None:
        """Scroll the Markdown view to the given block ID."""
        self.scroll_to_widget(self.markdown_view.query_one(f"#{block_id}"), top=True)
