"""
MediaRow update service for handling file path changes after organization.
"""

from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import QWidget


class MediaRowUpdater:
    """Service for updating MediaRow instances after file operations."""

    @staticmethod
    def update_media_row_for_moved_file(
        media_row: QWidget, old_path: Path, new_path: Path
    ) -> bool:
        """
        Update a MediaRow instance after its file has been moved.

        Args:
            media_row: The MediaRow widget to update
            old_path: Original file path
            new_path: New file path after move

        Returns:
            bool: True if update was successful
        """
        try:
            # Update the main file path
            media_row.path = new_path

            # Update media preview
            if hasattr(media_row, "media_preview"):
                media_row.media_preview.path = new_path

                # Reset media preview state
                media_row.media_preview.media_loaded = False
                media_row.media_preview.loading_media = False

            # Update media info widget
            if hasattr(media_row, "media_info"):
                media_row.media_info.path = new_path
                media_row.media_info._load_media_info()

            # Update status indicators
            if hasattr(media_row, "_update_status_indicators"):
                media_row._update_status_indicators()

            # Update title if it was the original filename
            if hasattr(media_row, "title"):
                original_filename = old_path.stem
                if media_row.title.text() == original_filename:
                    media_row.title.setText(new_path.stem)

            return True

        except Exception:
            return False

    @staticmethod
    def find_media_rows_for_file(
        root_widget: QWidget, file_path: Path
    ) -> List[QWidget]:
        """
        Find all MediaRow instances that reference a specific file.

        Args:
            root_widget: Root widget to search from (usually MainWindow)
            file_path: File path to search for

        Returns:
            List of MediaRow widgets that reference this file
        """
        media_rows = []

        try:
            # Search through all child widgets
            for child in root_widget.findChildren(QWidget):
                if hasattr(child, "path") and child.path == file_path:
                    media_rows.append(child)

            return media_rows

        except Exception:
            return []

    @staticmethod
    def update_all_media_rows_for_moved_file(
        root_widget: QWidget, old_path: Path, new_path: Path
    ) -> int:
        """
        Update all MediaRow instances that reference a moved file.

        Args:
            root_widget: Root widget to search from
            old_path: Original file path
            new_path: New file path after move

        Returns:
            int: Number of MediaRow instances updated
        """
        try:
            # Find all affected MediaRow instances
            media_rows = MediaRowUpdater.find_media_rows_for_file(root_widget, old_path)

            # Update each one
            updated_count = 0
            for media_row in media_rows:
                if MediaRowUpdater.update_media_row_for_moved_file(
                    media_row, old_path, new_path
                ):
                    updated_count += 1

            return updated_count

        except Exception:
            return 0

    @staticmethod
    def validate_media_row_update(media_row: QWidget, new_path: Path) -> bool:
        """
        Validate that a MediaRow can be updated to a new path.

        Args:
            media_row: MediaRow widget to validate
            new_path: New file path to validate

        Returns:
            bool: True if update is valid
        """
        try:
            # Check if new file exists
            if not new_path.exists():
                return False

            # Check if it's a valid media file
            if not new_path.is_file():
                return False

            # Check file size (should be > 0)
            if new_path.stat().st_size == 0:
                return False

            return True

        except Exception:
            return False
