"""
Media file scanner for discovering and validating media files.
"""

import logging
from pathlib import Path
from typing import List, Optional

from .models import MediaItem
from .config import SUPPORTED_EXTENSIONS


def find_media(directory: Path) -> List[MediaItem]:
    """Find all media files in the given directory."""
    media_items = []

    if not directory.exists() or not directory.is_dir():
        return media_items

    # Supported media extensions
    media_extensions = {".mp3", ".mp4", ".wav", ".flac", ".m4a", ".avi", ".mov", ".mkv"}

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in media_extensions:
            try:
                # Create MediaItem with only the parameters it accepts
                media_item = MediaItem(
                    path=file_path,
                    title=file_path.stem,  # Use filename without extension as title
                )

                media_items.append(media_item)

            except (OSError, PermissionError):
                continue

    return media_items
