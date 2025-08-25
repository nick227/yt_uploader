# app/ui/media_info_widget.py
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

# Import constants from core config
from core.config import SUPPORTED_EXTENSIONS
from core.styles import theme


class MediaInfoWidget(QWidget):
    """Compact widget displaying media file metadata."""

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path = path
        self._setup_ui()
        self._load_media_info()

    def _setup_ui(self):
        """Setup the info display layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # File info labels with consistent styling
        info_style = f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                font-weight: 400;
                padding: 2px 0px;
            }}
        """

        self.size_label = QLabel()
        self.size_label.setStyleSheet(info_style)

        self.duration_label = QLabel()
        self.duration_label.setStyleSheet(info_style)

        self.dimensions_label = QLabel()
        self.dimensions_label.setStyleSheet(info_style)

        self.date_label = QLabel()
        self.date_label.setStyleSheet(info_style)

        # Separator dots
        separator_style = f"""
            QLabel {{
                color: {theme.border};
                font-size: 8px;
                font-weight: bold;
                padding: 2px 0px;
            }}
        """

        # Add labels to layout
        layout.addWidget(self.size_label)
        layout.addWidget(self._create_separator(separator_style))
        layout.addWidget(self.duration_label)
        layout.addWidget(self._create_separator(separator_style))
        layout.addWidget(self.dimensions_label)
        layout.addWidget(self._create_separator(separator_style))
        layout.addWidget(self.date_label)

        # Add folder icon link
        self.folder_link = self._create_folder_link()
        layout.addWidget(self.folder_link)

        # Add status indicators (will be populated by parent)
        self.upload_status_indicator = QLabel("")
        self.upload_status_indicator.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                padding: 2px 6px;
                border-radius: 4px;
                background: transparent;
            }}
        """
        )
        layout.addWidget(self.upload_status_indicator)

        self.render_status_indicator = QLabel("")
        self.render_status_indicator.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                padding: 2px 6px;
                border-radius: 4px;
                background: transparent;
            }}
        """
        )
        layout.addWidget(self.render_status_indicator)

        layout.addStretch()

    def _create_separator(self, style: str) -> QLabel:
        """Create a styled separator dot."""
        separator = QLabel("•")
        separator.setStyleSheet(style)
        return separator

    def _create_folder_link(self) -> QLabel:
        """Create a clickable folder icon to open containing folder."""
        folder_link = QLabel("📁")
        folder_link.setToolTip("Open containing folder")
        folder_link.setCursor(Qt.PointingHandCursor)
        folder_link.mousePressEvent = self._open_containing_folder

        folder_link.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                padding: 2px 4px;
                border-radius: 3px;
            }}
            QLabel:hover {{
                color: {theme.primary};
                background: {theme.background_secondary};
            }}
        """
        )

        return folder_link

    def _open_containing_folder(self, event):
        """Open the containing folder in Windows Explorer."""
        try:
            import os
            import subprocess

            # Get the directory containing the file
            folder_path = str(self.path.parent)

            # Use Windows Explorer to open the folder
            subprocess.run(["explorer", folder_path], check=True)

        except Exception as e:
            pass

        event.accept()

    def _load_media_info(self):
        """Load and display media file information."""
        try:
            # File size
            size_bytes = self.path.stat().st_size
            self.size_label.setText(self._format_file_size(size_bytes))

            # File date
            mtime = self.path.stat().st_mtime
            self.date_label.setText(self._format_date(mtime))

            # Media-specific info
            if self.path.suffix.lower() == ".mp4":
                self._load_video_info()
            elif self.path.suffix.lower() == ".mp3":
                self._load_audio_info()
            else:
                self.duration_label.setText("Unknown")
                self.dimensions_label.setText("Unknown")

        except Exception:
            # Set fallback values instead of "Error"
            self.size_label.setText("Unknown")
            self.duration_label.setText("Unknown")
            self.dimensions_label.setText("Unknown")
            self.date_label.setText("Unknown")

    def _load_video_info(self):
        """Load video-specific information using ffprobe."""
        try:
            # Get video duration and dimensions
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=duration,width,height",
                "-of",
                "csv=p=0",
                str(self.path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 3:
                    duration = float(parts[0]) if parts[0] != "N/A" else 0
                    width = int(parts[1]) if parts[1] != "N/A" else 0
                    height = int(parts[2]) if parts[2] != "N/A" else 0

                    self.duration_label.setText(self._format_duration(duration))
                    self.dimensions_label.setText(f"{width}×{height}")
                else:
                    self.duration_label.setText("Unknown")
                    self.dimensions_label.setText("Unknown")
            else:
                self.duration_label.setText("Unknown")
                self.dimensions_label.setText("Unknown")

        except Exception:
            # Try to get basic info from Qt media player as fallback
            self._load_basic_media_info()

    def _load_audio_info(self):
        """Load audio-specific information using ffprobe."""
        try:
            # Get audio duration
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=duration",
                "-of",
                "csv=p=0",
                str(self.path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = (
                    float(result.stdout.strip())
                    if result.stdout.strip() != "N/A"
                    else 0
                )
                self.duration_label.setText(self._format_duration(duration))
            else:
                self.duration_label.setText("Unknown")

            # Audio files don't have dimensions
            self.dimensions_label.setText("Audio")

        except Exception:
            # Try to get basic info from Qt media player as fallback
            self._load_basic_media_info()
            self.dimensions_label.setText("Audio")

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def _format_duration(self, seconds: float) -> str:
        """Format duration in MM:SS format."""
        if seconds <= 0:
            return "0:00"

        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def _format_date(self, timestamp: float) -> str:
        """Format file modification date."""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%m/%d/%Y")

    def _load_basic_media_info(self):
        """Load basic media info using Qt media player as fallback."""
        try:
            # Create a temporary media player to get duration
            temp_player = QMediaPlayer()
            temp_player.setSource(QUrl.fromLocalFile(str(self.path)))

            # Wait a bit for media to load
            QTimer.singleShot(
                500, lambda: self._update_duration_from_player(temp_player)
            )

        except Exception:
            self.duration_label.setText("Unknown")

    def _update_duration_from_player(self, player):
        """Update duration from Qt media player."""
        try:
            duration_ms = player.duration()
            if duration_ms > 0:
                duration_sec = duration_ms / 1000.0
                self.duration_label.setText(self._format_duration(duration_sec))
            else:
                self.duration_label.setText("Unknown")
        except Exception:
            self.duration_label.setText("Unknown")
        finally:
            player.deleteLater()
            # Notify parent to refresh sorting if needed
            self._notify_sorting_refresh()

    def _notify_sorting_refresh(self):
        """Notify parent window to refresh sorting."""
        try:
            # Walk up the widget hierarchy to find the main window
            parent = self.parent()
            while parent:
                if hasattr(parent, "refresh_sorting"):
                    parent.refresh_sorting()
                    break
                parent = parent.parent()
        except Exception:
            pass
