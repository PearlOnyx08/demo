from textual.app import App, ComposeResult
from textual.widgets import Tree, Log, Footer, Header
from textual.containers import Vertical
from textual.reactive import reactive
import os

WATCH_DIR = "./"  # Change this if needed


class DebugConsole(Log):
    """Debug console that logs events inside the UI."""

    def on_mount(self):
        """Redirects print() output to this console."""
        self.write("[DEBUG] Debug console started...")
        import sys
        sys.stdout = self  # Redirect stdout to this widget

    def write(self, message):
        """Capture and display print output."""
        self.write_line(message.rstrip())


class DirectoryTree(Tree):
    """Custom directory tree widget for testing."""

    path = reactive(WATCH_DIR)

    def on_mount(self):
        """Print debug log when the tree mounts."""
        print("[DEBUG] DirectoryTree mounted")
        self.build_tree(self.path)
    
    def build_tree(self, path):
        """Populate the tree with directories and files."""
        print(f"[DEBUG] Building tree for: {path}")
        self.clear()
        root_node = self.root.add(os.path.basename(path), data=path)
        try:
            for item in sorted(os.listdir(path)):
                root_node.add_leaf(item, data=os.path.join(path, item))
        except PermissionError:
            pass
        root_node.expand()

    def on_node_selected(self, event):
        """Debugging: Log when a file or folder is clicked."""
        file_path = event.node.data
        print(f"[DEBUG] Node selected: {file_path}")  # This should appear in debug console


class SimpleDebugApp(App):
    """A minimal app to debug the tree widget."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Compose layout with only a tree and debug log."""
        yield Header()
        with Vertical():
            yield DirectoryTree("Directory", id="tree-view")
            yield DebugConsole(id="debug-log")  # Debug log window
        yield Footer()


if __name__ == "__main__":
    SimpleDebugApp().run()
