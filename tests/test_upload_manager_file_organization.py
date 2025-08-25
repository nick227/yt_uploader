"""
Tests for the enhanced UploadManager with file organization features.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from unittest.mock import Mock, patch

from core.auth_manager import GoogleAuthManager
from core.upload_manager import UploadManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_auth_manager():
    """Create mock auth manager."""
    auth_manager = Mock(spec=GoogleAuthManager)
    auth_manager.is_authenticated.return_value = True
    auth_manager.get_auth_info.return_value = {"authenticated": True}
    return auth_manager


@pytest.fixture
def upload_manager(mock_auth_manager, temp_dir):
    """Create UploadManager instance with file organization."""
    manager = UploadManager(mock_auth_manager)
    # Override the file organizer's uploaded directory
    manager.file_organizer.uploaded_dir = temp_dir / "uploaded"
    manager.file_organizer.uploaded_dir.mkdir(exist_ok=True)
    return manager


class TestUploadManagerFileOrganization:
    """Test cases for UploadManager file organization features."""

    def test_init_with_file_organizer(self, mock_auth_manager):
        """Test UploadManager initialization includes file organizer."""
        manager = UploadManager(mock_auth_manager)

        assert hasattr(manager, "file_organizer")
        assert manager.file_organizer is not None

    def test_organize_uploaded_file_success(self, upload_manager, temp_dir):
        """Test successful file organization through upload manager."""
        # Create test file
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("fake video content")

        # Organize the file
        success, message = upload_manager.organize_uploaded_file(test_file)

        assert success is True
        assert "File moved to:" in message

        # Check file was moved
        assert not test_file.exists()

        # Check file exists in organized location
        date_folder = (
            upload_manager.file_organizer.uploaded_dir
            / datetime.now().strftime("%Y-%m-%d")
        )
        organized_file = date_folder / "test_video.mp4"
        assert organized_file.exists()

    def test_organize_uploaded_file_with_custom_date(self, upload_manager, temp_dir):
        """Test file organization with custom date through upload manager."""
        # Create test file
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("fake video content")

        # Use custom date
        custom_date = datetime(2023, 12, 25)
        success, message = upload_manager.organize_uploaded_file(test_file, custom_date)

        assert success is True

        # Check file exists in correct date folder
        date_folder = upload_manager.file_organizer.uploaded_dir / "2023-12-25"
        organized_file = date_folder / "test_video.mp4"
        assert organized_file.exists()

    def test_organize_uploaded_file_nonexistent(self, upload_manager):
        """Test organizing nonexistent file through upload manager."""
        nonexistent_file = Path("/nonexistent/file.mp4")

        success, message = upload_manager.organize_uploaded_file(nonexistent_file)

        assert success is False
        assert "File not found:" in message

    def test_organize_uploaded_file_exception(self, upload_manager, temp_dir):
        """Test file organization with exception through upload manager."""
        # Create test file
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("fake video content")

        # Mock file organizer to raise exception
        with patch.object(
            upload_manager.file_organizer,
            "organize_uploaded_file",
            side_effect=Exception("Test error"),
        ):
            success, message = upload_manager.organize_uploaded_file(test_file)

            assert success is False
            assert "Error organizing file" in message

    def test_get_organization_stats(self, upload_manager, temp_dir):
        """Test getting organization statistics through upload manager."""
        # Create test files
        date_folder = upload_manager.file_organizer.uploaded_dir / "2023-12-25"
        date_folder.mkdir()

        (date_folder / "file1.mp4").write_text("content1")
        (date_folder / "file2.mp4").write_text("content2")

        # Create another date folder
        date_folder2 = upload_manager.file_organizer.uploaded_dir / "2023-12-26"
        date_folder2.mkdir()
        (date_folder2 / "file3.mp4").write_text("content3")

        stats = upload_manager.get_organization_stats()

        assert stats["total_files"] == 3
        assert stats["date_folders"] == 2
        assert stats["total_size"] > 0

    def test_get_organization_stats_empty(self, upload_manager):
        """Test getting stats for empty organization through upload manager."""
        stats = upload_manager.get_organization_stats()

        assert stats["total_files"] == 0
        assert stats["date_folders"] == 0
        assert stats["total_size"] == 0

    def test_organize_uploaded_file_delegation(self, upload_manager, temp_dir):
        """Test that organize_uploaded_file properly delegates to file organizer."""
        # Create test file
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("fake video content")

        # Mock the file organizer's organize_uploaded_file method
        with patch.object(
            upload_manager.file_organizer, "organize_uploaded_file"
        ) as mock_organize:
            mock_organize.return_value = (True, "Mock success message")

            success, message = upload_manager.organize_uploaded_file(test_file)

            # Verify the file organizer was called
            mock_organize.assert_called_once_with(test_file, None)

            # Verify the result was returned
            assert success is True
            assert message == "Mock success message"

    def test_organize_uploaded_file_with_date_delegation(
        self, upload_manager, temp_dir
    ):
        """Test that organize_uploaded_file properly delegates with custom date."""
        # Create test file
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("fake video content")

        custom_date = datetime(2023, 12, 25)

        # Mock the file organizer's organize_uploaded_file method
        with patch.object(
            upload_manager.file_organizer, "organize_uploaded_file"
        ) as mock_organize:
            mock_organize.return_value = (True, "Mock success message")

            success, message = upload_manager.organize_uploaded_file(
                test_file, custom_date
            )

            # Verify the file organizer was called with the custom date
            mock_organize.assert_called_once_with(test_file, custom_date)

            # Verify the result was returned
            assert success is True
            assert message == "Mock success message"

    def test_get_organization_stats_delegation(self, upload_manager):
        """Test that get_organization_stats properly delegates to file organizer."""
        # Mock the file organizer's get_organization_stats method
        with patch.object(
            upload_manager.file_organizer, "get_organization_stats"
        ) as mock_stats:
            mock_stats.return_value = {
                "total_files": 5,
                "date_folders": 2,
                "total_size": 1024,
            }

            stats = upload_manager.get_organization_stats()

            # Verify the file organizer was called
            mock_stats.assert_called_once()

            # Verify the result was returned
            assert stats["total_files"] == 5
            assert stats["date_folders"] == 2
            assert stats["total_size"] == 1024

    def test_organize_uploaded_file_logging(self, upload_manager, temp_dir):
        """Test that organize_uploaded_file logs errors properly."""
        # Create test file
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("fake video content")

        # Mock the file organizer to raise an exception
        with patch.object(
            upload_manager.file_organizer,
            "organize_uploaded_file",
            side_effect=Exception("Test error"),
        ):
            with patch("core.upload_manager.logger") as mock_logger:
                success, message = upload_manager.organize_uploaded_file(test_file)

                # Verify error was logged
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args[0][0]
                assert "Error organizing uploaded file" in error_call
                assert str(test_file) in error_call
                assert "Test error" in error_call

    def test_file_organizer_integration(self, upload_manager, temp_dir):
        """Test full integration of file organizer with upload manager."""
        # Create test files in different locations
        file1 = temp_dir / "folder1" / "video1.mp4"
        file2 = temp_dir / "folder2" / "video2.mp4"

        file1.parent.mkdir()
        file2.parent.mkdir()
        file1.write_text("content1")
        file2.write_text("content2")

        # Organize both files
        success1, _ = upload_manager.organize_uploaded_file(file1)
        success2, _ = upload_manager.organize_uploaded_file(file2)

        assert success1 is True
        assert success2 is True

        # Check both files were moved
        assert not file1.exists()
        assert not file2.exists()

        # Check both files exist in organized location
        date_folder = (
            upload_manager.file_organizer.uploaded_dir
            / datetime.now().strftime("%Y-%m-%d")
        )
        organized_file1 = date_folder / "video1.mp4"
        organized_file2 = date_folder / "video2.mp4"

        assert organized_file1.exists()
        assert organized_file2.exists()

        # Check stats reflect the organized files
        stats = upload_manager.get_organization_stats()
        assert stats["total_files"] == 2
        assert stats["date_folders"] == 1
        assert stats["total_size"] > 0
