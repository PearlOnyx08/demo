from __future__ import annotations

import sys
from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive, var
from textual.widgets import DirectoryTree, Footer, Header, Static, Log


class DebugConsole(Log):
    """A widget that displays debug logs inside the UI."""

    def on_mount(self):
        """Redirects standard output to this widget."""
        self.write("[DEBUG] Debug console started...")
        import sys
        sys.stdout = self  # Redirect stdout to this widget

    def write(self, message):
        """Capture and display print output."""
        self.write_line(message.rstrip())


class FixedCodeBrowser(App):
    """Textual code browser app (with debugging)."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
    ]

    show_tree = var(True)
    path: reactive[str | None] = reactive(None)

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        yield Header()
        with Container():
            yield DirectoryTree(path, id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
        yield DebugConsole(id="debug-log")  # ✅ Debug log at the bottom
        yield Footer()

    def on_mount(self) -> None:
        """Ensure tree is focused."""
        self.query_one(DirectoryTree).focus()
        print("[DEBUG] App mounted")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user clicks a file in the directory tree."""
        event.stop()
        self.path = str(event.path)
        print(f"[DEBUG] File selected: {self.path}")  # ✅ Confirms click event

    def watch_path(self, path: str | None) -> None:
        """Called when path changes (i.e., a file is clicked)."""
        print(f"[DEBUG] Updating path: {path}")  # ✅ Logs the path update
        code_view = self.query_one("#code", Static)
        if path is None:
            code_view.update("")
            return
        try:
            syntax = Syntax.from_path(
                path,
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark" if self.current_theme.dark else "github-light",
            )
            print("[DEBUG] Successfully loaded syntax")
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = path

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree


if __name__ == "__main__":
    FixedCodeBrowser().run()
