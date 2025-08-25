"""
Unit tests for the MediaRow UI component.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock, Mock, patch

from app.ui.media_row import MediaRow


@pytest.fixture
def app():
    """Create QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_mp3_file(tmp_path):
    """Create a temporary MP3 file for testing."""
    mp3_file = tmp_path / "test_audio.mp3"
    mp3_file.write_text("fake mp3 content")
    return mp3_file


@pytest.fixture
def temp_mp4_file(tmp_path):
    """Create a temporary MP4 file for testing."""
    mp4_file = tmp_path / "test_video.mp4"
    mp4_file.write_text("fake mp4 content")
    return mp4_file


class TestMediaRow:
    """Test MediaRow UI component."""

    def test_init_mp3_file(self, app, temp_mp3_file):
        """Test MediaRow initialization with MP3 file."""
        media_row = MediaRow(temp_mp3_file)

        assert media_row.path == temp_mp3_file
        assert media_row.is_mp3 is True
        assert media_row.is_mp4 is False
        assert media_row.upload_manager is None

    def test_init_mp4_file(self, app, temp_mp4_file):
        """Test MediaRow initialization with MP4 file."""
        media_row = MediaRow(temp_mp4_file)

        assert media_row.path == temp_mp4_file
        assert media_row.is_mp3 is False
        assert media_row.is_mp4 is True
        assert media_row.upload_manager is None

    def test_init_with_upload_manager(self, app, temp_mp4_file):
        """Test MediaRow initialization with upload manager."""
        mock_upload_manager = Mock()
        media_row = MediaRow(temp_mp4_file, upload_manager=mock_upload_manager)

        assert media_row.upload_manager == mock_upload_manager

    def test_ui_components_created(self, app, temp_mp4_file):
        """Test that all UI components are created."""
        media_row = MediaRow(temp_mp4_file)

        # Check that key UI components exist
        assert hasattr(media_row, "title")
        assert hasattr(media_row, "description")
        assert hasattr(media_row, "upload_btn")
        assert hasattr(media_row, "upload_status")
        assert hasattr(media_row, "select_box")

    def test_mp3_ui_components(self, app, temp_mp3_file):
        """Test MP3-specific UI components."""
        media_row = MediaRow(temp_mp3_file)

        # MP3 should have convert button and image button
        assert hasattr(media_row, "convert_btn")
        assert hasattr(media_row, "image_btn")

        # MP3 should not have upload button initially
        assert not hasattr(media_row, "upload_btn")

    def test_mp4_ui_components(self, app, temp_mp4_file):
        """Test MP4-specific UI components."""
        media_row = MediaRow(temp_mp4_file)

        # MP4 should have upload button and schedule checkbox
        assert hasattr(media_row, "upload_btn")
        assert hasattr(media_row, "schedule_checkbox")

        # MP4 should not have convert button
        assert not hasattr(media_row, "convert_btn")

    def test_validation_without_upload_manager(self, app, temp_mp4_file):
        """Test validation when upload manager is not available."""
        media_row = MediaRow(temp_mp4_file)

        # Should not crash when upload manager is None
        media_row._validate()

        # Upload button should be disabled
        if hasattr(media_row, "upload_btn"):
            assert not media_row.upload_btn.isEnabled()

    def test_validation_with_upload_manager(self, app, temp_mp4_file):
        """Test validation with upload manager."""
        mock_upload_manager = Mock()
        mock_upload_manager.validate_upload_request.return_value = (True, "")

        media_row = MediaRow(temp_mp4_file, upload_manager=mock_upload_manager)

        # Set valid title and description
        media_row.title.setText("Test Title")
        media_row.description.setPlainText("Test Description")

        media_row._validate()

        # Upload button should be enabled
        assert media_row.upload_btn.isEnabled()

    def test_validation_with_invalid_data(self, app, temp_mp4_file):
        """Test validation with invalid data."""
        mock_upload_manager = Mock()
        mock_upload_manager.validate_upload_request.return_value = (
            False,
            "Invalid data",
        )

        media_row = MediaRow(temp_mp4_file, upload_manager=mock_upload_manager)

        # Set invalid title (empty)
        media_row.title.setText("")
        media_row.description.setPlainText("Test Description")

        media_row._validate()

        # Upload button should be disabled
        assert not media_row.upload_btn.isEnabled()

    def test_is_selected(self, app, temp_mp4_file):
        """Test is_selected method."""
        media_row = MediaRow(temp_mp4_file)

        # Initially should not be selected
        assert not media_row.is_selected()

        # Check the select box
        media_row.select_box.setChecked(True)
        assert media_row.is_selected()

        # Uncheck the select box
        media_row.select_box.setChecked(False)
        assert not media_row.is_selected()

    @patch("app.ui.media_row.QFileDialog.getOpenFileName")
    def test_image_selection_mp3(self, mock_file_dialog, app, temp_mp3_file):
        """Test image selection for MP3 files."""
        mock_file_dialog.return_value = (
            str(temp_mp3_file.parent / "test.jpg"),
            "Image Files (*.jpg)",
        )

        media_row = MediaRow(temp_mp3_file)

        # Initially convert button should be disabled
        assert not media_row.convert_btn.isEnabled()

        # Select image
        media_row.on_image_clicked()

        # Convert button should be enabled
        assert media_row.convert_btn.isEnabled()
        assert "test.jpg" in media_row.image_btn.text()

    @patch("app.ui.media_row.QFileDialog.getOpenFileName")
    def test_image_selection_cancelled(self, mock_file_dialog, app, temp_mp3_file):
        """Test image selection when cancelled."""
        mock_file_dialog.return_value = ("", "")

        media_row = MediaRow(temp_mp3_file)

        # Convert button should remain disabled
        assert not media_row.convert_btn.isEnabled()

        # Select image (cancelled)
        media_row.on_image_clicked()

        # Convert button should still be disabled
        assert not media_row.convert_btn.isEnabled()

    def test_image_selection_mp4(self, app, temp_mp4_file):
        """Test image selection for MP4 files (should do nothing)."""
        media_row = MediaRow(temp_mp4_file)

        # Should not crash and should do nothing
        media_row.on_image_clicked()

    @patch("app.ui.media_row.QMessageBox.warning")
    def test_upload_clicked_without_manager(self, mock_warning, app, temp_mp4_file):
        """Test upload button click without upload manager."""
        media_row = MediaRow(temp_mp4_file)

        # Should show warning and not crash
        media_row.on_upload_clicked()

        mock_warning.assert_called_once()

    @patch("app.ui.media_row.QMessageBox.warning")
    def test_upload_clicked_without_validation(self, mock_warning, app, temp_mp4_file):
        """Test upload button click without proper validation."""
        mock_upload_manager = Mock()
        mock_upload_manager.validate_upload_request.return_value = (
            False,
            "Invalid data",
        )

        media_row = MediaRow(temp_mp4_file, upload_manager=mock_upload_manager)

        # Set invalid data
        media_row.title.setText("")
        media_row.description.setPlainText("")

        # Should show warning and not crash
        media_row.on_upload_clicked()

        mock_warning.assert_called_once()

    @patch("app.ui.media_row.QMessageBox.warning")
    def test_upload_clicked_success(self, mock_warning, app, temp_mp4_file):
        """Test successful upload button click."""
        mock_upload_manager = Mock()
        mock_upload_manager.validate_upload_request.return_value = (True, "")
        mock_upload_manager.start_upload.return_value = "test_request_id"

        media_row = MediaRow(temp_mp4_file, upload_manager=mock_upload_manager)

        # Set valid data
        media_row.title.setText("Test Title")
        media_row.description.setPlainText("Test Description")

        # Upload should succeed
        media_row.on_upload_clicked()

        # Should call upload manager
        mock_upload_manager.start_upload.assert_called_once()

        # Upload button should be disabled during upload
        assert not media_row.upload_btn.isEnabled()

    def test_set_upload_manager(self, app, temp_mp4_file):
        """Test setting upload manager after initialization."""
        media_row = MediaRow(temp_mp4_file)

        mock_upload_manager = Mock()
        media_row.set_upload_manager(mock_upload_manager)

        assert media_row.upload_manager == mock_upload_manager

    def test_upload_progress_handling(self, app, temp_mp4_file):
        """Test upload progress handling."""
        media_row = MediaRow(temp_mp4_file)

        # Test progress updates
        media_row.on_upload_progress("test_id", 50, "uploading", "Test message")

        # Should not crash and should update status
        assert media_row.upload_status is not None

    def test_upload_completion_success(self, app, temp_mp4_file):
        """Test successful upload completion."""
        media_row = MediaRow(temp_mp4_file)
        media_row.upload_request_id = "test_id"

        # Mock upload button
        media_row.upload_btn = Mock()

        # Test successful completion
        media_row.on_upload_completed("test_id", True, "test_video_id")

        # Upload button should be re-enabled
        media_row.upload_btn.setEnabled.assert_called_with(True)

        # Request ID should be cleared
        assert media_row.upload_request_id is None

    def test_upload_completion_failure(self, app, temp_mp4_file):
        """Test failed upload completion."""
        media_row = MediaRow(temp_mp4_file)
        media_row.upload_request_id = "test_id"

        # Mock upload button
        media_row.upload_btn = Mock()

        # Test failed completion
        media_row.on_upload_completed("test_id", False, "Upload failed")

        # Upload button should be re-enabled
        media_row.upload_btn.setEnabled.assert_called_with(True)

        # Request ID should be cleared
        assert media_row.upload_request_id is None

    def test_upload_completion_wrong_id(self, app, temp_mp4_file):
        """Test upload completion with wrong request ID."""
        media_row = MediaRow(temp_mp4_file)
        media_row.upload_request_id = "wrong_id"

        # Mock upload button
        media_row.upload_btn = Mock()

        # Test completion with different ID
        media_row.on_upload_completed("test_id", True, "test_video_id")

        # Should not affect this media row
        media_row.upload_btn.setEnabled.assert_not_called()
        assert media_row.upload_request_id == "wrong_id"
