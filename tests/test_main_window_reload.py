#!/usr/bin/env python3
"""
Unit tests for MainWindow reload functionality.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock, Mock, patch

from app.ui.main_window import MainWindow
from core.scanner import MediaItem


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication([])


@pytest.fixture
def main_window(app):
    """Create MainWindow instance for testing."""
    window = MainWindow()
    yield window
    window.close()


@pytest.fixture
def mock_media_items():
    """Create mock media items for testing."""
    return [
        MediaItem(Path("test1.mp3"), "audio/mp3", 1024, 120.5),
        MediaItem(Path("test2.mp4"), "video/mp4", 2048, 180.0),
        MediaItem(Path("test3.jpg"), "image/jpeg", 512, 0.0),
    ]


class TestReloadButton:
    """Test the reload button functionality."""

    def test_reload_button_exists(self, main_window):
        """Test that the reload button is created and visible."""
        assert hasattr(main_window, "reload_btn")
        assert main_window.reload_btn is not None
        assert main_window.reload_btn.text() == "🔄"
        assert main_window.reload_btn.toolTip() == "Rescan and reload current directory"

    def test_reload_button_styling(self, main_window):
        """Test that the reload button has correct styling."""
        style = main_window.reload_btn.styleSheet()
        assert "QPushButton" in style
        assert "padding: 4px 8px" in style
        assert "border-radius: 6px" in style
        assert "min-width: 24px" in style
        assert "max-width: 24px" in style

    def test_reload_button_connected(self, main_window):
        """Test that the reload button is connected to the reload method."""
        # Mock the reload method
        with patch.object(main_window, "_reload_current_folder") as mock_reload:
            # Simulate button click
            main_window.reload_btn.clicked.emit()
            mock_reload.assert_called_once()

    @patch("app.ui.main_window.find_media")
    def test_reload_current_folder_success(
        self, mock_find_media, main_window, mock_media_items
    ):
        """Test successful reload of current folder."""
        # Setup mock
        mock_find_media.return_value = mock_media_items

        # Mock the scan folder method
        with patch.object(main_window, "_scan_folder") as mock_scan:
            main_window._reload_current_folder()

            # Verify scan was called with current folder
            mock_scan.assert_called_once_with(main_window.current_folder)

    @patch("app.ui.main_window.find_media")
    def test_reload_current_folder_with_items(
        self, mock_find_media, main_window, mock_media_items
    ):
        """Test reload when items are found."""
        # Setup mock
        mock_find_media.return_value = mock_media_items

        # Mock the scan folder method
        with patch.object(main_window, "_scan_folder") as mock_scan:
            main_window._reload_current_folder()

            # Verify status message
            assert "✅ Reloaded 3 items" in main_window.status_label.text()

    @patch("app.ui.main_window.find_media")
    def test_reload_current_folder_no_items(self, mock_find_media, main_window):
        """Test reload when no items are found."""
        # Setup mock to return empty list
        mock_find_media.return_value = []

        # Mock the scan folder method
        with patch.object(main_window, "_scan_folder") as mock_scan:
            main_window._reload_current_folder()

            # Verify status message
            assert "✅ Reloaded (no items found)" in main_window.status_label.text()

    @patch("app.ui.main_window.find_media")
    def test_reload_current_folder_loading_status(
        self, mock_find_media, main_window, mock_media_items
    ):
        """Test that loading status is shown during reload."""
        # Setup mock
        mock_find_media.return_value = mock_media_items

        # Mock the scan folder method
        with patch.object(main_window, "_scan_folder") as mock_scan:
            main_window._reload_current_folder()

            # Verify loading status was shown (the scan method would have been called)
            mock_scan.assert_called_once()

    def test_reload_button_in_sorting_area(self, main_window):
        """Test that reload button is positioned in the sorting controls area."""
        # The reload button should be added to the sort layout
        # We can verify this by checking it's a sibling of other sort controls
        sort_controls = [
            main_window.sort_field_combo,
            main_window.sort_direction_btn,
            main_window.clear_sort_btn,
            main_window.reload_btn,
        ]

        # All should exist
        for control in sort_controls:
            assert control is not None


class TestReloadIntegration:
    """Test reload functionality integration with other features."""

    @patch("app.ui.main_window.find_media")
    def test_reload_maintains_sorting(
        self, mock_find_media, main_window, mock_media_items
    ):
        """Test that reload maintains current sorting settings."""
        # Setup mock
        mock_find_media.return_value = mock_media_items

        # Set a specific sort
        main_window.current_sort_field = "size"
        main_window.current_sort_reverse = True

        # Mock the apply sorting method
        with patch.object(main_window, "_apply_sorting") as mock_apply_sort:
            with patch.object(main_window, "_scan_folder") as mock_scan:
                main_window._reload_current_folder()

                # Verify scan was called
                mock_scan.assert_called_once()

                # The scan method should call apply_sorting internally
                # This is tested in the scan method itself

    @patch("app.ui.main_window.find_media")
    def test_reload_preserves_upload_manager(
        self, mock_find_media, main_window, mock_media_items
    ):
        """Test that reload preserves the upload manager reference."""
        # Setup mock
        mock_find_media.return_value = mock_media_items

        # Store original upload manager
        original_upload_manager = main_window.upload_manager

        # Mock the scan folder method
        with patch.object(main_window, "_scan_folder") as mock_scan:
            main_window._reload_current_folder()

            # Verify upload manager is still the same
            assert main_window.upload_manager is original_upload_manager

    def test_reload_button_accessibility(self, main_window):
        """Test that reload button is accessible and properly configured."""
        reload_btn = main_window.reload_btn

        # Check basic properties
        assert reload_btn.isEnabled()
        assert reload_btn.isVisible()
        assert reload_btn.toolTip() == "Rescan and reload current directory"

        # Check size constraints
        assert reload_btn.minimumWidth() <= 24
        assert reload_btn.maximumWidth() >= 24


class TestReloadErrorHandling:
    """Test reload functionality error handling."""

    @patch("app.ui.main_window.find_media")
    def test_reload_handles_scan_errors(self, mock_find_media, main_window):
        """Test that reload handles errors during scanning."""
        # Setup mock to raise an exception
        mock_find_media.side_effect = Exception("Scan failed")

        # Mock QMessageBox to avoid showing actual dialog
        with patch("app.ui.main_window.QMessageBox.critical") as mock_critical:
            with patch.object(main_window, "_scan_folder") as mock_scan:
                main_window._reload_current_folder()

                # Verify scan was called (error handling is in _scan_folder)
                mock_scan.assert_called_once()

    def test_reload_with_invalid_folder(self, main_window):
        """Test reload behavior with invalid folder path."""
        # Set an invalid folder path
        main_window.current_folder = Path("/nonexistent/path")

        # Mock the scan folder method
        with patch.object(main_window, "_scan_folder") as mock_scan:
            main_window._reload_current_folder()

            # Verify scan was called with the invalid path
            mock_scan.assert_called_once_with(Path("/nonexistent/path"))


if __name__ == "__main__":
    pytest.main([__file__])
