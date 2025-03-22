from textual.app import App, ComposeResult
from textual.widgets import Tree, Static, ScrollView
from textual.reactive import reactive
from textual.containers import Horizontal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from syntax import Syntax  # Importing Syntax for code highlighting
import os
import time
import threading

WATCH_DIR = "your_directory_path"  # Change this to your directory


### 📌 CODE PREVIEW PANEL (Now Fully Works!)
class CodeViewer(ScrollView):
    """Scrollable widget to display syntax-highlighted code."""

    def update_content(self, file_path):
        """Update the content of the code viewer when a file is clicked."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            file_extension = file_path.split(".")[-1]  # Get file type
            syntax = Syntax(code, file_extension, theme="monokai", line_numbers=True)

            # Clear old content & update the viewer
            self.clear()
            self.mount(Static(syntax))  # Ensure it properly renders in ScrollView

        except Exception as e:
            self.clear()
            self.mount(Static(f"[red]Error loading file: {e}[/red]"))


### 📌 DIRECTORY TREE COMPONENT (Now Calls Code Viewer Correctly!)
class DirectoryTree(Tree):
    """Tree widget that displays a directory structure."""
    path = reactive(WATCH_DIR)

    def on_mount(self):
        """Build the tree when the widget mounts."""
        self.build_tree(self.path)
        self.expand_all_nodes(self.root)  

    def build_tree(self, path):
        """Recursively add directories and files to the tree."""
        self.clear()
        root_node = self.root.add(os.path.basename(path), data=path)
        self.populate_tree(root_node, path)
        root_node.expand()
        self.expand_all_nodes(root_node)  

    def populate_tree(self, parent_node, path):
        """Populate the tree with the contents of the directory."""
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
        self.build_tree(self.path)

    def on_node_selected(self, event):
        """Handle file selection and update inline code preview."""
        file_path = event.node.data
        if os.path.isfile(file_path):  
            self.app.show_file_content(file_path)  # Calls `CodeViewer.update_content()`


### 📌 DIRECTORY WATCHER (Auto-refreshes file list)
class DirectoryWatcher(FileSystemEventHandler):
    """Watches a directory and notifies the app when changes occur."""
    def __init__(self, app):
        super().__init__()
        self.app = app

    def on_any_event(self, event):
        """Notify the app to refresh the tree when a file event occurs."""
        self.app.call_from_thread(self.app.refresh_tree)


### 📌 MAIN APPLICATION (Now Works Correctly!)
class DirectoryTreeApp(App):
    """Main application with directory tree and inline code viewer."""

    CSS = """
    Horizontal {
        height: 100%;
        width: 100%;
    }
    Tree {
        width: 30%;
        border: solid green;
    }
    ScrollView {
        width: 70%;
        border: solid blue;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        with Horizontal():
            yield DirectoryTree("Directory")  # Left side: File tree
            yield CodeViewer()  # Right side: Code viewer

    def refresh_tree(self):
        """Refresh the directory tree when changes occur."""
        tree = self.query_one(DirectoryTree)
        tree.refresh_tree()

    def show_file_content(self, file_path):
        """Show the selected file's contents in the code viewer."""
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
        threading.Thread(target=self.watch_directory, daemon=True).start()


if __name__ == "__main__":
    DirectoryTreeApp().run()
