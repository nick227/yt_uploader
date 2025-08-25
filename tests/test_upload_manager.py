"""
Unit tests for the Upload Manager.
"""

from datetime import datetime
from pathlib import Path

import pytest
from unittest.mock import MagicMock, Mock, patch

from core.auth_manager import GoogleAuthManager
from core.upload_manager import UploadManager, UploadRequest, UploadResult


class TestUploadRequest:
    """Test the UploadRequest dataclass."""

    def test_upload_request_creation(self):
        """Test creating UploadRequest instances."""
        path = Path("test_video.mp4")
        request = UploadRequest(
            path=path,
            title="Test Video",
            description="Test description",
            request_id="test_123",
        )

        assert request.path == path
        assert request.title == "Test Video"
        assert request.description == "Test description"
        assert request.request_id == "test_123"
        assert request.created_at is not None

    def test_upload_request_post_init(self):
        """Test UploadRequest post_init sets created_at."""
        request = UploadRequest(
            path=Path("test.mp4"), title="Test", description="Test", request_id="test"
        )

        assert request.created_at is not None
        assert isinstance(request.created_at, datetime)


class TestUploadResult:
    """Test the UploadResult dataclass."""

    def test_upload_result_creation(self):
        """Test creating UploadResult instances."""
        result = UploadResult(request_id="test_123", success=True, video_id="video_456")

        assert result.request_id == "test_123"
        assert result.success is True
        assert result.video_id == "video_456"
        assert result.error_message is None
        assert result.completed_at is not None

    def test_upload_result_failure(self):
        """Test creating UploadResult for failed upload."""
        result = UploadResult(
            request_id="test_123", success=False, error_message="Upload failed"
        )

        assert result.success is False
        assert result.error_message == "Upload failed"
        assert result.video_id is None


class TestUploadManager:
    """Test the UploadManager class."""

    @pytest.fixture
    def upload_manager(self, mock_auth_manager):
        """Create an UploadManager instance for testing."""
        return UploadManager(mock_auth_manager)

    def test_init(self, mock_auth_manager):
        """Test UploadManager initialization."""
        manager = UploadManager(mock_auth_manager)

        assert manager.auth_manager == mock_auth_manager
        assert manager._active_uploads == {}
        assert manager._upload_threads == {}
        assert manager._upload_workers == {}
        assert manager._batch_requests == []
        assert manager._batch_completed == 0
        assert manager._batch_failed == 0

    def test_is_ready_authenticated(self, upload_manager, mock_auth_manager):
        """Test is_ready when authenticated."""
        mock_auth_manager.is_authenticated.return_value = True
        assert upload_manager.is_ready() is True

    def test_is_ready_not_authenticated(self, upload_manager, mock_auth_manager):
        """Test is_ready when not authenticated."""
        mock_auth_manager.is_authenticated.return_value = False
        assert upload_manager.is_ready() is False

    def test_get_auth_status(self, upload_manager, mock_auth_manager):
        """Test get_auth_status returns auth manager info."""
        auth_info = {"test": "info"}
        mock_auth_manager.get_auth_info.return_value = auth_info

        result = upload_manager.get_auth_status()
        assert result == auth_info
        mock_auth_manager.get_auth_info.assert_called_once()

    def test_validate_upload_request_not_authenticated(
        self, upload_manager, mock_auth_manager
    ):
        """Test validation when not authenticated."""
        mock_auth_manager.is_authenticated.return_value = False

        is_valid, error = upload_manager.validate_upload_request(
            Path("test.mp4"), "Title", "Description"
        )

        assert is_valid is False
        assert "Not authenticated" in error

    def test_validate_upload_request_file_not_exists(
        self, upload_manager, mock_auth_manager
    ):
        """Test validation when file doesn't exist."""
        mock_auth_manager.is_authenticated.return_value = True

        is_valid, error = upload_manager.validate_upload_request(
            Path("nonexistent.mp4"), "Title", "Description"
        )

        assert is_valid is False
        assert "File does not exist" in error

    def test_validate_upload_request_not_file(
        self, upload_manager, mock_auth_manager, temp_dir
    ):
        """Test validation when path is not a file."""
        mock_auth_manager.is_authenticated.return_value = True

        is_valid, error = upload_manager.validate_upload_request(
            temp_dir, "Title", "Description"
        )

        assert is_valid is False
        assert "Path is not a file" in error

    def test_validate_upload_request_missing_title(
        self, upload_manager, mock_auth_manager, temp_dir
    ):
        """Test validation with missing title."""
        mock_auth_manager.is_authenticated.return_value = True
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        is_valid, error = upload_manager.validate_upload_request(
            test_file, "", "Description"
        )

        assert is_valid is False
        assert "Title is required" in error

    def test_validate_upload_request_title_too_long(
        self, upload_manager, mock_auth_manager, temp_dir
    ):
        """Test validation with title too long."""
        mock_auth_manager.is_authenticated.return_value = True
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        is_valid, error = upload_manager.validate_upload_request(
            test_file, "A" * 101, "Description"
        )

        assert is_valid is False
        assert "Title too long" in error

    def test_validate_upload_request_missing_description(
        self, upload_manager, mock_auth_manager, temp_dir
    ):
        """Test validation with missing description."""
        mock_auth_manager.is_authenticated.return_value = True
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        is_valid, error = upload_manager.validate_upload_request(test_file, "Title", "")

        assert is_valid is False
        assert "Description is required" in error

    def test_validate_upload_request_description_too_long(
        self, upload_manager, mock_auth_manager, temp_dir
    ):
        """Test validation with description too long."""
        mock_auth_manager.is_authenticated.return_value = True
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        is_valid, error = upload_manager.validate_upload_request(
            test_file, "Title", "A" * 5001
        )

        assert is_valid is False
        assert "Description too long" in error

    def test_validate_upload_request_valid(
        self, upload_manager, mock_auth_manager, temp_dir
    ):
        """Test validation with valid data."""
        mock_auth_manager.is_authenticated.return_value = True
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        is_valid, error = upload_manager.validate_upload_request(
            test_file, "Valid Title", "Valid description"
        )

        assert is_valid is True
        assert error == ""

    def test_start_upload_validation_fails(self, upload_manager, mock_auth_manager):
        """Test start_upload when validation fails."""
        mock_auth_manager.is_authenticated.return_value = False

        with pytest.raises(ValueError, match="Not authenticated"):
            upload_manager.start_upload(Path("test.mp4"), "Title", "Description")

    @patch("core.upload_manager.UploadWorker")
    @patch("core.upload_manager.QThread")
    def test_start_upload_success(
        self,
        mock_qthread,
        mock_upload_worker,
        upload_manager,
        mock_auth_manager,
        temp_dir,
    ):
        """Test successful start_upload."""
        # Setup
        mock_auth_manager.is_authenticated.return_value = True
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        mock_thread = Mock()
        mock_worker = Mock()
        mock_qthread.return_value = mock_thread
        mock_upload_worker.return_value = mock_worker

        # Test
        request_id = upload_manager.start_upload(test_file, "Title", "Description")

        # Verify
        assert request_id.startswith("upload_")
        assert request_id in upload_manager._active_uploads
        assert request_id in upload_manager._upload_threads
        assert request_id in upload_manager._upload_workers

        # Verify request data
        request = upload_manager._active_uploads[request_id]
        assert request.path == test_file
        assert request.title == "Title"
        assert request.description == "Description"
        assert request.request_id == request_id

    def test_start_batch_upload_validation_fails(
        self, upload_manager, mock_auth_manager
    ):
        """Test start_batch_upload when validation fails."""
        mock_auth_manager.is_authenticated.return_value = False

        uploads = [(Path("test.mp4"), "Title", "Description")]

        with pytest.raises(ValueError, match="Not authenticated"):
            upload_manager.start_batch_upload(uploads)

    @patch("core.upload_manager.UploadWorker")
    @patch("core.upload_manager.QThread")
    def test_start_batch_upload_success(
        self,
        mock_qthread,
        mock_upload_worker,
        upload_manager,
        mock_auth_manager,
        temp_dir,
    ):
        """Test successful start_batch_upload."""
        # Setup
        mock_auth_manager.is_authenticated.return_value = True
        test_files = []
        for i in range(2):
            test_file = temp_dir / f"test_{i}.mp4"
            test_file.write_text(f"test content {i}")
            test_files.append(test_file)

        uploads = [
            (test_files[0], "Title 1", "Description 1"),
            (test_files[1], "Title 2", "Description 2"),
        ]

        mock_thread = Mock()
        mock_worker = Mock()
        mock_qthread.return_value = mock_thread
        mock_upload_worker.return_value = mock_worker

        # Test
        request_ids = upload_manager.start_batch_upload(uploads)

        # Verify
        assert len(request_ids) == 2
        assert len(upload_manager._batch_requests) == 2
        assert upload_manager._batch_completed == 0
        assert upload_manager._batch_failed == 0

        for request_id in request_ids:
            assert request_id in upload_manager._active_uploads
            assert request_id in upload_manager._batch_requests

    def test_cancel_upload_not_found(self, upload_manager):
        """Test cancel_upload when upload not found."""
        result = upload_manager.cancel_upload("nonexistent_id")
        assert result is False

    def test_cancel_upload_success(self, upload_manager):
        """Test successful cancel_upload."""
        # Setup
        mock_worker = Mock()
        upload_manager._upload_workers["test_id"] = mock_worker

        # Test
        result = upload_manager.cancel_upload("test_id")

        # Verify
        assert result is True
        mock_worker.cancel.assert_called_once()

    def test_cancel_all_uploads(self, upload_manager):
        """Test cancel_all_uploads."""
        # Setup
        mock_workers = [Mock(), Mock()]
        upload_manager._upload_workers = {
            "id1": mock_workers[0],
            "id2": mock_workers[1],
        }

        # Test
        upload_manager.cancel_all_uploads()

        # Verify
        for worker in mock_workers:
            worker.cancel.assert_called_once()

    def test_get_upload_status_not_found(self, upload_manager):
        """Test get_upload_status when upload not found."""
        result = upload_manager.get_upload_status("nonexistent_id")
        assert result is None

    def test_get_upload_status_found(self, upload_manager):
        """Test get_upload_status when upload found."""
        # Setup
        request = UploadRequest(
            path=Path("test.mp4"),
            title="Test",
            description="Test",
            request_id="test_id",
        )
        upload_manager._active_uploads["test_id"] = request
        upload_manager._upload_workers["test_id"] = Mock()

        # Test
        result = upload_manager.get_upload_status("test_id")

        # Verify
        assert result is not None
        assert result["request_id"] == "test_id"
        assert result["path"] == str(request.path)
        assert result["title"] == request.title
        assert result["is_active"] is True

    def test_get_active_uploads(self, upload_manager):
        """Test get_active_uploads."""
        # Setup
        upload_manager._active_uploads = {"id1": Mock(), "id2": Mock()}

        # Test
        result = upload_manager.get_active_uploads()

        # Verify
        assert len(result) == 2
        assert "id1" in result
        assert "id2" in result

    def test_on_upload_started(self, upload_manager):
        """Test _on_upload_started signal emission."""
        with patch.object(upload_manager, "upload_started") as mock_signal:
            upload_manager._on_upload_started("test_id")
            mock_signal.emit.assert_called_once_with("test_id")

    def test_on_upload_progress(self, upload_manager):
        """Test _on_upload_progress signal emission."""
        with patch.object(upload_manager, "upload_progress") as mock_signal:
            mock_progress = Mock()
            mock_progress.percent = 50
            mock_progress.status = "uploading"
            mock_progress.message = "Test message"

            upload_manager._on_upload_progress("test_id", mock_progress)

            mock_signal.emit.assert_called_once_with(
                "test_id", 50, "uploading", "Test message"
            )

    def test_on_upload_finished_success(self, upload_manager):
        """Test _on_upload_finished with successful upload."""
        # Setup
        upload_manager._active_uploads["test_id"] = Mock()
        upload_manager._upload_threads["test_id"] = Mock()
        upload_manager._upload_workers["test_id"] = Mock()
        upload_manager._batch_requests = ["test_id"]

        with patch.object(
            upload_manager, "upload_completed"
        ) as mock_completed, patch.object(
            upload_manager, "batch_progress"
        ) as mock_batch_progress, patch.object(
            upload_manager, "batch_completed"
        ) as mock_batch_completed:

            # Test
            upload_manager._on_upload_finished("test_id", True, "video_123")

            # Verify cleanup
            assert "test_id" not in upload_manager._active_uploads
            assert "test_id" not in upload_manager._upload_workers
            # Note: _upload_threads cleanup happens separately in _cleanup_thread

            # Verify signals
            mock_completed.emit.assert_called_once_with("test_id", True, "video_123")
            mock_batch_progress.emit.assert_called_once_with(1, 1, 0)
            mock_batch_completed.emit.assert_called_once_with(1, 0)

    def test_on_upload_finished_failure(self, upload_manager):
        """Test _on_upload_finished with failed upload."""
        # Setup
        upload_manager._active_uploads["test_id"] = Mock()
        upload_manager._upload_threads["test_id"] = Mock()
        upload_manager._upload_workers["test_id"] = Mock()
        upload_manager._batch_requests = ["test_id"]

        with patch.object(
            upload_manager, "upload_completed"
        ) as mock_completed, patch.object(
            upload_manager, "batch_progress"
        ) as mock_batch_progress, patch.object(
            upload_manager, "batch_completed"
        ) as mock_batch_completed:

            # Test
            upload_manager._on_upload_finished("test_id", False, "Upload failed")

            # Verify signals
            mock_completed.emit.assert_called_once_with(
                "test_id", False, "Upload failed"
            )
            mock_batch_progress.emit.assert_called_once_with(1, 0, 1)
            mock_batch_completed.emit.assert_called_once_with(0, 1)

    def test_cleanup(self, upload_manager):
        """Test cleanup method."""
        # Setup
        mock_workers = [Mock(), Mock()]
        mock_threads = [Mock(), Mock()]

        upload_manager._upload_workers = {
            "id1": mock_workers[0],
            "id2": mock_workers[1],
        }
        upload_manager._upload_threads = {
            "id1": mock_threads[0],
            "id2": mock_threads[1],
        }

        # Test
        upload_manager.cleanup()

        # Verify
        for worker in mock_workers:
            worker.cancel.assert_called_once()

        for thread in mock_threads:
            thread.wait.assert_called_once_with(5000)
