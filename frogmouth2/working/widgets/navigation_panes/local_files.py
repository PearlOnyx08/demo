from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import DirectoryTree
from textual.containers import Vertical
from textual.message import Message


class LocalFiles(Vertical):
    """A pane that displays a file tree of the local filesystem."""

    DEFAULT_CSS = """
    LocalFiles {
        width: 1fr;
        height: 100%;
    }

    DirectoryTree {
        height: 1fr;
    }
    """

    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, file_path: Path) -> None:
            super().__init__()
            self.file_path = file_path

    def compose(self) -> ComposeResult:
        """Compose the local files pane."""
        yield DirectoryTree(Path.home(), id="directory_tree")

    def on_mount(self) -> None:
        """Ensure correct directory structure is visible on startup."""
        self.file_tree = self.query_one(DirectoryTree)
        self.file_tree.focus()
        self.file_tree.refresh()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection and trigger file viewing."""
        self.post_message(self.FileSelected(event.path))
