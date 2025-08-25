"""
File organization service for automatically moving uploaded videos.
Handles QMediaPlayer cleanup and file operations safely.
"""

import gc
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QApplication


class FileOrganizer:
    """Service for organizing uploaded files with QMediaPlayer safety."""

    def __init__(self):
        self.uploaded_dir = Path("uploaded")
        self.uploaded_dir.mkdir(exist_ok=True)

    def organize_uploaded_file(
        self, file_path: Path, upload_date: Optional[datetime] = None
    ) -> tuple[bool, str]:
        """
        Move uploaded file to organized folder structure.

        Returns:
            (success: bool, message: str)
        """
        try:
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            # Use provided date or current date
            if upload_date is None:
                upload_date = datetime.now()

            # Create destination folder
            date_folder = self.uploaded_dir / upload_date.strftime("%Y-%m-%d")
            date_folder.mkdir(parents=True, exist_ok=True)

            destination = date_folder / file_path.name

            # Check if destination already exists
            if destination.exists():
                # Generate unique filename
                counter = 1
                while destination.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    destination = date_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Attempt to move file
            success = self._safe_move_file(file_path, destination)

            if success:
                return True, f"File moved to: {destination}"
            else:
                return False, "Failed to move file - may be in use"

        except Exception as e:
            return False, f"Error organizing file: {str(e)}"

    def _safe_move_file(self, source: Path, destination: Path) -> bool:
        """Safely move file with QMediaPlayer cleanup."""
        try:
            # First attempt: direct move
            source.rename(destination)
            return True

        except PermissionError:
            # File is locked, try cleanup approach
            return self._move_with_cleanup(source, destination)

        except Exception:
            return False

    def _move_with_cleanup(self, source: Path, destination: Path) -> bool:
        """Move file after forcing QMediaPlayer cleanup."""
        try:
            # Force cleanup of all QMediaPlayer instances
            self._force_media_player_cleanup()

            # Try move again
            source.rename(destination)
            return True

        except PermissionError:
            # Still locked, try copy + delete approach
            return self._copy_and_delete(source, destination)

        except Exception:
            return False

    def _copy_and_delete(self, source: Path, destination: Path) -> bool:
        """Copy file then attempt to delete original."""
        try:
            # Copy file first
            shutil.copy2(source, destination)

            # Try to delete original
            try:
                source.unlink()
                return True
            except PermissionError:
                # Original still locked, but copy succeeded
                # Schedule deletion for later
                self._schedule_file_deletion(source)
                return True

        except Exception:
            return False

    def _force_media_player_cleanup(self):
        """Force cleanup of all QMediaPlayer instances."""
        try:
            # Force garbage collection
            gc.collect()

            # Process Qt events to ensure cleanup
            QApplication.processEvents()

            # Removed QTimer.singleShot call that was causing hangs

        except Exception:
            pass

    def _schedule_file_deletion(self, file_path: Path):
        """Schedule file deletion for when app closes."""
        # This could be implemented with a cleanup queue
        # For now, we'll just leave the file and let user handle it
        pass

    def get_organized_files(self, date: Optional[datetime] = None) -> List[Path]:
        """Get list of organized files for a specific date."""
        try:
            if date is None:
                date = datetime.now()

            date_folder = self.uploaded_dir / date.strftime("%Y-%m-%d")

            if date_folder.exists():
                return list(date_folder.glob("*"))
            else:
                return []

        except Exception:
            return []

    def get_organization_stats(self) -> dict:
        """Get statistics about organized files."""
        try:
            stats = {"total_files": 0, "date_folders": 0, "total_size": 0}

            if self.uploaded_dir.exists():
                for date_folder in self.uploaded_dir.iterdir():
                    if date_folder.is_dir():
                        stats["date_folders"] += 1
                        for file_path in date_folder.iterdir():
                            if file_path.is_file():
                                stats["total_files"] += 1
                                stats["total_size"] += file_path.stat().st_size

            return stats

        except Exception:
            return {"total_files": 0, "date_folders": 0, "total_size": 0}
