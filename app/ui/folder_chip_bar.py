"""
Folder chip bar component for filtering media by parent folders.
"""

from pathlib import Path
from typing import Callable, Dict, List, Set

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QScrollArea, QWidget

from core.styles import theme


class FolderChipBar(QWidget):
    """Chip bar showing parent folders with toggle functionality."""

    # Signal emitted when folder visibility is toggled
    folder_toggled = Signal(str, bool)  # folder_path, is_visible

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_states: Dict[str, bool] = {}  # folder_path -> is_visible
        self.folder_buttons: Dict[str, QPushButton] = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI layout."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Scroll area for chips
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setMaximumHeight(28)
        self.scroll_area.setMinimumHeight(28)

        # Container widget for chips
        self.chip_container = QWidget()
        self.chip_layout = QHBoxLayout(self.chip_container)
        self.chip_layout.setContentsMargins(1, 1, 1, 1)
        self.chip_layout.setSpacing(12)
        self.chip_layout.addStretch()  # Push chips to the left

        self.scroll_area.setWidget(self.chip_container)
        layout.addWidget(self.scroll_area)

    def update_folders(self, media_paths: List[Path]):
        """Update the folder chips based on media paths."""
        # Extract unique parent folders
        folders = self._extract_parent_folders(media_paths)

        # Remove chips for folders that no longer exist
        self._remove_old_chips(folders)

        # Add new chips
        self._add_new_chips(folders)

        # Update existing chips
        self._update_existing_chips(folders)

    def _extract_parent_folders(self, media_paths: List[Path]) -> Set[str]:
        """Extract unique parent folder paths from media paths."""
        folders = set()
        for path in media_paths:
            if path.exists():
                parent = path.parent
                if parent.exists():
                    folders.add(str(parent))
        return folders

    def _remove_old_chips(self, current_folders: Set[str]):
        """Remove chips for folders that no longer exist."""
        folders_to_remove = set(self.folder_buttons.keys()) - current_folders
        for folder_path in folders_to_remove:
            if folder_path in self.folder_buttons:
                button = self.folder_buttons.pop(folder_path)
                self.chip_layout.removeWidget(button)
                button.deleteLater()
            if folder_path in self.folder_states:
                del self.folder_states[folder_path]

    def _add_new_chips(self, current_folders: Set[str]):
        """Add new chips for folders that don't exist yet."""
        new_folders = current_folders - set(self.folder_buttons.keys())
        for folder_path in new_folders:
            self._create_folder_chip(folder_path)

    def _update_existing_chips(self, current_folders: Set[str]):
        """Update existing chips (refresh styling, etc.)."""
        for folder_path in current_folders:
            if folder_path in self.folder_buttons:
                self._update_chip_styling(folder_path)

    def _create_folder_chip(self, folder_path: str):
        """Create a new folder chip button."""
        folder_name = self._get_display_name(folder_path)

        button = QPushButton(folder_name)
        button.setCheckable(True)
        button.setChecked(True)  # Default to visible
        button.setToolTip(f"Toggle visibility for: {folder_path}")

        # Store references
        self.folder_buttons[folder_path] = button
        self.folder_states[folder_path] = True

        # Connect signal
        button.toggled.connect(
            lambda checked, path=folder_path: self._on_chip_toggled(path, checked)
        )

        # Style the button
        self._update_chip_styling(folder_path)

        # Add to layout (before the stretch)
        self.chip_layout.insertWidget(self.chip_layout.count() - 1, button)

    def _get_display_name(self, folder_path: str) -> str:
        """Get display name for folder (truncated to 15 chars)."""
        folder_name = Path(folder_path).name
        if len(folder_name) > 15:
            return folder_name[:12] + "..."
        return folder_name

    def _update_chip_styling(self, folder_path: str):
        """Update the styling of a folder chip."""
        if folder_path not in self.folder_buttons:
            return

        button = self.folder_buttons[folder_path]
        is_visible = self.folder_states.get(folder_path, True)

        if is_visible:
            # Visible state - green/active styling
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {theme.primary};
                    color: white;
                    border: 1px solid {theme.primary};
                    border-radius: 10px;
                    padding: 2px 6px;
                    font-size: 10px;
                    font-weight: 500;
                    min-width: 20px;
                    max-width: 80px;
                }}
                QPushButton:hover {{
                    background: {theme.primary_hover};
                    border-color: {theme.primary_hover};
                }}
                QPushButton:pressed {{
                    background: {theme.primary_hover};
                }}
            """
            )
        else:
            # Hidden state - gray/inactive styling
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {theme.background_elevated};
                    color: {theme.text_secondary};
                    border: 1px solid {theme.border};
                    border-radius: 10px;
                    padding: 2px 6px;
                    font-size: 10px;
                    font-weight: 500;
                    min-width: 20px;
                    max-width: 80px;
                }}
                QPushButton:hover {{
                    background: {theme.background_secondary};
                    border-color: {theme.text_secondary};
                }}
                QPushButton:pressed {{
                    background: {theme.background_secondary};
                }}
            """
            )

    def _on_chip_toggled(self, folder_path: str, is_visible: bool):
        """Handle chip toggle event."""
        self.folder_states[folder_path] = is_visible
        self._update_chip_styling(folder_path)
        self.folder_toggled.emit(folder_path, is_visible)

    def get_visible_folders(self) -> Set[str]:
        """Get set of currently visible folder paths."""
        return {path for path, visible in self.folder_states.items() if visible}

    def get_hidden_folders(self) -> Set[str]:
        """Get set of currently hidden folder paths."""
        return {path for path, visible in self.folder_states.items() if not visible}

    def set_folder_visibility(self, folder_path: str, is_visible: bool):
        """Programmatically set folder visibility."""
        if folder_path in self.folder_buttons:
            button = self.folder_buttons[folder_path]
            button.setChecked(is_visible)
            self.folder_states[folder_path] = is_visible
            self._update_chip_styling(folder_path)

    def show_all_folders(self):
        """Show all folders."""
        for folder_path in self.folder_buttons:
            self.set_folder_visibility(folder_path, True)

    def hide_all_folders(self):
        """Hide all folders."""
        for folder_path in self.folder_buttons:
            self.set_folder_visibility(folder_path, False)

    def clear(self):
        """Clear all folder chips."""
        for button in self.folder_buttons.values():
            self.chip_layout.removeWidget(button)
            button.deleteLater()
        self.folder_buttons.clear()
        self.folder_states.clear()
