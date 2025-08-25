"""
Unit tests for core models and data structures.
"""

from datetime import datetime
from pathlib import Path

import pytest

from core.models import MediaItem
from infra.events import UploadProgress, UploadStatus


class TestMediaItem:
    """Test the MediaItem dataclass."""

    def test_media_item_creation(self):
        """Test creating MediaItem instances."""
        path = Path("test_video.mp4")
        item = MediaItem(
            path=path,
            title="Test Video",
            description="Test description",
            size_mb_override=10.5,
        )

        assert item.path == path
        assert item.title == "Test Video"
        assert item.description == "Test description"
        assert item.size_mb == 10.5

    def test_media_item_defaults(self):
        """Test MediaItem with default values."""
        path = Path("test_video.mp4")
        item = MediaItem(path=path)

        assert item.path == path
        assert item.title == ""
        assert item.description == ""
        assert item.size_mb == 0.0

    def test_media_item_str_representation(self):
        """Test MediaItem string representation."""
        path = Path("test_video.mp4")
        item = MediaItem(path=path, title="Test Video", size_mb_override=10.5)

        str_repr = str(item)
        assert "test_video.mp4" in str_repr
        assert "Test Video" in str_repr
        assert "10.5" in str_repr

    def test_media_item_filename_property(self):
        """Test MediaItem filename property."""
        path = Path("test_video.mp4")
        item = MediaItem(path=path)

        assert item.filename == "test_video.mp4"

    def test_media_item_extension_property(self):
        """Test MediaItem extension property."""
        path = Path("test_video.mp4")
        item = MediaItem(path=path)

        assert item.extension == ".mp4"

    def test_media_item_is_video(self):
        """Test MediaItem is_video property."""
        # Test video file
        video_path = Path("test_video.mp4")
        video_item = MediaItem(path=video_path)
        assert video_item.is_video is True

        # Test audio file
        audio_path = Path("test_audio.mp3")
        audio_item = MediaItem(path=audio_path)
        assert audio_item.is_video is False

    def test_media_item_is_audio(self):
        """Test MediaItem is_audio property."""
        # Test audio file
        audio_path = Path("test_audio.mp3")
        audio_item = MediaItem(path=audio_path)
        assert audio_item.is_audio is True

        # Test video file
        video_path = Path("test_video.mp4")
        video_item = MediaItem(path=video_path)
        assert video_item.is_audio is False


class TestUploadProgress:
    """Test the UploadProgress dataclass."""

    def test_upload_progress_creation(self):
        """Test creating UploadProgress instances."""
        progress = UploadProgress(
            percent=50,
            status="uploading",
            message="Uploading file...",
            details="Speed: 1.5 MB/s",
            eta_seconds=120,
            speed_mbps=1.5,
        )

        assert progress.percent == 50
        assert progress.status == "uploading"
        assert progress.message == "Uploading file..."
        assert progress.details == "Speed: 1.5 MB/s"
        assert progress.eta_seconds == 120
        assert progress.speed_mbps == 1.5

    def test_upload_progress_defaults(self):
        """Test UploadProgress with default values."""
        progress = UploadProgress(percent=25, status="queued")

        assert progress.percent == 25
        assert progress.status == "queued"
        assert progress.message == ""
        assert progress.details == ""
        assert progress.eta_seconds == 0
        assert progress.speed_mbps == 0.0

    def test_upload_progress_str_representation(self):
        """Test UploadProgress string representation."""
        progress = UploadProgress(
            percent=75, status="uploading", message="Uploading...", speed_mbps=2.5
        )

        str_repr = str(progress)
        assert "75%" in str_repr
        assert "uploading" in str_repr
        assert "Uploading..." in str_repr

    def test_upload_progress_is_complete(self):
        """Test UploadProgress is_complete property."""
        # Test incomplete progress
        incomplete = UploadProgress(percent=50, status="uploading")
        assert incomplete.is_complete is False

        # Test complete progress
        complete = UploadProgress(percent=100, status="completed")
        assert complete.is_complete is True

    def test_upload_progress_is_failed(self):
        """Test UploadProgress is_failed property."""
        # Test successful progress
        success = UploadProgress(percent=100, status="completed")
        assert success.is_failed is False

        # Test failed progress
        failed = UploadProgress(percent=0, status="failed")
        assert failed.is_failed is True

    def test_upload_progress_eta_formatted(self):
        """Test UploadProgress eta_formatted property."""
        # Test with ETA
        progress = UploadProgress(percent=50, status="uploading", eta_seconds=125)
        assert progress.eta_formatted == "2m 5s"

        # Test without ETA
        progress_no_eta = UploadProgress(percent=50, status="uploading", eta_seconds=0)
        assert progress_no_eta.eta_formatted == "Unknown"

    def test_upload_progress_speed_formatted(self):
        """Test UploadProgress speed_formatted property."""
        # Test with speed
        progress = UploadProgress(percent=50, status="uploading", speed_mbps=1.5)
        assert progress.speed_formatted == "1.5 MB/s"

        # Test without speed
        progress_no_speed = UploadProgress(
            percent=50, status="uploading", speed_mbps=0.0
        )
        assert progress_no_speed.speed_formatted == "Unknown"


class TestUploadStatus:
    """Test the UploadStatus enum."""

    def test_upload_status_values(self):
        """Test UploadStatus enum values."""
        assert UploadStatus.QUEUED.value == "queued"
        assert UploadStatus.UPLOADING.value == "uploading"
        assert UploadStatus.COMPLETED.value == "completed"
        assert UploadStatus.FAILED.value == "failed"
        assert UploadStatus.CANCELLED.value == "cancelled"

    def test_upload_status_membership(self):
        """Test UploadStatus enum membership."""
        assert "queued" in UploadStatus
        assert "uploading" in UploadStatus
        assert "completed" in UploadStatus
        assert "failed" in UploadStatus
        assert "cancelled" in UploadStatus
        assert "invalid_status" not in UploadStatus

    def test_upload_status_is_final(self):
        """Test UploadStatus is_final property."""
        # Test final statuses
        assert UploadStatus.is_final("completed") is True
        assert UploadStatus.is_final("failed") is True
        assert UploadStatus.is_final("cancelled") is True

        # Test non-final statuses
        assert UploadStatus.is_final("queued") is False
        assert UploadStatus.is_final("uploading") is False

    def test_upload_status_is_success(self):
        """Test UploadStatus is_success property."""
        # Test success status
        assert UploadStatus.is_success("completed") is True

        # Test non-success statuses
        assert UploadStatus.is_success("failed") is False
        assert UploadStatus.is_success("cancelled") is False
        assert UploadStatus.is_success("queued") is False
        assert UploadStatus.is_success("uploading") is False

    def test_upload_status_is_error(self):
        """Test UploadStatus is_error property."""
        # Test error statuses
        assert UploadStatus.is_error("failed") is True
        assert UploadStatus.is_error("cancelled") is True

        # Test non-error statuses
        assert UploadStatus.is_error("completed") is False
        assert UploadStatus.is_error("queued") is False
        assert UploadStatus.is_error("uploading") is False

    def test_upload_status_icon(self):
        """Test UploadStatus icon property."""
        assert UploadStatus.icon("queued") == "⏳"
        assert UploadStatus.icon("uploading") == "📤"
        assert UploadStatus.icon("completed") == "✅"
        assert UploadStatus.icon("failed") == "❌"
        assert UploadStatus.icon("cancelled") == "🚫"
        assert UploadStatus.icon("unknown") == "❓"

    def test_upload_status_color(self):
        """Test UploadStatus color property."""
        assert UploadStatus.color("queued") == "orange"
        assert UploadStatus.color("uploading") == "blue"
        assert UploadStatus.color("completed") == "green"
        assert UploadStatus.color("failed") == "red"
        assert UploadStatus.color("cancelled") == "gray"
        assert UploadStatus.color("unknown") == "gray"


class TestModelIntegration:
    """Test integration between models."""

    def test_media_item_with_upload_progress(self):
        """Test MediaItem with UploadProgress integration."""
        # Create media item
        item = MediaItem(
            path=Path("test_video.mp4"),
            title="Test Video",
            description="Test description",
            size_mb_override=10.5,
        )

        # Create upload progress
        progress = UploadProgress(
            percent=75,
            status="uploading",
            message=f"Uploading {item.filename}",
            speed_mbps=2.5,
            eta_seconds=60,
        )

        # Test integration
        assert progress.message == f"Uploading {item.filename}"
        assert progress.percent == 75
        assert not progress.is_complete
        assert not progress.is_failed

    def test_upload_progress_status_validation(self):
        """Test UploadProgress with UploadStatus validation."""
        # Test valid statuses
        valid_progress = UploadProgress(percent=50, status="uploading")
        assert valid_progress.status in UploadStatus

        # Test invalid status (should still work but not be in enum)
        invalid_progress = UploadProgress(percent=50, status="invalid_status")
        assert invalid_progress.status not in UploadStatus

    def test_model_serialization(self):
        """Test model serialization for storage/transmission."""
        # Create media item
        item = MediaItem(
            path=Path("test_video.mp4"),
            title="Test Video",
            description="Test description",
            size_mb_override=10.5,
        )

        # Create upload progress
        progress = UploadProgress(
            percent=100,
            status="completed",
            message="Upload successful",
            speed_mbps=3.0,
            eta_seconds=0,
        )

        # Test that models can be converted to dict-like structures
        item_dict = {
            "path": str(item.path),
            "title": item.title,
            "description": item.description,
            "size_mb": item.size_mb,
        }

        progress_dict = {
            "percent": progress.percent,
            "status": progress.status,
            "message": progress.message,
            "speed_mbps": progress.speed_mbps,
            "eta_seconds": progress.eta_seconds,
        }

        # Verify structure
        assert item_dict["path"] == "test_video.mp4"
        assert item_dict["title"] == "Test Video"
        assert progress_dict["percent"] == 100
        assert progress_dict["status"] == "completed"
