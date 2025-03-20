from textual.app import App, ComposeResult
from textual.widgets import Tree
from textual.reactive import reactive
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import threading

WATCH_DIR = "your_directory_path"  # Change this to the directory you want to watch

class DirectoryTree(Tree):
    """Tree widget that displays a directory structure."""
    path = reactive(WATCH_DIR)

    def on_mount(self):
        """Build the tree when the widget mounts."""
        self.build_tree(self.path)

    def build_tree(self, path):
        """Recursively add directories and files to the tree."""
        self.clear()
        root_node = self.root.add(os.path.basename(path), data=path)
        self.populate_tree(root_node, path)
        root_node.expand()

    def populate_tree(self, parent_node, path):
        """Populate the tree with the contents of the directory."""
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    child_node = parent_node.add(item, data=item_path)
                    self.populate_tree(child_node, item_path)
                else:
                    parent_node.add(item, data=item_path)
        except PermissionError:
            pass  # Ignore inaccessible directories

    def refresh_tree(self):
        """Rebuild the tree when changes occur."""
        self.build_tree(self.path)
        self.refresh()


class DirectoryWatcher(FileSystemEventHandler):
    """Watches a directory and notifies the app when changes occur."""
    def __init__(self, app):
        super().__init__()
        self.app = app

    def on_any_event(self, event):
        """Notify the app to refresh the tree when a file event occurs."""
        self.app.call_from_thread(self.app.refresh_tree)


class DirectoryTreeApp(App):
    CSS = """
    Tree {
        height: 100%;
        width: 100%;
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the directory tree widget."""
        yield DirectoryTree("Directory")  # No direct assignment to self.tree

    def refresh_tree(self):
        """Refresh the directory tree when changes occur."""
        tree = self.query_one(DirectoryTree)  # Dynamically fetch the tree
        tree.refresh_tree()

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
