from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import SUPPORTED_EXTENSIONS


@dataclass(frozen=True)
class MediaItem:
    path: Path
    title: str = ""
    description: str = ""
    duration_ms: Optional[int] = None
    size_mb_override: Optional[float] = None  # Allow explicit size override

    @property
    def ext(self) -> str:
        return self.path.suffix.lower()

    @property
    def extension(self) -> str:
        """Alias for ext property to match test expectations."""
        return self.ext

    @property
    def is_video(self) -> bool:
        return self.ext == ".mp4"

    @property
    def is_audio(self) -> bool:
        return self.ext == ".mp3"

    @property
    def filename(self) -> str:
        return self.path.name

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
            and self.ext in SUPPORTED_EXTENSIONS
            and self.size_mb > 0
        )
