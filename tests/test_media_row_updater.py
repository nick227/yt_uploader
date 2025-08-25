"""
Tests for the MediaRowUpdater component.
"""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QWidget
from unittest.mock import Mock, patch

from app.ui.media_row_updater import MediaRowUpdater


@pytest.fixture
def app(qtbot):
    """Create QApplication instance for testing."""
    return qtbot


@pytest.fixture
def mock_media_row():
    """Create a mock MediaRow widget."""
    row = Mock(spec=QWidget)
    row.path = Path("/test/original/file.mp4")

    # Mock media preview
    row.media_preview = Mock()
    row.media_preview.path = Path("/test/original/file.mp4")
    row.media_preview.media_loaded = True
    row.media_preview.loading_media = False

    # Mock media info widget
    row.media_info = Mock()
    row.media_info.path = Path("/test/original/file.mp4")
    row.media_info._load_media_info = Mock()

    # Mock title
    row.title = Mock()
    row.title.text.return_value = "original"
    row.title.setText = Mock()

    # Mock status update method
    row._update_status_indicators = Mock()

    return row


@pytest.fixture
def mock_root_widget():
    """Create a mock root widget with child widgets."""
    root = Mock(spec=QWidget)

    # Create mock child widgets
    child1 = Mock(spec=QWidget)
    child1.path = Path("/test/folder1/file1.mp4")

    child2 = Mock(spec=QWidget)
    child2.path = Path("/test/folder2/file2.mp4")

    child3 = Mock(spec=QWidget)
    child3.path = Path("/test/folder1/file3.mp4")  # Same folder as child1

    # Mock findChildren to return our mock children
    root.findChildren.return_value = [child1, child2, child3]

    return root


class TestMediaRowUpdater:
    """Test cases for MediaRowUpdater component."""

    def test_update_media_row_for_moved_file_success(self, app, mock_media_row):
        """Test successful media row update for moved file."""
        old_path = Path("/test/original/file.mp4")
        new_path = Path("/test/new/location/file.mp4")

        success = MediaRowUpdater.update_media_row_for_moved_file(
            mock_media_row, old_path, new_path
        )

        assert success is True

        # Check path was updated
        assert mock_media_row.path == new_path

        # Check media preview was updated
        assert mock_media_row.media_preview.path == new_path
        assert mock_media_row.media_preview.media_loaded is False
        assert mock_media_row.media_preview.loading_media is False

        # Check media info was updated
        assert mock_media_row.media_info.path == new_path
        mock_media_row.media_info._load_media_info.assert_called_once()

        # Check status indicators were updated
        mock_media_row._update_status_indicators.assert_called_once()

    def test_update_media_row_for_moved_file_with_title_update(
        self, app, mock_media_row
    ):
        """Test media row update with title update."""
        old_path = Path("/test/original/file.mp4")
        new_path = Path("/test/new/location/renamed_file.mp4")

        # Set title to match original filename
        mock_media_row.title.text.return_value = "file"

        success = MediaRowUpdater.update_media_row_for_moved_file(
            mock_media_row, old_path, new_path
        )

        assert success is True

        # Check title was updated
        mock_media_row.title.setText.assert_called_once_with("renamed_file")

    def test_update_media_row_for_moved_file_no_title_update(self, app, mock_media_row):
        """Test media row update without title update."""
        old_path = Path("/test/original/file.mp4")
        new_path = Path("/test/new/location/renamed_file.mp4")

        # Set title to something different from original filename
        mock_media_row.title.text.return_value = "Custom Title"

        success = MediaRowUpdater.update_media_row_for_moved_file(
            mock_media_row, old_path, new_path
        )

        assert success is True

        # Check title was NOT updated
        mock_media_row.title.setText.assert_not_called()

    def test_update_media_row_for_moved_file_missing_attributes(self, app):
        """Test media row update with missing attributes."""
        # Create minimal mock without all attributes
        minimal_row = Mock(spec=QWidget)
        minimal_row.path = Path("/test/original/file.mp4")

        old_path = Path("/test/original/file.mp4")
        new_path = Path("/test/new/location/file.mp4")

        # Should not raise exception
        success = MediaRowUpdater.update_media_row_for_moved_file(
            minimal_row, old_path, new_path
        )

        assert success is True
        assert minimal_row.path == new_path

    def test_update_media_row_for_moved_file_exception(self, app, mock_media_row):
        """Test media row update with exception."""
        old_path = Path("/test/original/file.mp4")
        new_path = Path("/test/new/location/file.mp4")

        # Make media info update raise an exception
        mock_media_row.media_info._load_media_info.side_effect = Exception("Test error")

        success = MediaRowUpdater.update_media_row_for_moved_file(
            mock_media_row, old_path, new_path
        )

        assert success is False

    def test_find_media_rows_for_file(self, app, mock_root_widget):
        """Test finding media rows for a specific file."""
        target_path = Path("/test/folder1/file1.mp4")

        media_rows = MediaRowUpdater.find_media_rows_for_file(
            mock_root_widget, target_path
        )

        assert len(media_rows) == 1
        assert media_rows[0].path == target_path

    def test_find_media_rows_for_file_multiple_matches(self, app, mock_root_widget):
        """Test finding media rows with multiple matches."""
        target_path = Path("/test/folder1/file1.mp4")

        # Add another child with the same path
        child4 = Mock(spec=QWidget)
        child4.path = target_path
        mock_root_widget.findChildren.return_value.append(child4)

        media_rows = MediaRowUpdater.find_media_rows_for_file(
            mock_root_widget, target_path
        )

        assert len(media_rows) == 2
        assert all(row.path == target_path for row in media_rows)

    def test_find_media_rows_for_file_no_matches(self, app, mock_root_widget):
        """Test finding media rows with no matches."""
        target_path = Path("/test/nonexistent/file.mp4")

        media_rows = MediaRowUpdater.find_media_rows_for_file(
            mock_root_widget, target_path
        )

        assert len(media_rows) == 0

    def test_find_media_rows_for_file_exception(self, app):
        """Test finding media rows with exception."""
        mock_root_widget = Mock(spec=QWidget)
        mock_root_widget.findChildren.side_effect = Exception("Test error")

        target_path = Path("/test/file.mp4")

        media_rows = MediaRowUpdater.find_media_rows_for_file(
            mock_root_widget, target_path
        )

        assert len(media_rows) == 0

    def test_update_all_media_rows_for_moved_file(self, app, mock_root_widget):
        """Test updating all media rows for moved file."""
        old_path = Path("/test/folder1/file1.mp4")
        new_path = Path("/test/new/location/file1.mp4")

        # Mock the update method to return True
        with patch.object(
            MediaRowUpdater, "update_media_row_for_moved_file", return_value=True
        ):
            updated_count = MediaRowUpdater.update_all_media_rows_for_moved_file(
                mock_root_widget, old_path, new_path
            )

            assert updated_count == 1

    def test_update_all_media_rows_for_moved_file_multiple_matches(
        self, app, mock_root_widget
    ):
        """Test updating all media rows with multiple matches."""
        old_path = Path("/test/folder1/file1.mp4")
        new_path = Path("/test/new/location/file1.mp4")

        # Add another child with the same path
        child4 = Mock(spec=QWidget)
        child4.path = old_path
        mock_root_widget.findChildren.return_value.append(child4)

        # Mock the update method to return True
        with patch.object(
            MediaRowUpdater, "update_media_row_for_moved_file", return_value=True
        ):
            updated_count = MediaRowUpdater.update_all_media_rows_for_moved_file(
                mock_root_widget, old_path, new_path
            )

            assert updated_count == 2

    def test_update_all_media_rows_for_moved_file_partial_failure(
        self, app, mock_root_widget
    ):
        """Test updating all media rows with partial failures."""
        old_path = Path("/test/folder1/file1.mp4")
        new_path = Path("/test/new/location/file1.mp4")

        # Add another child with the same path
        child4 = Mock(spec=QWidget)
        child4.path = old_path
        mock_root_widget.findChildren.return_value.append(child4)

        # Mock the update method to return False for one row
        with patch.object(
            MediaRowUpdater,
            "update_media_row_for_moved_file",
            side_effect=[True, False],
        ):
            updated_count = MediaRowUpdater.update_all_media_rows_for_moved_file(
                mock_root_widget, old_path, new_path
            )

            assert updated_count == 1

    def test_update_all_media_rows_for_moved_file_exception(self, app):
        """Test updating all media rows with exception."""
        mock_root_widget = Mock(spec=QWidget)
        mock_root_widget.findChildren.side_effect = Exception("Test error")

        old_path = Path("/test/file.mp4")
        new_path = Path("/test/new/file.mp4")

        updated_count = MediaRowUpdater.update_all_media_rows_for_moved_file(
            mock_root_widget, old_path, new_path
        )

        assert updated_count == 0

    def test_validate_media_row_update_success(self, app, mock_media_row):
        """Test successful media row update validation."""
        new_path = Path("/test/new/location/file.mp4")

        # Create the new file
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text("test content")

        try:
            is_valid = MediaRowUpdater.validate_media_row_update(
                mock_media_row, new_path
            )
            assert is_valid is True
        finally:
            # Cleanup
            if new_path.exists():
                new_path.unlink()
            if new_path.parent.exists():
                new_path.parent.rmdir()

    def test_validate_media_row_update_nonexistent_file(self, app, mock_media_row):
        """Test validation with nonexistent file."""
        new_path = Path("/test/nonexistent/file.mp4")

        is_valid = MediaRowUpdater.validate_media_row_update(mock_media_row, new_path)

        assert is_valid is False

    def test_validate_media_row_update_not_file(self, app, mock_media_row, tmp_path):
        """Test validation with path that is not a file."""
        # Create a directory
        new_path = tmp_path / "directory"
        new_path.mkdir()

        is_valid = MediaRowUpdater.validate_media_row_update(mock_media_row, new_path)

        assert is_valid is False

    def test_validate_media_row_update_empty_file(self, app, mock_media_row, tmp_path):
        """Test validation with empty file."""
        # Create an empty file
        new_path = tmp_path / "empty_file.mp4"
        new_path.touch()

        is_valid = MediaRowUpdater.validate_media_row_update(mock_media_row, new_path)

        assert is_valid is False

    def test_validate_media_row_update_exception(self, app, mock_media_row):
        """Test validation with exception."""
        new_path = Path("/test/file.mp4")

        # Mock stat to raise exception
        with patch.object(Path, "stat", side_effect=Exception("Test error")):
            is_valid = MediaRowUpdater.validate_media_row_update(
                mock_media_row, new_path
            )

            assert is_valid is False
