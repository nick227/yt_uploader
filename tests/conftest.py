"""
Pytest configuration and common fixtures for Media Uploader tests.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock, Mock

# Import application modules
from core.auth_manager import AuthState, GoogleAuthManager
from core.upload_manager import UploadManager
from infra.uploader import UploadWorker
from services.youtube_service import YouTubeService


@pytest.fixture(scope="session")
def qt_app():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_media_files(temp_dir):
    """Create sample media files for testing."""
    files = []

    # Create sample MP4 file
    mp4_file = temp_dir / "sample_video.mp4"
    mp4_file.write_bytes(b"fake mp4 content")
    files.append(mp4_file)

    # Create sample MP3 file
    mp3_file = temp_dir / "sample_audio.mp3"
    mp3_file.write_bytes(b"fake mp3 content")
    files.append(mp3_file)

    return files


@pytest.fixture
def mock_auth_manager():
    """Create a mock authentication manager."""
    mock = Mock(spec=GoogleAuthManager)
    mock.is_authenticated.return_value = True
    mock.get_user_email.return_value = "test@example.com"
    mock.get_user_info.return_value = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": None,
    }
    mock.get_auth_info.return_value = {
        "is_authenticated": True,
        "user_email": "test@example.com",
        "user_name": "Test User",
        "user_picture": None,
        "expires_at": None,
        "last_refresh": None,
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    }
    mock.get_credentials.return_value = Mock()
    return mock


@pytest.fixture
def mock_youtube_service():
    """Create a mock YouTube service."""
    mock = Mock(spec=YouTubeService)
    mock.upload_media.return_value = "test_video_id_123"
    mock._ensure_authenticated.return_value = True
    return mock


@pytest.fixture
def mock_upload_worker():
    """Create a mock upload worker."""
    mock = Mock(spec=UploadWorker)
    mock.progress = Mock()
    mock.finished = Mock()
    mock.started = Mock()
    mock.cancel = Mock()
    return mock


@pytest.fixture
def sample_upload_request():
    """Create a sample upload request."""
    from pathlib import Path

    from core.upload_manager import UploadRequest

    return UploadRequest(
        path=Path("test_video.mp4"),
        title="Test Video Title",
        description="Test video description",
        request_id="test_upload_123",
    )


@pytest.fixture
def mock_credentials():
    """Create mock Google credentials."""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = "mock_refresh_token"
    mock_creds.token = "mock_access_token"
    mock_creds.expiry = None
    mock_creds.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    return mock_creds


@pytest.fixture
def auth_state_authenticated():
    """Create an authenticated auth state."""
    return AuthState(
        is_authenticated=True,
        user_email="test@example.com",
        expires_at=None,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )


@pytest.fixture
def auth_state_unauthenticated():
    """Create an unauthenticated auth state."""
    return AuthState(
        is_authenticated=False,
        user_email=None,
        expires_at=None,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )


@pytest.fixture
def mock_file_system(temp_dir):
    """Create a mock file system with test files."""
    # Create test directory structure
    test_dir = temp_dir / "test_media"
    test_dir.mkdir()

    # Create test files
    files = []
    for i in range(3):
        file_path = test_dir / f"test_video_{i}.mp4"
        file_path.write_bytes(f"fake video content {i}".encode())
        files.append(file_path)

    return {"root_dir": test_dir, "files": files, "temp_dir": temp_dir}


@pytest.fixture
def mock_progress_callback():
    """Create a mock progress callback function."""

    def mock_callback(percent, status, message=""):
        pass

    return Mock(side_effect=mock_callback)


@pytest.fixture
def sample_media_item():
    """Create a sample media item for testing."""
    from pathlib import Path

    from core.models import MediaItem

    return MediaItem(
        path=Path("test_video.mp4"),
        title="Test Video",
        description="Test description",
        size_mb=10.5,
    )


# Test data fixtures
@pytest.fixture
def valid_upload_data():
    """Valid upload data for testing."""
    return {
        "path": Path("test_video.mp4"),
        "title": "Valid Video Title",
        "description": "Valid video description with enough content",
    }


@pytest.fixture
def invalid_upload_data():
    """Invalid upload data for testing validation."""
    return [
        {
            "path": Path("nonexistent.mp4"),
            "title": "Test Title",
            "description": "Test description",
        },
        {
            "path": Path("test_video.mp4"),
            "title": "",
            "description": "Test description",
        },
        {
            "path": Path("test_video.mp4"),
            "title": "A" * 101,  # Too long
            "description": "Test description",
        },
        {"path": Path("test_video.mp4"), "title": "Test Title", "description": ""},
    ]


# Utility functions for tests
def create_temp_file(temp_dir, filename, content="test content"):
    """Create a temporary file for testing."""
    file_path = temp_dir / filename
    file_path.write_text(content)
    return file_path


def create_temp_media_file(temp_dir, filename, size_mb=1):
    """Create a temporary media file with specified size."""
    file_path = temp_dir / filename
    # Create file with approximate size
    content = "0" * (size_mb * 1024 * 1024 // 10)  # Approximate size
    file_path.write_text(content)
    return file_path


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line(
        "markers", "upload: mark test as upload functionality related"
    )
    config.addinivalue_line("markers", "ui: mark test as UI component related")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "mock: mark test as using mocking")
