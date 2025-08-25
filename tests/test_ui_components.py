"""
Unit tests for UI components.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock, Mock, patch

from app.ui.history_widget import HistoryItemWidget, HistoryWidget
from app.ui.media_info_widget import MediaInfoWidget
from app.ui.schedule_dialog import ScheduleDialog
from app.ui.upload_status import UploadStatusWidget
from core.history_manager import HistoryManager


@pytest.fixture
def app():
    """Create QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_media_file(tmp_path):
    """Create a temporary media file for testing."""
    media_file = tmp_path / "test_video.mp4"
    media_file.write_text("fake video content")
    return media_file


class TestMediaInfoWidget:
    """Test MediaInfoWidget component."""

    def test_init(self, app, temp_media_file):
        """Test MediaInfoWidget initialization."""
        widget = MediaInfoWidget(temp_media_file)

        assert widget.path == temp_media_file
        assert widget.size_label is not None
        assert widget.date_label is not None
        assert widget.type_label is not None
        assert widget.duration_label is not None
        assert widget.dimensions_label is not None

    def test_load_basic_media_info(self, app, temp_media_file):
        """Test loading basic media information."""
        widget = MediaInfoWidget(temp_media_file)

        # Should load basic info without crashing
        widget._load_basic_media_info()

        # File size should be displayed
        assert widget.size_label.text() != ""

    def test_folder_link_creation(self, app, temp_media_file):
        """Test folder link creation."""
        widget = MediaInfoWidget(temp_media_file)

        # Should have folder link
        assert hasattr(widget, "folder_link")
        assert widget.folder_link is not None

    @patch("subprocess.run")
    def test_open_containing_folder(self, mock_run, app, temp_media_file):
        """Test opening containing folder."""
        widget = MediaInfoWidget(temp_media_file)

        # Mock the mouse press event
        mock_event = Mock()
        widget._open_containing_folder(mock_event)

        # Should call explorer with the folder path
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "explorer"
        assert str(temp_media_file.parent) in call_args[1]


class TestHistoryWidget:
    """Test HistoryWidget component."""

    def test_init(self, app):
        """Test HistoryWidget initialization."""
        history_manager = HistoryManager()
        widget = HistoryWidget(history_manager)

        assert widget.history_manager == history_manager
        assert widget.refresh_btn is not None
        assert widget.stats_label is not None

    def test_refresh_history(self, app):
        """Test refreshing history."""
        history_manager = HistoryManager()
        widget = HistoryWidget(history_manager)

        # Add some test data
        history_manager.add_upload(
            original_file="test.mp4",
            title="Test Video",
            video_url="https://youtube.com/watch?v=123",
            video_id="123",
        )

        # Refresh should update the display
        widget.refresh_history()

        # Should have items in the list
        assert widget.history_list.count() > 0

    def test_clear_history(self, app):
        """Test clearing history."""
        history_manager = HistoryManager()
        widget = HistoryWidget(history_manager)

        # Add some test data
        history_manager.add_upload(
            original_file="test.mp4",
            title="Test Video",
            video_url="https://youtube.com/watch?v=123",
            video_id="123",
        )

        # Clear history
        widget.clear_history()

        # History should be empty
        assert widget.history_list.count() == 0


class TestHistoryItemWidget:
    """Test HistoryItemWidget component."""

    def test_init_upload_item(self, app):
        """Test HistoryItemWidget initialization for upload item."""
        upload_data = {
            "type": "upload",
            "timestamp": "2024-01-01T12:00:00Z",
            "original_file": "test.mp4",
            "title": "Test Video",
            "video_url": "https://youtube.com/watch?v=123",
            "video_id": "123",
        }

        widget = HistoryItemWidget(upload_data)

        assert widget.item_data == upload_data
        assert widget.title_label is not None
        assert widget.date_label is not None

    def test_init_conversion_item(self, app):
        """Test HistoryItemWidget initialization for conversion item."""
        conversion_data = {
            "type": "conversion",
            "timestamp": "2024-01-01T12:00:00Z",
            "mp3_file": "test.mp3",
            "mp4_file": "test.mp4",
            "image_file": "test.jpg",
        }

        widget = HistoryItemWidget(conversion_data)

        assert widget.item_data == conversion_data
        assert widget.title_label is not None
        assert widget.date_label is not None

    def test_clickable_youtube_url(self, app):
        """Test clickable YouTube URL."""
        upload_data = {
            "type": "upload",
            "timestamp": "2024-01-01T12:00:00Z",
            "original_file": "test.mp4",
            "title": "Test Video",
            "video_url": "https://youtube.com/watch?v=123",
            "video_id": "123",
        }

        widget = HistoryItemWidget(upload_data)

        # Should have clickable URL
        url_labels = [
            child
            for child in widget.findChildren(type(widget.title_label))
            if hasattr(child, "text") and "youtube.com" in child.text()
        ]
        assert len(url_labels) > 0


class TestScheduleDialog:
    """Test ScheduleDialog component."""

    def test_init(self, app):
        """Test ScheduleDialog initialization."""
        dialog = ScheduleDialog()

        assert dialog.date_time_edit is not None
        assert dialog.accept_btn is not None
        assert dialog.cancel_btn is not None

    def test_minimum_date_setting(self, app):
        """Test that minimum date is set to tomorrow."""
        dialog = ScheduleDialog()

        # Minimum date should be tomorrow
        from datetime import datetime, timedelta

        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

        assert dialog.date_time_edit.minimumDateTime().toPython() >= tomorrow

    def test_preset_buttons(self, app):
        """Test preset time buttons."""
        dialog = ScheduleDialog()

        # Test tomorrow 9 AM preset
        dialog._set_preset_time("tomorrow_9am")

        # Date should be set to tomorrow
        from datetime import datetime, timedelta

        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

        selected_time = dialog.date_time_edit.dateTime().toPython()
        assert selected_time.hour == 9
        assert selected_time.minute == 0

    def test_get_scheduled_time(self, app):
        """Test getting scheduled time."""
        dialog = ScheduleDialog()

        # Set a specific time
        from datetime import datetime, timedelta

        test_time = datetime.now() + timedelta(days=1, hours=2)
        test_time = test_time.replace(minute=30, second=0, microsecond=0)

        dialog.date_time_edit.setDateTime(test_time)

        # Get scheduled time
        scheduled_time = dialog.get_scheduled_time()

        # Should be in ISO format with Z suffix
        assert scheduled_time.endswith("Z")
        assert "T" in scheduled_time


class TestUploadStatusWidget:
    """Test UploadStatusWidget component."""

    def test_init(self, app):
        """Test UploadStatusWidget initialization."""
        widget = UploadStatusWidget()

        assert widget.progress_bar is not None
        assert widget.status_label is not None

    def test_show_conversion_progress(self, app):
        """Test showing conversion progress."""
        widget = UploadStatusWidget()

        # Show conversion progress
        widget.show_conversion_progress(50)

        # Progress bar should be visible and set to 50%
        assert widget.progress_bar.isVisible()
        assert widget.progress_bar.value() == 50

    def test_show_upload_progress(self, app):
        """Test showing upload progress."""
        widget = UploadStatusWidget()

        # Show upload progress
        widget.show_upload_progress(75, "uploading", "Uploading...")

        # Progress bar should be visible and set to 75%
        assert widget.progress_bar.isVisible()
        assert widget.progress_bar.value() == 75
        assert "Uploading..." in widget.status_label.text()

    def test_hide_progress(self, app):
        """Test hiding progress."""
        widget = UploadStatusWidget()

        # Show progress first
        widget.show_conversion_progress(50)
        assert widget.progress_bar.isVisible()

        # Hide progress
        widget.hide_progress()
        assert not widget.progress_bar.isVisible()

    def test_set_status(self, app):
        """Test setting status."""
        widget = UploadStatusWidget()

        # Set status
        widget.set_status("ready", "Ready to upload")

        # Status should be updated
        assert "Ready to upload" in widget.status_label.text()

    def test_progress_states(self, app):
        """Test different progress states."""
        widget = UploadStatusWidget()

        # Test converting state
        widget.show_conversion_progress(25)
        assert "converting" in widget.progress_bar.styleSheet().lower()

        # Test uploading state
        widget.show_upload_progress(50, "uploading", "Uploading...")
        assert "uploading" in widget.progress_bar.styleSheet().lower()

        # Test ready state
        widget.set_status("ready", "Ready")
        assert "ready" in widget.progress_bar.styleSheet().lower()

        # Test warning state
        widget.set_status("warning", "Warning")
        assert "warning" in widget.progress_bar.styleSheet().lower()
