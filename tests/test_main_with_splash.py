#!/usr/bin/env python3
"""
Unit tests for main application integration with splash screen.
"""

import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock, Mock, patch

from app.main import main
from app.splash_screen import show_splash_screen


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication([])


class TestMainWithSplashScreen:
    """Test main application with splash screen integration."""

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_shows_splash_screen(self, mock_show_splash, mock_main_window, app):
        """Test that main function shows splash screen."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify splash screen was shown
        mock_show_splash.assert_called_once()

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_finishes_splash_screen(self, mock_show_splash, mock_main_window, app):
        """Test that main function finishes splash screen with main window."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify splash screen was finished with main window
        mock_splash.finish.assert_called_once_with(mock_window)

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_shows_main_window(self, mock_show_splash, mock_main_window, app):
        """Test that main function shows main window."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify main window was shown
        mock_window.show.assert_called_once()

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_creates_main_window(self, mock_show_splash, mock_main_window, app):
        """Test that main function creates main window."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify main window was created
        mock_main_window.assert_called_once()

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_signal_handler_setup(self, mock_show_splash, mock_main_window, app):
        """Test that main function sets up signal handler."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock signal.signal to capture the handler
        with patch("signal.signal") as mock_signal:
            # Mock sys.exit to prevent actual exit
            with patch("sys.exit"):
                # Mock app.exec to prevent actual event loop
                with patch.object(app, "exec", return_value=0):
                    main()

        # Verify signal handler was set up
        mock_signal.assert_called_once()

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_timer_setup(self, mock_show_splash, mock_main_window, app):
        """Test that main function sets up timer for signal processing."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock QTimer to capture timer setup
        with patch("app.main.QTimer") as mock_timer_class:
            mock_timer = Mock()
            mock_timer_class.return_value = mock_timer

            # Mock sys.exit to prevent actual exit
            with patch("sys.exit"):
                # Mock app.exec to prevent actual event loop
                with patch.object(app, "exec", return_value=0):
                    main()

        # Verify timer was set up
        mock_timer.start.assert_called_once_with(500)
        mock_timer.timeout.connect.assert_called_once()


class TestMainErrorHandling:
    """Test main application error handling."""

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_handles_keyboard_interrupt(
        self, mock_show_splash, mock_main_window, app
    ):
        """Test that main function handles KeyboardInterrupt gracefully."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock app.exec to raise KeyboardInterrupt
        with patch.object(app, "exec", side_effect=KeyboardInterrupt):
            # Mock sys.exit to prevent actual exit
            with patch("sys.exit") as mock_exit:
                main()

        # Verify main window was closed
        mock_window.close.assert_called_once()

        # Verify sys.exit was called
        mock_exit.assert_called_once_with(0)

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_handles_main_window_creation_error(
        self, mock_show_splash, mock_main_window, app
    ):
        """Test that main function handles MainWindow creation errors."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock MainWindow to raise an exception
        mock_main_window.side_effect = Exception("MainWindow creation failed")

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit") as mock_exit:
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify sys.exit was called (due to exception)
        mock_exit.assert_called_once()


class TestMainIntegration:
    """Test main application integration scenarios."""

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_complete_flow(self, mock_show_splash, mock_main_window, app):
        """Test the complete main function flow."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify the complete flow:
        # 1. Splash screen shown
        mock_show_splash.assert_called_once()

        # 2. Main window created
        mock_main_window.assert_called_once()

        # 3. Splash screen finished with main window
        mock_splash.finish.assert_called_once_with(mock_window)

        # 4. Main window shown
        mock_window.show.assert_called_once()

    @patch("app.main.MainWindow")
    @patch("app.main.show_splash_screen")
    def test_main_splash_screen_lifecycle(
        self, mock_show_splash, mock_main_window, app
    ):
        """Test splash screen lifecycle in main function."""
        # Mock the splash screen
        mock_splash = Mock()
        mock_show_splash.return_value = mock_splash

        # Mock the main window
        mock_window = Mock()
        mock_main_window.return_value = mock_window

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Mock app.exec to prevent actual event loop
            with patch.object(app, "exec", return_value=0):
                main()

        # Verify splash screen lifecycle:
        # 1. Created and shown
        mock_show_splash.assert_called_once()

        # 2. Finished with main window
        mock_splash.finish.assert_called_once_with(mock_window)


if __name__ == "__main__":
    pytest.main([__file__])
