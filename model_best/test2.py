from __future__ import annotations

from pathlib import Path
from typing import Iterable
from httpx import URL
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DirectoryTree
from ...utility import maybe_markdown
from .navigation_pane import NavigationPane
import threading
import time


class FilteredDirectoryTree(DirectoryTree):  # pylint:disable=too-many-ancestors
    """A `DirectoryTree` filtered for the markdown viewer."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filter the directory tree for the Markdown viewer.

        Args:
            paths: The paths to be filtered.

        Returns:
            The parts filtered for the Markdown viewer.

        The filtered set will include all filesystem entries that aren't
        hidden (in a Unix sense of hidden) which are either a directory or a
        file that looks like it could be a Markdown document.
        """
        try:
            return [
                path
                for path in paths
                if not path.name.startswith(".")
                and path.is_dir()
                or (path.is_file() and maybe_markdown(path))
            ]
        except PermissionError:
            return []


class DirectoryWatcher(FileSystemEventHandler):
    """Watches the directory for changes and refreshes the tree."""

    def __init__(self, tree: FilteredDirectoryTree):
        self.tree = tree

    def on_any_event(self, event):
        """Handle any filesystem event by refreshing the tree."""
        self.tree.refresh()


class LocalFiles(NavigationPane):
    """Local file picking navigation pane."""

    DEFAULT_CSS = """
    LocalFiles {
        height: 100%;
    }

    LocalFiles > DirectoryTree {
        background: $panel;
        width: 1fr;
    }

    LocalFiles > DirectoryTree:focus .tree--cursor, LocalFiles > DirectoryTree .tree--cursor {
        background: $accent 50%;
        color: $text;
    }
    """

    def __init__(self) -> None:
        """Initialise the local files navigation pane."""
        super().__init__("Local")
        self.tree = FilteredDirectoryTree(Path("~").expanduser())
        self.observer = Observer()

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield self.tree
        self.start_watching()

    def start_watching(self):
        """Start watching the directory for changes."""
        event_handler = DirectoryWatcher(self.tree)
        self.observer.schedule(event_handler, str(self.tree.path), recursive=True)
        thread = threading.Thread(target=self.observer.start, daemon=True)
        thread.start()

    def chdir(self, path: Path) -> None:
        """Change the filesystem view to the given directory.

        Args:
            path: The path to change to.
        """
        self.tree.path = path
        self.observer.unschedule_all()
        self.start_watching()

    def set_focus_within(self) -> None:
        """Focus the directory tree."""
        self.tree.focus(scroll_visible=False)

    class Goto(Message):
        """Message that requests the viewer goes to a given location."""

        def __init__(self, location: Path | URL) -> None:
            """Initialise the history goto message.

            Args:
                location: The location to go to.
            """
            super().__init__()
            self.location = location
            """The location to go to."""

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle a file being selected in the directory tree.

        Args:
            event: The direct tree selection event.
        """
        event.stop()
        self.post_message(self.Goto(Path(event.path)))

    def __del__(self):
        """Ensure observer stops when object is deleted."""
        self.observer.stop()
        self.observer.join()
