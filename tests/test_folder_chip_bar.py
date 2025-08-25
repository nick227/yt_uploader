"""
Tests for the FolderChipBar component.
"""

import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from unittest.mock import Mock

from app.ui.folder_chip_bar import FolderChipBar


@pytest.fixture
def app(qtbot):
    """Create QApplication instance for testing."""
    return qtbot


@pytest.fixture
def temp_dir():
    """Create temporary directory with test structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test folder structure
        folder1 = temp_path / "music"
        folder2 = temp_path / "videos"
        folder3 = temp_path / "music" / "rock"  # Nested folder with same name
        folder4 = temp_path / "very_long_folder_name_that_needs_truncation"

        folder1.mkdir()
        folder2.mkdir()
        folder3.mkdir(parents=True)
        folder4.mkdir()

        # Create test media files
        (folder1 / "song1.mp3").write_text("fake audio")
        (folder1 / "song2.mp3").write_text("fake audio")
        (folder2 / "video1.mp4").write_text("fake video")
        (folder3 / "song3.mp3").write_text("fake audio")
        (folder4 / "test.mp3").write_text("fake audio")

        yield temp_path


class TestFolderChipBar:
    """Test cases for FolderChipBar component."""

    def test_init(self, app):
        """Test FolderChipBar initialization."""
        chip_bar = FolderChipBar()

        assert chip_bar.folder_states == {}
        assert chip_bar.folder_buttons == {}
        assert chip_bar.scroll_area is not None
        assert chip_bar.chip_container is not None

    def test_extract_parent_folders(self, app, temp_dir):
        """Test parent folder extraction from media paths."""
        chip_bar = FolderChipBar()

        media_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "videos" / "video1.mp4",
            temp_dir / "music" / "rock" / "song3.mp3",
        ]

        folders = chip_bar._extract_parent_folders(media_paths)

        expected_folders = {
            str(temp_dir / "music"),
            str(temp_dir / "videos"),
            str(temp_dir / "music" / "rock"),
        }

        assert folders == expected_folders

    def test_extract_parent_folders_with_nonexistent_files(self, app):
        """Test parent folder extraction with nonexistent files."""
        chip_bar = FolderChipBar()

        media_paths = [
            Path("/nonexistent/file1.mp3"),
            Path("/another/nonexistent/file2.mp4"),
        ]

        folders = chip_bar._extract_parent_folders(media_paths)

        assert folders == set()

    def test_get_display_name_normal(self, app):
        """Test display name generation for normal folder names."""
        chip_bar = FolderChipBar()

        folder_path = "/path/to/music"
        display_name = chip_bar._get_display_name(folder_path)

        assert display_name == "music"

    def test_get_display_name_truncation(self, app):
        """Test display name truncation for long folder names."""
        chip_bar = FolderChipBar()

        folder_path = "/path/to/very_long_folder_name_that_exceeds_limit"
        display_name = chip_bar._get_display_name(folder_path)

        assert len(display_name) <= 15
        assert display_name.endswith("...")
        assert display_name.startswith("very_long_fo")

    def test_create_folder_chip(self, app):
        """Test folder chip creation."""
        chip_bar = FolderChipBar()

        folder_path = "/test/path"
        chip_bar._create_folder_chip(folder_path)

        assert folder_path in chip_bar.folder_buttons
        assert folder_path in chip_bar.folder_states
        assert chip_bar.folder_states[folder_path] is True

        button = chip_bar.folder_buttons[folder_path]
        assert button.text() == "path"
        assert button.isChecked() is True

    def test_update_folders_add_new(self, app, temp_dir):
        """Test updating folders with new folders."""
        chip_bar = FolderChipBar()

        media_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "videos" / "video1.mp4",
        ]

        chip_bar.update_folders(media_paths)

        expected_folders = {
            str(temp_dir / "music"),
            str(temp_dir / "videos"),
        }

        assert set(chip_bar.folder_buttons.keys()) == expected_folders
        assert set(chip_bar.folder_states.keys()) == expected_folders

    def test_update_folders_remove_old(self, app, temp_dir):
        """Test updating folders removes old ones."""
        chip_bar = FolderChipBar()

        # Add initial folders
        initial_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "videos" / "video1.mp4",
        ]
        chip_bar.update_folders(initial_paths)

        # Update with different folders
        new_paths = [
            temp_dir / "music" / "rock" / "song3.mp3",
        ]
        chip_bar.update_folders(new_paths)

        expected_folders = {str(temp_dir / "music" / "rock")}

        assert set(chip_bar.folder_buttons.keys()) == expected_folders
        assert set(chip_bar.folder_states.keys()) == expected_folders

    def test_folder_toggle_signal(self, app, temp_dir):
        """Test folder toggle signal emission."""
        chip_bar = FolderChipBar()

        # Mock signal handler
        mock_handler = Mock()
        chip_bar.folder_toggled.connect(mock_handler)

        media_paths = [temp_dir / "music" / "song1.mp3"]
        chip_bar.update_folders(media_paths)

        folder_path = str(temp_dir / "music")
        button = chip_bar.folder_buttons[folder_path]

        # Toggle the button
        button.setChecked(False)

        # Check signal was emitted
        mock_handler.assert_called_once_with(folder_path, False)

    def test_get_visible_folders(self, app, temp_dir):
        """Test getting visible folders."""
        chip_bar = FolderChipBar()

        media_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "videos" / "video1.mp4",
        ]
        chip_bar.update_folders(media_paths)

        # All folders should be visible by default
        visible_folders = chip_bar.get_visible_folders()
        expected_folders = {
            str(temp_dir / "music"),
            str(temp_dir / "videos"),
        }

        assert visible_folders == expected_folders

    def test_get_hidden_folders(self, app, temp_dir):
        """Test getting hidden folders."""
        chip_bar = FolderChipBar()

        media_paths = [temp_dir / "music" / "song1.mp3"]
        chip_bar.update_folders(media_paths)

        folder_path = str(temp_dir / "music")

        # Initially no hidden folders
        assert chip_bar.get_hidden_folders() == set()

        # Hide a folder
        chip_bar.set_folder_visibility(folder_path, False)

        assert chip_bar.get_hidden_folders() == {folder_path}

    def test_set_folder_visibility(self, app, temp_dir):
        """Test programmatically setting folder visibility."""
        chip_bar = FolderChipBar()

        media_paths = [temp_dir / "music" / "song1.mp3"]
        chip_bar.update_folders(media_paths)

        folder_path = str(temp_dir / "music")
        button = chip_bar.folder_buttons[folder_path]

        # Set to hidden
        chip_bar.set_folder_visibility(folder_path, False)

        assert button.isChecked() is False
        assert chip_bar.folder_states[folder_path] is False

        # Set to visible
        chip_bar.set_folder_visibility(folder_path, True)

        assert button.isChecked() is True
        assert chip_bar.folder_states[folder_path] is True

    def test_show_all_folders(self, app, temp_dir):
        """Test showing all folders."""
        chip_bar = FolderChipBar()

        media_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "videos" / "video1.mp4",
        ]
        chip_bar.update_folders(media_paths)

        # Hide all folders first
        for folder_path in chip_bar.folder_buttons:
            chip_bar.set_folder_visibility(folder_path, False)

        assert len(chip_bar.get_visible_folders()) == 0

        # Show all folders
        chip_bar.show_all_folders()

        expected_folders = {
            str(temp_dir / "music"),
            str(temp_dir / "videos"),
        }
        assert chip_bar.get_visible_folders() == expected_folders

    def test_hide_all_folders(self, app, temp_dir):
        """Test hiding all folders."""
        chip_bar = FolderChipBar()

        media_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "videos" / "video1.mp4",
        ]
        chip_bar.update_folders(media_paths)

        # All folders should be visible initially
        expected_folders = {
            str(temp_dir / "music"),
            str(temp_dir / "videos"),
        }
        assert chip_bar.get_visible_folders() == expected_folders

        # Hide all folders
        chip_bar.hide_all_folders()

        assert len(chip_bar.get_visible_folders()) == 0
        assert chip_bar.get_hidden_folders() == expected_folders

    def test_clear(self, app, temp_dir):
        """Test clearing all folder chips."""
        chip_bar = FolderChipBar()

        media_paths = [temp_dir / "music" / "song1.mp3"]
        chip_bar.update_folders(media_paths)

        assert len(chip_bar.folder_buttons) > 0
        assert len(chip_bar.folder_states) > 0

        chip_bar.clear()

        assert len(chip_bar.folder_buttons) == 0
        assert len(chip_bar.folder_states) == 0

    def test_chip_styling_visible(self, app, temp_dir):
        """Test chip styling for visible state."""
        chip_bar = FolderChipBar()

        media_paths = [temp_dir / "music" / "song1.mp3"]
        chip_bar.update_folders(media_paths)

        folder_path = str(temp_dir / "music")
        button = chip_bar.folder_buttons[folder_path]

        # Check that visible chips have the correct styling
        stylesheet = button.styleSheet()
        assert "background:" in stylesheet
        assert "color: white" in stylesheet

    def test_chip_styling_hidden(self, app, temp_dir):
        """Test chip styling for hidden state."""
        chip_bar = FolderChipBar()

        media_paths = [temp_dir / "music" / "song1.mp3"]
        chip_bar.update_folders(media_paths)

        folder_path = str(temp_dir / "music")

        # Hide the folder
        chip_bar.set_folder_visibility(folder_path, False)

        button = chip_bar.folder_buttons[folder_path]
        stylesheet = button.styleSheet()

        # Check that hidden chips have the correct styling
        assert "background:" in stylesheet
        assert "color:" in stylesheet  # Should have secondary text color

    def test_nested_folders_same_name(self, app, temp_dir):
        """Test handling of nested folders with same names."""
        chip_bar = FolderChipBar()

        media_paths = [
            temp_dir / "music" / "song1.mp3",
            temp_dir / "music" / "rock" / "song3.mp3",
        ]
        chip_bar.update_folders(media_paths)

        # Should have separate chips for each folder level
        expected_folders = {
            str(temp_dir / "music"),
            str(temp_dir / "music" / "rock"),
        }

        assert set(chip_bar.folder_buttons.keys()) == expected_folders

        # Both should have the same display name "music" but different paths
        music_button = chip_bar.folder_buttons[str(temp_dir / "music")]
        rock_button = chip_bar.folder_buttons[str(temp_dir / "music" / "rock")]

        assert music_button.text() == "music"
        assert rock_button.text() == "rock"
