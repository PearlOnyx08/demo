from __future__ import annotations

import sys
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import DirectoryTree, Static, Footer, Header, Log
from textual.scroll_view import ScrollView  # Correct import for new versions

WATCH_DIR = str(Path("./") if len(sys.argv) < 2 else Path(sys.argv[1]))  # Convert Path to string


### 📌 DEBUG CONSOLE (For Troubleshooting)
class DebugConsole(Log):
    """A widget that displays debug logs inside the UI."""

    def on_mount(self):
        self.write("[DEBUG] Debug console started...")
        import sys
        sys.stdout = self  # Redirect stdout to this widget

    def write(self, message):
        self.write_line(message.rstrip())


### 📌 DIRECTORY TREE (Fixed for Textual Updates)
class LiveUpdatingDirectoryTree(DirectoryTree):
    """Directory tree that refreshes when triggered externally."""

    def on_mount(self):
        """Initialize the directory tree."""
        print("[DEBUG] DirectoryTree mounted")
        self.set_path(WATCH_DIR)  # ✅ Correctly set path without errors
        self.run_worker(self.watch_path())  # ✅ Properly awaited

    async def watch_path(self):
        """Ensures directory tree updates properly."""
        has_cursor = self.cursor_node is not None
        self.refresh_tree()
        if has_cursor:
            self.cursor_line = 0
        self.scroll_to(0, 0, animate=False)

    def refresh_tree(self):
        """Rebuild the tree to reflect file changes."""
        print("[DEBUG] Full directory refresh triggered")
        self.clear()  # ✅ Clears the entire tree before reloading
        self.set_path(WATCH_DIR)  # ✅ Correct way to reset the path
        self.expand_all_nodes(self.root)

    def expand_all_nodes(self, node):
        node.expand()
        for child in node.children:
            child.expand()
            self.expand_all_nodes(child)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        event.stop()
        file_path = event.path
        print(f"[DEBUG] File selected: {file_path}")
        self.app.show_file_content(file_path)


### 📌 CODE VIEWER (Displays Syntax-Highlighted Code)
class CodeViewer(ScrollView):
    """Scrollable widget to display syntax-highlighted code."""

    def on_mount(self):
        self.code_display = Static(id="code", expand=True)
        self.mount(self.code_display)

    def update_content(self, file_path):
        self.code_display.update(f"[yellow]Loading {file_path}...[/yellow]")

        try:
            syntax = Syntax.from_path(
                file_path,
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
            self.code_display.update(syntax)

        except Exception as e:
            self.code_display.update(Traceback(theme="github-dark", width=None))


### 📌 DIRECTORY WATCHER (Detects File Changes)
class DirectoryWatcher(FileSystemEventHandler):
    def __init__(self, app: CodeBrowserApp):
        super().__init__()
        self.app = app

    def on_any_event(self, event):
        if not event.is_directory:
            print(f"[DEBUG] File system change detected: {event.src_path}")
            self.app.call_from_thread(self.app.refresh_tree)


### 📌 MAIN APPLICATION
class CodeBrowserApp(App):
    """Main application with a live-updating directory tree and code viewer."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.observer = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal():
                self.tree = LiveUpdatingDirectoryTree(WATCH_DIR, id="tree-view")  # ✅ Fixed
                yield self.tree
                with VerticalScroll(id="code-view"):
                    yield CodeViewer()
            yield DebugConsole(id="debug-log")
        yield Footer()

    def show_file_content(self, file_path):
        viewer = self.query_one(CodeViewer)
        viewer.update_content(file_path)

    def refresh_tree(self):
        """Externally refresh the directory tree when files change."""
        print("[DEBUG] External tree refresh triggered")
        self.tree.refresh_tree()

    def on_mount(self):
        print("[DEBUG] App mounted")
        self.start_watching_directory()

    def start_watching_directory(self):
        print("[DEBUG] Starting directory watcher")
        event_handler = DirectoryWatcher(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, WATCH_DIR, recursive=True)
        self.observer.start()

    def on_exit(self):
        """Stop the file observer when the app exits."""
        if self.observer:
            print("[DEBUG] Stopping file observer")
            self.observer.stop()
            self.observer.join()


if __name__ == "__main__":
    CodeBrowserApp().run()
