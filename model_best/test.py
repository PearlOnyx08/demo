from __future__ import annotations

import os
import sys
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Tree, Static, Footer, Header
from textual.scroll_view import ScrollView  # ✅ Correct import for newer versions

WATCH_DIR = "./" if len(sys.argv) < 2 else sys.argv[1]  # Allow command-line path


### 📌 CUSTOM DIRECTORY TREE (Now Includes Debugging Prints)
class DirectoryTree(Tree):
    """Custom directory tree widget."""

    path = reactive(WATCH_DIR)

    def on_mount(self):
        """Build the tree when the widget mounts."""
        print("[DEBUG] DirectoryTree mounted")  # ✅ Check if this runs
        self.build_tree(self.path)
        self.expand_all_nodes(self.root)

    def build_tree(self, path):
        """Recursively add directories and files to the tree."""
        print(f"[DEBUG] Building tree for: {path}")  # ✅ Confirm it runs
        self.clear()
        root_node = self.root.add(os.path.basename(path), data=path)
        self.populate_tree(root_node, path)
        root_node.expand()
        self.expand_all_nodes(root_node)

    def populate_tree(self, parent_node, path):
        """Populate the tree with directories and files."""
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    child_node = parent_node.add(item, data=item_path)
                    self.populate_tree(child_node, item_path)
                else:
                    parent_node.add_leaf(item, data=item_path)
        except PermissionError:
            pass  # Ignore inaccessible directories

    def expand_all_nodes(self, node):
        """Recursively expand all nodes in the tree."""
        node.expand()
        for child in node.children:
            child.expand()
            self.expand_all_nodes(child)

    def refresh_tree(self):
        """Rebuild the tree when changes occur."""
        print("[DEBUG] Refreshing directory tree")  # ✅ Check if it refreshes
        self.build_tree(self.path)

    def on_node_selected(self, event):
        """Handle file selection and update the code preview."""
        file_path = event.node.data
        print(f"[DEBUG] File selected: {file_path}")  # ✅ Check if clicking a file works
        if os.path.isfile(file_path):
            self.app.show_file_content(file_path)  # Calls `CodeViewer.update_content()`


### 📌 CODE VIEWER (Now Includes Debugging Prints)
class CodeViewer(ScrollView):
    """Scrollable widget to display syntax-highlighted code."""

    def on_mount(self):
        """Ensure a Static widget exists for updating."""
        print("[DEBUG] CodeViewer mounted")  # ✅ Check if it initializes
        self.code_display = Static(id="code", expand=True)
        self.mount(self.code_display)  # ✅ Ensure it's inside `ScrollView`

    def update_content(self, file_path):
        """Update the content of the code viewer when a file is clicked."""
        print(f"[DEBUG] Updating content for: {file_path}")  # ✅ Check if function runs
        self.code_display.update(f"[yellow]Loading {file_path}...[/yellow]")  # Show loading

        try:
            syntax = Syntax.from_path(
                file_path,
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
            print("[DEBUG] Successfully loaded syntax")  # ✅ Check if Syntax works
            self.code_display.update(syntax)  # ✅ Correct way to update content inside ScrollView

        except Exception as e:
            print(f"[ERROR] Failed to load file: {e}")  # ✅ Show error if Syntax fails
            self.code_display.update(Traceback(theme="github-dark", width=None))  # Show error


### 📌 DIRECTORY WATCHER (Auto-refreshes file list)
class DirectoryWatcher(FileSystemEventHandler):
    """Watches a directory and notifies the app when changes occur."""
    def __init__(self, app):
        super().__init__()
        self.app = app

    def on_any_event(self, event):
        """Notify the app to refresh the tree when a file event occurs."""
        print("[DEBUG] File change detected")  # ✅ Confirm if this runs
        self.app.call_from_thread(self.app.refresh_tree)


### 📌 MAIN APPLICATION (Fix for `ScrollView`)
class CodeBrowserApp(App):
    """Main application with custom directory tree and code viewer."""

    CSS_PATH = "code_browser.tcss"  # Load the `.tcss` file for styling
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()
        with Horizontal():
            yield DirectoryTree("Directory", id="tree-view")  # ✅ Your Custom Tree
            with VerticalScroll(id="code-view"):
                yield CodeViewer()  # ✅ Uses ScrollView correctly
        yield Footer()

    def refresh_tree(self):
        """Refresh the directory tree when changes occur."""
        print("[DEBUG] App refresh_tree() called")  # ✅ Ensure this runs
        tree = self.query_one(DirectoryTree)
        tree.refresh_tree()

    def show_file_content(self, file_path):
        """Show the selected file's contents in the code viewer."""
        print(f"[DEBUG] App.show_file_content({file_path}) called")  # ✅ Ensure it's triggered
        viewer = self.query_one(CodeViewer)
        viewer.update_content(file_path)

    def watch_directory(self):
        """Run the watchdog observer in a separate thread."""
        event_handler = DirectoryWatcher(self)
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIR, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def on_mount(self):
        """Start watching the directory when the app mounts."""
        print("[DEBUG] App mounted")  # ✅ Confirm app starts
        threading.Thread(target=self.watch_directory, daemon=True).start()


if __name__ == "__main__":
    CodeBrowserApp().run()
