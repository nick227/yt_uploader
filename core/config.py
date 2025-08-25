"""
Configuration settings for the Media Uploader application.
"""

from pathlib import Path
from typing import Final

# UI Configuration
MEDIA_AREA_SIZE: Final[tuple[int, int]] = (240, 135)  # 16:9 aspect ratio
WINDOW_MIN_SIZE: Final[tuple[int, int]] = (800, 600)
WINDOW_TITLE: Final[str] = "Media Uploader"

# File Configuration
SUPPORTED_EXTENSIONS: Final[set[str]] = {".mp3", ".mp4"}
MAX_FILE_SIZE_MB: Final[int] = 1024  # 1GB limit
DEFAULT_SCAN_DEPTH: Final[int] = 10  # Max directory depth for scanning

# YouTube Configuration
YOUTUBE_TITLE_MAX_LENGTH: Final[int] = 100
YOUTUBE_DESCRIPTION_MAX_LENGTH: Final[int] = 5000
YOUTUBE_MAX_CONSECUTIVE_CAPS: Final[int] = 10
YOUTUBE_MAX_PUNCTUATION: Final[int] = 3

# Upload Configuration
UPLOAD_TIMEOUT_SECONDS: Final[int] = 300  # 5 minutes
MAX_CONCURRENT_UPLOADS: Final[int] = 3
PROGRESS_UPDATE_INTERVAL_MS: Final[int] = 100

# Logging Configuration
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE: Final[Path] = Path("media_uploader.log")

# Default paths
DEFAULT_DOWNLOAD_PATH: Final[Path] = Path.home() / "Downloads"
DEFAULT_MEDIA_PATH: Final[Path] = Path.cwd()


# Data directory for app persistence
def get_data_dir() -> Path:
    """Get the data directory for app persistence files."""
    data_dir = Path.home() / ".media_uploader"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
