#!/usr/bin/env python3
"""
Splash screen that shows immediately when the EXE starts.
"""

import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QSplashScreen, QVBoxLayout, QWidget


class LoadingThread(QThread):
    """Thread to simulate loading progress."""

    progress_updated = Signal(int)

    def run(self):
        """Simulate loading progress."""
        # Start at 0
        self.progress_updated.emit(0)
        time.sleep(0.1)

        # Quick initial load
        for i in range(1, 30):
            self.progress_updated.emit(i)
            time.sleep(0.02)

        # Faster middle section
        for i in range(30, 80):
            self.progress_updated.emit(i)
            time.sleep(0.03)

        # Final stretch
        for i in range(80, 101):
            self.progress_updated.emit(i)
            time.sleep(0.01)


class SplashScreen(QSplashScreen):
    """Custom splash screen with loading animation."""

    def __init__(self):
        # Create a custom pixmap for the splash screen
        pixmap = self.create_splash_pixmap()
        super().__init__(pixmap)

        # Set up the splash screen
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Create loading thread
        self.loading_thread = LoadingThread()
        self.loading_thread.progress_updated.connect(self.update_progress)

        # Start loading animation
        self.loading_thread.start()

        # Show the splash screen
        self.show()

        # Process events to ensure the splash screen is displayed
        QApplication.processEvents()

    def create_splash_pixmap(self):
        """Create a custom splash screen pixmap."""
        width, height = 400, 300

        # Create pixmap with gradient background
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(35, 35, 35))
        gradient.setColorAt(1, QColor(20, 20, 20))
        painter.fillRect(0, 0, width, height, gradient)

        # Draw subtle border
        painter.setPen(QColor(50, 50, 50))
        painter.drawRect(0, 0, width - 1, height - 1)

        # Draw title
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 255, 255))

        title_text = "Media Uploader"
        title_rect = painter.fontMetrics().boundingRect(title_text)
        title_x = (width - title_rect.width()) // 2
        title_y = 80
        painter.drawText(title_x, title_y, title_text)

        # Draw subtitle
        subtitle_font = QFont("Segoe UI", 10)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(180, 180, 180))

        subtitle_text = "Loading application..."
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle_text)
        subtitle_x = (width - subtitle_rect.width()) // 2
        subtitle_y = title_y + 30
        painter.drawText(subtitle_x, subtitle_y, subtitle_text)

        # Draw loading bar background
        bar_width = 300
        bar_height = 6
        bar_x = (width - bar_width) // 2
        bar_y = subtitle_y + 40

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(30, 30, 30))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 3, 3)

        # Draw loading bar progress (will be updated)
        self.bar_x = bar_x
        self.bar_y = bar_y
        self.bar_width = bar_width
        self.bar_height = bar_height

        # Draw version info
        version_font = QFont("Segoe UI", 8)
        painter.setFont(version_font)
        painter.setPen(QColor(120, 120, 120))

        version_text = "v1.0.0"
        version_rect = painter.fontMetrics().boundingRect(version_text)
        version_x = width - version_rect.width() - 20
        version_y = height - 20
        painter.drawText(version_x, version_y, version_text)

        painter.end()
        return pixmap

    def update_progress(self, progress):
        """Update the loading progress bar."""
        # Create a completely new pixmap to avoid overlay issues
        pixmap = self.create_splash_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate progress bar width
        progress_width = int((progress / 100.0) * self.bar_width)

        # Draw progress bar
        painter.setPen(Qt.NoPen)

        # Create gradient for progress bar
        gradient = QLinearGradient(
            self.bar_x, self.bar_y, self.bar_x + progress_width, self.bar_y
        )
        gradient.setColorAt(0, QColor(0, 150, 255))
        gradient.setColorAt(1, QColor(0, 120, 215))
        painter.setBrush(gradient)

        painter.drawRoundedRect(
            self.bar_x, self.bar_y, progress_width, self.bar_height, 3, 3
        )

        # Draw progress text
        progress_font = QFont("Segoe UI", 9)
        painter.setFont(progress_font)
        painter.setPen(QColor(200, 200, 200))

        progress_text = f"{progress}%"
        progress_rect = painter.fontMetrics().boundingRect(progress_text)
        progress_x = self.bar_x + (self.bar_width - progress_rect.width()) // 2
        progress_y = self.bar_y + self.bar_height + 20
        painter.drawText(progress_x, progress_y, progress_text)

        painter.end()

        # Update the splash screen
        self.setPixmap(pixmap)
        QApplication.processEvents()

    def finish(self, widget):
        """Finish the splash screen and show the main widget."""
        super().finish(widget)
        self.loading_thread.quit()
        self.loading_thread.wait()


def show_splash_screen():
    """Show the splash screen and return it."""
    # Create splash screen
    splash = SplashScreen()

    # Process events to ensure it's displayed
    QApplication.processEvents()

    return splash


if __name__ == "__main__":
    # Test the splash screen
    app = QApplication(sys.argv)

    splash = show_splash_screen()

    # Simulate some loading time
    time.sleep(3)

    # Create a dummy widget to finish the splash screen
    widget = QWidget()
    widget.show()

    splash.finish(widget)

    sys.exit(app.exec())
