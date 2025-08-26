"""
Core data models for the Media Uploader application.

This module defines the primary data structures used throughout the application,
including MediaItem for representing media files and UploadProgress for tracking
upload status.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import SUPPORTED_EXTENSIONS


@dataclass
class MediaItem:
    """Represents a media file with metadata and properties."""

    path: Path
    title: str = ""
    description: str = ""
    duration_ms: Optional[int] = None
    size_mb_override: Optional[float] = None  # Allow explicit size override

    @property
    def extension(self) -> str:
        """Get the file extension in lowercase."""
        return self.path.suffix.lower()

    @property
    def is_video(self) -> bool:
        """Check if this is a video file."""
        return self.extension == ".mp4"

    @property
    def is_audio(self) -> bool:
        """Check if this is an audio file."""
        return self.extension == ".mp3"

    @property
    def filename(self) -> str:
        """Get the filename without extension."""
        return self.path.stem

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        if self.size_mb_override is not None:
            return self.size_mb_override
        try:
            return self.path.stat().st_size / (1024 * 1024)
        except OSError:
            return 0.0

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes (alias for file_size_mb)."""
        return self.file_size_mb

    def is_valid(self) -> bool:
        """Check if this media item is valid for upload."""
        return (
            self.path.exists()
            and self.path.is_file()
            and self.extension in SUPPORTED_EXTENSIONS
            and self.size_mb > 0
        )
