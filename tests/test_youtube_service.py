"""
Unit tests for the YouTube Service.
"""

from pathlib import Path

import pytest
from googleapiclient.errors import HttpError
from unittest.mock import MagicMock, Mock, patch

from core.auth_manager import AuthError, GoogleAuthManager
from services.youtube_service import YouTubeService


class TestYouTubeService:
    """Test the YouTubeService class."""

    @pytest.fixture
    def mock_auth_manager(self):
        """Create a mock authentication manager."""
        mock = Mock(spec=GoogleAuthManager)
        mock.is_authenticated.return_value = True
        mock.get_credentials.return_value = Mock()
        return mock

    @pytest.fixture
    def youtube_service(self, mock_auth_manager):
        """Create a YouTubeService instance for testing."""
        return YouTubeService(auth_manager=mock_auth_manager)

    def test_init(self, mock_auth_manager):
        """Test YouTubeService initialization."""
        service = YouTubeService(auth_manager=mock_auth_manager)

        assert service.auth_manager == mock_auth_manager
        assert service.youtube is None

    def test_ensure_authenticated_not_authenticated(
        self, youtube_service, mock_auth_manager
    ):
        """Test _ensure_authenticated when not authenticated."""
        mock_auth_manager.is_authenticated.return_value = False

        result = youtube_service._ensure_authenticated()
        assert result is False

    def test_ensure_authenticated_already_initialized(
        self, youtube_service, mock_auth_manager
    ):
        """Test _ensure_authenticated when already initialized."""
        mock_youtube = Mock()
        youtube_service.youtube = mock_youtube

        result = youtube_service._ensure_authenticated()
        assert result is True

    @patch("googleapiclient.discovery.build")
    def test_ensure_authenticated_success(
        self, mock_build, youtube_service, mock_auth_manager
    ):
        """Test successful _ensure_authenticated."""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube

        # Mock the auth manager to return valid credentials
        mock_credentials = Mock()
        youtube_service.auth_manager.get_credentials.return_value = mock_credentials
        youtube_service.auth_manager.is_authenticated.return_value = True

        # Reset the service to ensure fresh state
        youtube_service.youtube = None
        youtube_service._auth_checked = False

        result = youtube_service._ensure_authenticated()

        assert result is True
        assert youtube_service.youtube == mock_youtube

    @patch("googleapiclient.discovery.build")
    def test_ensure_authenticated_auth_error(
        self, mock_build, youtube_service, mock_auth_manager
    ):
        """Test _ensure_authenticated with authentication error."""
        # Mock the auth manager to raise AuthError
        youtube_service.auth_manager.is_authenticated.return_value = True
        youtube_service.auth_manager.get_credentials.side_effect = AuthError(
            "Auth failed"
        )

        result = youtube_service._ensure_authenticated()

        assert result is False

    @patch("googleapiclient.discovery.build")
    def test_ensure_authenticated_general_error(
        self, mock_build, youtube_service, mock_auth_manager
    ):
        """Test _ensure_authenticated with general error."""
        # Mock the auth manager to raise general exception
        youtube_service.auth_manager.is_authenticated.return_value = True
        youtube_service.auth_manager.get_credentials.side_effect = Exception(
            "General error"
        )

        result = youtube_service._ensure_authenticated()

        assert result is False

    def test_validate_file_not_exists(self, youtube_service):
        """Test _validate_file when file doesn't exist."""
        result = youtube_service._validate_file(Path("nonexistent.mp4"))
        assert result is False

    def test_validate_file_not_file(self, youtube_service, temp_dir):
        """Test _validate_file when path is not a file."""
        result = youtube_service._validate_file(temp_dir)
        assert result is False

    def test_validate_file_unsupported_extension(self, youtube_service, temp_dir):
        """Test _validate_file with unsupported extension."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        result = youtube_service._validate_file(test_file)
        assert result is False

    def test_validate_file_valid(self, youtube_service, temp_dir):
        """Test _validate_file with valid file."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        result = youtube_service._validate_file(test_file)
        assert result is True

    def test_validate_metadata_missing_title(self, youtube_service):
        """Test _validate_metadata with missing title."""
        is_valid, error = youtube_service._validate_metadata("", "Description")
        assert is_valid is False
        assert "Title is required" in error

    def test_validate_metadata_title_too_long(self, youtube_service):
        """Test _validate_metadata with title too long."""
        is_valid, error = youtube_service._validate_metadata("A" * 101, "Description")
        assert is_valid is False
        assert "Title too long" in error

    def test_validate_metadata_missing_description(self, youtube_service):
        """Test _validate_metadata with missing description."""
        is_valid, error = youtube_service._validate_metadata("Title", "")
        assert is_valid is False
        assert "Description is required" in error

    def test_validate_metadata_description_too_long(self, youtube_service):
        """Test _validate_metadata with description too long."""
        is_valid, error = youtube_service._validate_metadata("Title", "A" * 5001)
        assert is_valid is False
        assert "Description too long" in error

    def test_validate_metadata_valid(self, youtube_service):
        """Test _validate_metadata with valid data."""
        is_valid, error = youtube_service._validate_metadata(
            "Valid Title", "Valid description"
        )
        assert is_valid is True
        assert error == ""

    def test_upload_media_validation_fails(self, youtube_service, temp_dir):
        """Test upload_media when validation fails."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        # Mock _ensure_authenticated to return False
        youtube_service._ensure_authenticated = Mock(return_value=False)

        def progress_callback(percent, status, message):
            pass

        result = youtube_service.upload_media(
            test_file, "Title", "Description", progress_callback
        )
        assert result is None

    def test_upload_media_file_validation_fails(self, youtube_service):
        """Test upload_media when file validation fails."""
        # Mock _ensure_authenticated to return True
        youtube_service._ensure_authenticated = Mock(return_value=True)
        youtube_service._validate_file = Mock(return_value=False)

        def progress_callback(percent, status, message):
            pass

        result = youtube_service.upload_media(
            Path("test.mp4"), "Title", "Description", progress_callback
        )
        assert result is None

    def test_upload_media_metadata_validation_fails(self, youtube_service, temp_dir):
        """Test upload_media when metadata validation fails."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test")

        # Mock validation methods
        youtube_service._ensure_authenticated = Mock(return_value=True)
        youtube_service._validate_file = Mock(return_value=True)
        youtube_service._validate_metadata = Mock(
            return_value=(False, "Invalid metadata")
        )

        def progress_callback(percent, status, message):
            pass

        result = youtube_service.upload_media(
            test_file, "Title", "Description", progress_callback
        )
        assert result is None

    @patch("services.youtube_service.MediaFileUpload")
    def test_upload_media_success(self, mock_media_upload, youtube_service, temp_dir):
        """Test successful upload_media."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test content")

        # Mock validation methods
        youtube_service._ensure_authenticated = Mock(return_value=True)
        youtube_service._validate_file = Mock(return_value=True)
        youtube_service._validate_metadata = Mock(return_value=(True, ""))

        # Mock YouTube API
        mock_youtube = Mock()
        mock_insert = Mock()

        # Mock the next_chunk method to return (None, response) on first call
        # and (status, response) on subsequent calls
        mock_insert.next_chunk.side_effect = [
            (None, {"id": "test_video_id"})  # First call returns the response
        ]

        mock_youtube.videos.return_value.insert.return_value = mock_insert
        youtube_service.youtube = mock_youtube

        # Mock MediaFileUpload
        mock_upload = Mock()
        mock_media_upload.return_value = mock_upload

        progress_calls = []

        def progress_callback(percent, status, message):
            progress_calls.append((percent, status, message))

        result = youtube_service.upload_media(
            test_file, "Test Title", "Test Description", progress_callback
        )

        assert result == "test_video_id"
        assert len(progress_calls) > 0

        # Verify MediaFileUpload was called correctly
        mock_media_upload.assert_called_once_with(
            str(test_file), resumable=True, chunksize=1024 * 1024, mimetype="video/mp4"
        )

        # Verify YouTube API was called correctly
        mock_youtube.videos.return_value.insert.assert_called_once()

    @patch("services.youtube_service.MediaFileUpload")
    def test_upload_media_http_error(
        self, mock_media_upload, youtube_service, temp_dir
    ):
        """Test upload_media with HTTP error."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test content")

        # Mock validation methods
        youtube_service._ensure_authenticated = Mock(return_value=True)
        youtube_service._validate_file = Mock(return_value=True)
        youtube_service._validate_metadata = Mock(return_value=(True, ""))

        # Mock YouTube API to raise HTTP error
        mock_youtube = Mock()
        mock_insert = Mock()
        mock_insert.execute.side_effect = HttpError(
            Mock(status=403), b'{"error": {"message": "Quota exceeded"}}'
        )
        mock_youtube.videos.return_value.insert.return_value = mock_insert
        youtube_service.youtube = mock_youtube

        # Mock MediaFileUpload
        mock_upload = Mock()
        mock_media_upload.return_value = mock_upload

        progress_calls = []

        def progress_callback(percent, status, message):
            progress_calls.append((percent, status, message))

        result = youtube_service.upload_media(
            test_file, "Test Title", "Test Description", progress_callback
        )

        assert result is None
        assert len(progress_calls) > 0
        # Check that error status was reported
        assert any(status == "Failed" for _, status, _ in progress_calls)

    @patch("services.youtube_service.MediaFileUpload")
    def test_upload_media_general_exception(
        self, mock_media_upload, youtube_service, temp_dir
    ):
        """Test upload_media with general exception."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test content")

        # Mock validation methods
        youtube_service._ensure_authenticated = Mock(return_value=True)
        youtube_service._validate_file = Mock(return_value=True)
        youtube_service._validate_metadata = Mock(return_value=(True, ""))

        # Mock YouTube API to raise general exception
        mock_youtube = Mock()
        mock_insert = Mock()
        mock_insert.execute.side_effect = Exception("General error")
        mock_youtube.videos.return_value.insert.return_value = mock_insert
        youtube_service.youtube = mock_youtube

        # Mock MediaFileUpload
        mock_upload = Mock()
        mock_media_upload.return_value = mock_upload

        progress_calls = []

        def progress_callback(percent, status, message):
            progress_calls.append((percent, status, message))

        result = youtube_service.upload_media(
            test_file, "Test Title", "Test Description", progress_callback
        )

        assert result is None
        assert len(progress_calls) > 0
        # Check that error status was reported
        assert any(status == "Failed" for _, status, _ in progress_calls)

    def test_get_upload_quota(self, youtube_service):
        """Test get_upload_quota method."""
        # This is a placeholder method, so just test it doesn't crash
        result = youtube_service.get_upload_quota()
        assert result is None  # Placeholder returns None

    def test_strip_metadata(self, youtube_service, temp_dir):
        """Test that metadata is properly stripped of whitespace."""
        test_file = temp_dir / "test.mp4"
        test_file.write_text("test content")

        # Mock validation methods
        youtube_service._ensure_authenticated = Mock(return_value=True)
        youtube_service._validate_file = Mock(return_value=True)
        youtube_service._validate_metadata = Mock(return_value=(True, ""))

        # Mock YouTube API
        mock_youtube = Mock()
        mock_insert = Mock()

        # Mock the next_chunk method to return (None, response) on first call
        mock_insert.next_chunk.side_effect = [
            (None, {"id": "test_video_id"})  # First call returns the response
        ]

        mock_youtube.videos.return_value.insert.return_value = mock_insert
        youtube_service.youtube = mock_youtube

        # Mock MediaFileUpload
        with patch("services.youtube_service.MediaFileUpload") as mock_media_upload:
            mock_upload = Mock()
            mock_media_upload.return_value = mock_upload

            def progress_callback(percent, status, message):
                pass

            # Test with whitespace in title and description
            result = youtube_service.upload_media(
                test_file, "  Test Title  ", "  Test Description  ", progress_callback
            )

            assert result == "test_video_id"

            # Verify that the insert was called with stripped metadata
            call_args = mock_youtube.videos.return_value.insert.call_args
            body = call_args[1]["body"]
            assert body["snippet"]["title"] == "Test Title"
            assert body["snippet"]["description"] == "Test Description"
