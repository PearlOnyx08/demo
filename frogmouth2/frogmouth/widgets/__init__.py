"""The major widgets for the application."""

from .navigation import Navigation
from .omnibox import Omnibox
from .viewer import Viewer
from .navigation_panes.local_files import LocalFiles  # ✅ Ensure this is included

__all__ = ["Navigation", "Omnibox", "Viewer"]
