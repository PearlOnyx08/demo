from __future__ import annotations

from functools import partial
from pathlib import Path
import os
from webbrowser import open as open_url
import asyncio
from rich.syntax import Syntax
from textual.timer import Timer
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Paste
from textual.screen import Screen
from textual.widgets import Footer, TabbedContent, TabPane, Markdown, Static, Select, Button, ProgressBar, LoadingIndicator
from textual.widgets import RadioSet, RadioButton, Label
from .. import __version__
from ..data import load_config, load_history, save_config, save_history
from ..dialogs import ErrorDialog, HelpDialog, InformationDialog
from ..utility import is_likely_url, maybe_markdown
from ..utility.advertising import (
    APPLICATION_TITLE,
    ORGANISATION_TITLE,
    TEXTUAL_URL,
)
from ..widgets import Navigation, Omnibox, Viewer
from ..widgets.navigation_panes import LocalFiles


class Main(Screen[None]):
    DEFAULT_CSS = """
    .focusable { border: blank; }
    .focusable:focus { border: heavy $accent !important; }
    """

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Quit"),
        Binding("ctrl+n", "navigation", "Navigation"),
    ]

    def __init__(self, initial_location: str | None = None):
        super().__init__()
        self._initial_location = initial_location
        self.selected_language = "C++"  # Default language
        self.files_in_selected_dir: list[Path] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Navigation()
            with TabbedContent(id="main-tabs"):
                with TabPane("README", id="readme-tab"):
                    yield Viewer(id="main-viewer", classes="focusable")

                with TabPane("Unit Tests", id="unit-tests-tab"):
                    with Vertical():
                        yield Viewer(id="unit-test-viewer", classes="focusable")
                        yield Label("Select a source file:", id="source-label")
                        yield Select(options=[], id="source-select")
                        yield Label("Select a header file:", id="header-label")
                        yield Select(options=[], id="header-select")
                        yield Label("Code Language", id="code-lang-label")
                        yield RadioSet(
                            RadioButton("C++", id="lang-cpp", value=True),
                            id="code-lang-radios"
                        )
                        yield Button("Generate Unit Test", id="generate-button")
                        yield Button("Reset", id="reset-button")
                        yield LoadingIndicator(id="spinner")
                        yield ProgressBar(total=100, id="progress-bar", show_percentage=True)

                with TabPane("Code Translation", id="translation-tab"):
                    with Vertical():
                        yield Viewer(id="translation-viewer", classes="focusable")
                        yield Static("Translation options placeholder")

        yield Footer()

    async def on_mount(self) -> None:
        # Load README on mount
        history = load_history()
        viewer = self.query_one("#main-viewer", Viewer)

        if self._initial_location:
            viewer.visit(Path(self._initial_location), remember=False)
        elif history:
            viewer.load_history(history)
            viewer.visit(history[-1], remember=False)

        # Defer setting the language and updating visibility until DOM is ready
        def after_mount():
            self.query_one("#code-lang-radios", RadioSet).pressed = "C++"
            self.selected_language = "C++"
            self._update_visibility()
            self.query_one("#spinner", LoadingIndicator).display = False

        self.call_after_refresh(after_mount)



    def _update_visibility(self) -> None:
        is_cpp = self.selected_language == "C++"

        header_label = self.query_one("#header-label", Label)
        header_select = self.query_one("#header-select", Select)
        source_label = self.query_one("#source-label", Label)
        source_select = self.query_one("#source-select", Select)

        header_label.display = is_cpp
        header_select.display = is_cpp

        # Always visible
        source_label.display = True
        source_select.display = True

        # ✅ Force layout refresh for affected widgets
        header_label.refresh(layout=True)
        header_select.refresh(layout=True)
        source_label.refresh(layout=True)
        source_select.refresh(layout=True)


    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.selected_language = event.pressed.label
        self._update_visibility()
    
    def on_local_files_goto(self, event: LocalFiles.Goto) -> None:
        file_path = event.location
        active_tab = self.query_one("#main-tabs").active

        viewer_id = {
            "readme-tab": "main-viewer",
            "unit-tests-tab": "unit-test-viewer",
            "translation-tab": "translation-viewer",
        }.get(active_tab, "main-viewer")

        viewer = self.query_one(f"#{viewer_id}", Viewer)

        if file_path.suffix in {".md", ".markdown"}:
            viewer.visit_markdown_file(file_path)
        elif file_path.suffix in {".txt"}:
            viewer.show_text(file_path.read_text(encoding="utf-8"))
        elif file_path.suffix in {".py", ".js", ".cpp", ".html", ".json", ".xml", ".yaml", ".css", ".h"}:
            content = file_path.read_text(encoding="utf-8")
            syntax = Syntax(content, file_path.suffix.lstrip("."), theme="monokai", line_numbers=True)
            viewer.show_syntax(syntax)
        else:
            os.system(f"xdg-open {file_path}")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        selected_dir = event.path
        if selected_dir.is_dir():
            all_files = list(selected_dir.glob("*.*"))
            py_cpp_files = [f for f in all_files if f.suffix in [".py", ".cpp", ".c", ".h"]]
            header_files = [f for f in all_files if f.suffix in [".h", ".py", ".hpp"]]

            self.query_one("#source-select", Select).set_options(
                [(f.name, str(f)) for f in py_cpp_files]
            )
            self.query_one("#header-select", Select).set_options(
                [(f.name, str(f)) for f in header_files]
            )

            self.query_one("#source-select", Select).clear()
            self.query_one("#header-select", Select).clear()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value:
            file_path = Path(event.value)
            print(f"[API PLACEHOLDER] Would send file path to API: {file_path}")

    def action_navigation(self) -> None:
        self.query_one(Navigation).toggle()

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        href = event.href
        if is_likely_url(href):
            open_url(href)
        else:
            path = Path(href)
            if path.exists():
                self.query_one("#main-viewer", Viewer).visit(path)
            else:
                self.app.push_screen(ErrorDialog("Link Error", f"Cannot open link: {href}"))

    def action_help(self) -> None:
        self.app.push_screen(HelpDialog())

    def action_about(self) -> None:
        self.app.push_screen(
            InformationDialog(
                f"{APPLICATION_TITLE} v{__version__}",
                f"Built with Textual by {ORGANISATION_TITLE}\n{TEXTUAL_URL}",
            )
        )

    def action_toggle_theme(self) -> None:
        config = load_config()
        config.light_mode = not config.light_mode
        save_config(config)
        self.app.dark = not config.light_mode
        

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "generate-button":
            spinner = self.query_one("#spinner")
            progress_bar = self.query_one("#progress-bar", ProgressBar)

            # Show the spinner and reset progress
            spinner.display = True
            progress_bar.progress = 0

            # Placeholder for API call or async work
            for step in range(1, 11):  # Simulated steps (10%)
                await asyncio.sleep(0.1)  # Simulated delay
                progress_bar.progress = step * 10

            # Hide the spinner at the end
            spinner.display = False

            print("[API PLACEHOLDER] Unit test generation complete")
            viewer = self.query_one("#unit-test-viewer", Viewer)
            file_path = Path("/home/spenser/test.cpp")

            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                syntax = Syntax(content, "cpp", theme="monokai", line_numbers=True)
                viewer.show_syntax(syntax)
            else:
                viewer.show_text("Generated unit test file not found.")

        elif event.button.id == "reset-button":
            self.selected_language = "C++"
            self.query_one("#code-lang-radios", RadioSet).pressed = "C++"
            self.query_one("#source-select", Select).clear()
            self.query_one("#header-select", Select).clear()
            self.query_one("#progress-bar", ProgressBar).progress = 0
            self.query_one("#spinner").display = False
            viewer = self.query_one("#unit-test-viewer", Viewer)
            viewer.show_text("")  # Clear code


    def _start_unit_test_generation(self):
        self.query_one("#spinner", LoadingIndicator).visible = True
        self.query_one("#progress-bar", ProgressBar).update(0)

        # Simulate async API call
        self.set_interval(0.05, self._simulate_progress, name="progress_timer")

        # Fake API delay, finish after 3 seconds
        self.set_timer(3.0, self._on_generation_complete)

    def _simulate_progress(self):
        progress = self.query_one("#progress-bar", ProgressBar)
        if progress.value < 95:
            progress.advance(2)
        else:
            self.remove_timer("progress_timer")

    def _on_generation_complete(self):
        self.query_one("#spinner", LoadingIndicator).visible = False
        self.query_one("#progress-bar", ProgressBar).update(100)
        print("[API] Unit test generated!")
        
    def _reset_unit_test_tab(self) -> None:
        # Reset dropdowns
        self.query_one("#source-select", Select).clear()
        self.query_one("#source-select", Select).options = []

        self.query_one("#header-select", Select).clear()
        self.query_one("#header-select", Select).options = []

        # Reset language to default C++
        self.query_one("#code-lang-radios", RadioSet).pressed = "C++"
        self.selected_language = "C++"
        self._update_visibility()

        # Reset progress bar and spinner
        self.query_one("#progress-bar").progress = 0
        self.query_one("#spinner").display = False
