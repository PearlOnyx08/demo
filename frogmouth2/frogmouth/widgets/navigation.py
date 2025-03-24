from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import var
from textual.widgets import TabbedContent, Tabs, TabPane
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

    Tabs {
        dock: top;
        height: 3;
    }
    """

    BINDINGS = [
        Binding("comma,a,ctrl+left,shift+left,h", "previous_tab", "", show=False),
        Binding("full_stop,d,ctrl+right,shift+right,l", "next_tab", "", show=False),
        Binding("\\", "toggle_dock", "Dock left/right"),
    ]

    popped_out: var[bool] = var(False)
    docked_left: var[bool] = var(True)

    class Hidden(Message):
        """Message sent when the navigation is hidden."""

    def compose(self) -> ComposeResult:
        """Compose the content of the navigation pane."""
        self.popped_out = False

        with TabbedContent(initial="local_files") as tabs:
            self._tabs = tabs
            #with TabPane("Table of Contents", id="table_of_contents"):
            #    self._contents = TableOfContents()
            #    yield self._contents
            with TabPane("Local Files", id="local_files"):
                self._local_files = LocalFiles()  # <-- FIX HERE: no args!
                yield self._local_files
            #with TabPane("Bookmarks", id="bookmarks"):
            #    self._bookmarks = Bookmarks()
            #    yield self._bookmarks
            #with TabPane("History", id="history"):
            #    self._history = History()
            #    yield self._history

    def on_mount(self) -> None:
        """Configure navigation once the DOM is set up."""
        self.docked_left = load_config().navigation_left
        self.jump_to_local_files()

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

    @property
    def table_of_contents(self) -> TableOfContents:
        """The table of contents widget."""
        return self._contents

    @property
    def local_files(self) -> LocalFiles:
        """The local files widget."""
        return self._local_files

    @property
    def bookmarks(self) -> Bookmarks:
        """The bookmarks widget."""
        return self._bookmarks

    @property
    def history(self) -> History:
        """The history widget."""
        return self._history

    def jump_to_local_files(self, target: Path | None = None) -> Self:
        if self.popped_out and self._tabs.active == "local_files":
            self.popped_out = False
        else:
            self.popped_out = True
            self._tabs.active = "local_files"
            if target:
                self._local_files.chdir(target)
            self._local_files.focus()
        return self

    def jump_to_bookmarks(self) -> Self:
        if self.popped_out and self._tabs.active == "bookmarks":
            self.popped_out = False
        else:
            self.popped_out = True
            self._tabs.active = "bookmarks"
            self._bookmarks.focus()
        return self

    def jump_to_history(self) -> Self:
        if self.popped_out and self._tabs.active == "history":
            self.popped_out = False
        else:
            self.popped_out = True
            self._tabs.active = "history"
            self._history.focus()
        return self

    def jump_to_contents(self) -> Self:
        if self.popped_out and self._tabs.active == "table_of_contents":
            self.popped_out = False
        else:
            self.popped_out = True
            self._tabs.active = "table_of_contents"
            self._contents.focus()
        return self

    def action_previous_tab(self) -> None:
        self._tabs.action_previous_tab()
        self.focus_tab()

    def action_next_tab(self) -> None:
        self._tabs.action_next_tab()
        self.focus_tab()

    def action_toggle_dock(self) -> None:
        config = load_config()
        config.navigation_left = not config.navigation_left
        save_config(config)
        self.docked_left = config.navigation_left

    def focus_tab(self) -> None:
        if self._tabs.active:
            self.query_one(f"TabPane#{self._tabs.active}").focus()

    def refresh_local_files(self) -> None:
        self._local_files.refresh_tree()

    def on_local_files_refresh_message(self, message: LocalFiles.RefreshMessage) -> None:
        self.refresh_local_files()
