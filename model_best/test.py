from __future__ import annotations

import sys
import os
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.reactive import reactive
from textual.widgets import DirectoryTree, Static, Footer, Header, Log
from textual.scroll_view import ScrollView  # Ensure correct import for newer versions

WATCH_DIR = Path("./") if len(sys.argv) < 2 else Path(sys.argv[1])  # Allow command-line path


### 📌 DEBUG CONSOLE (For Troubleshooting)
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


### 📌 DIRECTORY TREE (Auto-Refreshing Version)
class LiveUpdatingDirectoryTree(DirectoryTree):
    """Directory tree that refreshes immediately when files are added/removed."""

    path = reactive(WATCH_DIR)

    def on_mount(self):
        """Initialize the directory tree and start watching for changes."""
        print("[DEBUG] DirectoryTree mounted")
        self.refresh_tree()
        self.watch_directory()

    def refresh_tree(self):
        """Rebuild the entire tree from scratch to reflect file changes."""
        print("[DEBUG] Full directory refresh triggered")
        self.clear()  # ✅ Clears the entire tree before reloading
        self.build_tree(self.root, self.path)
        self.expand_all_nodes(self.root)  # ✅ Expand nodes after refresh

    def build_tree(self, parent, path):
        """Recursively build the directory tree."""
        try:
            for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                node = parent.add(item.name, data=item)
                if item.is_dir():
                    self.build_tree(node, item)  # Recurse into directories
        except PermissionError:
            pass  # Skip inaccessible directories

    def expand_all_nodes(self, node):
        """Expand all nodes to show new files immediately."""
        node.expand()
        for child in node.children:
            child.expand()
            self.expand_all_nodes(child)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file selection and update the code preview."""
        event.stop()
        file_path = event.path
        print(f"[DEBUG] File selected: {file_path}")
        self.app.show_file_content(file_path)

    def watch_directory(self):
        """Start a background thread to watch the directory for changes."""
        print("[DEBUG] Starting directory watcher")
        self.observer = Observer()
        event_handler = DirectoryWatcher(self)
        self.observer.schedule(event_handler, self.path, recursive=True)
        self.observer.start()


### 📌 CODE VIEWER (Displays Syntax-Highlighted Code)
class CodeViewer(ScrollView):
    """Scrollable widget to display syntax-highlighted code."""

    def on_mount(self):
        """Ensure a Static widget exists for updating."""
        print("[DEBUG] CodeViewer mounted")
        self.code_display = Static(id="code", expand=True)
        self.mount(self.code_display)

    def update_content(self, file_path):
        """Update the content of the code viewer when a file is clicked."""
        print(f"[DEBUG] Updating content for: {file_path}")
        self.code_display.update(f"[yellow]Loading {file_path}...[/yellow]")

        try:
            syntax = Syntax.from_path(
                file_path,
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
            print("[DEBUG] Successfully loaded syntax")
            self.code_display.update(syntax)

        except Exception as e:
            print(f"[ERROR] Failed to load file: {e}")
            self.code_display.update(Traceback(theme="github-dark", width=None))


### 📌 DIRECTORY WATCHER (Detects File Changes & Triggers Refresh)
class DirectoryWatcher(FileSystemEventHandler):
    """Watches a directory and refreshes the tree when files change."""

    def __init__(self, tree_widget):
        super().__init__()
        self.tree_widget = tree_widget

    def on_any_event(self, event):
        """Trigger a full directory refresh when any file system change is detected."""
        print(f"[DEBUG] File system change detected: {event.src_path}")
        self.tree_widget.app.call_from_thread(self.tree_widget.refresh_tree)


### 📌 MAIN APPLICATION (Combines Everything)
class CodeBrowserApp(App):
    """Main application with a live-updating directory tree and code viewer."""

    CSS_PATH = "code_browser.tcss"  # Load the `.tcss` file for styling
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        """Initialize the app and create an observer for file watching."""
        super().__init__()
        self.observer = None  # Track observer instance

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()
        with Vertical():
            with Horizontal():
                self.tree = LiveUpdatingDirectoryTree(WATCH_DIR, id="tree-view")  # ✅ Now updates live!
                yield self.tree
                with VerticalScroll(id="code-view"):
                    yield CodeViewer()  # ✅ Uses ScrollView correctly
            yield DebugConsole(id="debug-log")  # ✅ Debug Console at the bottom
        yield Footer()

    def show_file_content(self, file_path):
        """Show the selected file's contents in the code viewer."""
        print(f"[DEBUG] Loading file: {file_path}")
        viewer = self.query_one(CodeViewer)
        viewer.update_content(file_path)

    def on_mount(self):
        """Start directory watching."""
        print("[DEBUG] App mounted")
        self.tree.watch_directory()
        self.observer = self.tree.observer  # Store observer reference

    def on_exit(self):
        """Stop the file observer when the app exits."""
        if self.observer:
            print("[DEBUG] Stopping file observer")
            self.observer.stop()
            self.observer.join()


if __name__ == "__main__":
    CodeBrowserApp().run()
