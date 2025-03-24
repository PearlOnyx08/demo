from __future__ import annotations

from pathlib import Path
from typing import Iterable
from httpx import URL
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DirectoryTree
from ...utility import maybe_markdown
from .navigation_pane import NavigationPane

class FilteredDirectoryTree(DirectoryTree):
    CODE_EXTENSIONS = {".py", ".cpp", ".c", ".h", ".hpp", ".java", ".js", ".ts",
                       ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".md", ".markdown",
                       ".txt", ".sh", ".rb", ".go", ".rs", ".kt", ".swift"}

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        try:
            return [
                path
                for path in paths
                if not path.name.startswith(".")
                and (path.is_dir() or (path.is_file() and path.suffix in self.CODE_EXTENSIONS))
            ]
        except PermissionError:
            return []

class LocalFiles(NavigationPane):
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
        super().__init__("Local")

    def compose(self) -> ComposeResult:
        self.file_tree = FilteredDirectoryTree(Path("~").expanduser())
        yield self.file_tree

    def on_mount(self) -> None:
        # ADD BACK AUTO-REFRESH HERE CLEARLY:
        self.set_interval(5, self.refresh_tree)

    def refresh_tree(self) -> None:
        """Refresh the tree periodically."""
        self.file_tree.reload()

    def chdir(self, path: Path) -> None:
        self.file_tree.path = path

    def set_focus_within(self) -> None:
        self.file_tree.focus(scroll_visible=False)

    class Goto(Message):
        def __init__(self, location: Path | URL) -> None:
            super().__init__()
            self.location = location

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        self.post_message(self.Goto(Path(event.path)))
