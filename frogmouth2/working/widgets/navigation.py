from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import var
from textual.widgets import TabbedContent, Tabs, DirectoryTree
from typing_extensions import Self

from ..data import load_config, save_config
from .navigation_panes.bookmarks import Bookmarks
from .navigation_panes.history import History
from .navigation_panes.local_files import LocalFiles
from .navigation_panes.table_of_contents import TableOfContents


class Navigation(Vertical, can_focus=False, can_focus_children=True):
    """A navigation panel widget."""

    DEFAULT_CSS = """
    Navigation {
        width: 44;
        background: $panel;
        display: block;
        dock: left;
    }

    Navigation.hidden {
        display: none;
    }

    TabbedContent {
        height: 100% !important;
    }

    ContentSwitcher {
        height: 1fr !important;
    }
    """

    BINDINGS = [
        Binding("comma,a,ctrl+left,shift+left,h", "previous_tab", "", show=False),
        Binding("full_stop,d,ctrl+right,shift+right,l", "next_tab", "", show=False),
        Binding("\\", "toggle_dock", "Dock left/right"),
        Binding("ctrl+q", "app.quit", "Quit"),
        Binding("ctrl+n", "navigation", "Navigation"),  # ✅ This adds the Navigation option
    ]
    """Bindings local to the navigation pane."""

    popped_out: var[bool] = var(False)
    """Is the navigation popped out?"""

    docked_left: var[bool] = var(True)
    """Should navigation be docked to the left side of the screen?"""

    def compose(self) -> ComposeResult:
        """Compose the content of the navigation pane."""
        self.popped_out = False
        self._contents = TableOfContents()
        self._local_files = LocalFiles()
        self._bookmarks = Bookmarks()
        self._history = History()
        
        with TabbedContent() as tabs:
            self._tabs = tabs
            yield self._contents
            yield self._local_files
            yield self._bookmarks
            yield self._history

    def on_mount(self) -> None:
        """Configure navigation once the DOM is set up."""
        self.docked_left = load_config().navigation_left
        self.jump_to_local_files()  # ✅ Ensure the Local Files view opens by default

    class Hidden(Message):
        """Message sent when the navigation is hidden."""

    def watch_popped_out(self) -> None:
        """Watch for changes to the popped out state."""
        self.set_class(not self.popped_out, "hidden")
        if not self.popped_out:
            self.post_message(self.Hidden())

    def toggle(self) -> None:
        """Toggle the popped/unpopped state."""
        self.popped_out = not self.popped_out

    def watch_docked_left(self) -> None:
        """Watch for changes to the left-docking status."""
        self.styles.dock = "left" if self.docked_left else "right"

    def jump_to_local_files(self, target: Path | None = None) -> Self:
        """Switch to and focus the local files pane."""
        if self.popped_out and target is None and self.query_one(Tabs).active == self._local_files.id:
            self.popped_out = False
        else:
            self.popped_out = True
            self.query_one(Tabs).active = self._local_files.id  # ✅ Switch to Local Files tab
            if target is not None:
                self._local_files.chdir(target)
            
            # ✅ Focus on the DirectoryTree inside LocalFiles
            self._local_files.query_one(DirectoryTree).focus()

        return self
