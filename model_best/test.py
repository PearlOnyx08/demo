from textual.app import App, ComposeResult
from textual.widgets import Tree, Log, Footer, Header
from textual.containers import Vertical
from textual.reactive import reactive
from textual.events import Click
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
    """Custom directory tree widget for debugging."""

    path = reactive(WATCH_DIR)

    def on_mount(self):
        """Force the tree to load and expand."""
        print("[DEBUG] DirectoryTree mounted")
        self.load_directory(self.path)
        self.expand_all_nodes(self.root)

    def load_directory(self, path):
        """Manually build the tree to ensure it loads files."""
        print(f"[DEBUG] Loading directory: {path}")
        self.clear()
        root_node = self.root.add(os.path.basename(path), data=path)
        self.populate_tree(root_node, path)
        root_node.expand()
    
    def populate_tree(self, parent_node, path):
        """Manually populate the tree with directories and files."""
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    parent_node.add(item, data=item_path)  # Folder
                else:
                    parent_node.add_leaf(item, data=item_path)  # File
        except PermissionError:
            pass

    def on_node_selected(self, event):
        """Log when a node is selected."""
        print(f"[DEBUG] Node selected: {event.node.data}")  # ✅ Should always appear

    def on_click(self, event: Click):
        """Manually detect clicks on tree elements."""
        print("[DEBUG] Tree clicked")  # ✅ Logs any click on the tree
        return super().on_click(event)  # Pass to normal behavior


class SimpleDebugApp(App):
    """Minimal app for debugging the tree widget."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Compose the UI layout with only a tree and debug log."""
        yield Header()
        with Vertical():
            yield DirectoryTree("Directory", id="tree-view")
            yield DebugConsole(id="debug-log")  # Debug log window
        yield Footer()


if __name__ == "__main__":
    SimpleDebugApp().run()

