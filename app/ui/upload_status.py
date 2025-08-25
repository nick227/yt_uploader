"""
Upload status component for displaying upload progress in a clean, minimal way.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from core.styles import StyleBuilder, theme


class UploadStatusWidget(QWidget):
    """Compact upload status widget with minimal, informative feedback."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._current_status = "idle"

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Status icon (hidden)
        self.status_icon = QLabel("")
        self.status_icon.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                min-width: 0px;
            }
        """
        )
        self.status_icon.setVisible(False)
        layout.addWidget(self.status_icon)

        # Status text
        self.status_text = QLabel("")
        self.status_text.setStyleSheet(StyleBuilder.label_status())
        layout.addWidget(self.status_text, 1)

        # Progress bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {theme.border};
                background: {theme.background_elevated};
                border-radius: 3px;
                text-align: center;
                font-size: 9px;
                color: {theme.text_primary};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.primary}, stop:1 {theme.primary_hover});
                border-radius: 2px;
            }}
        """
        )
        layout.addWidget(self.progress)

        # Set initial state
        self.set_status("idle", "")

    def set_status(self, status: str, message: str = "", progress: int = 0):
        """Set the upload status with appropriate styling."""
        self._current_status = status.lower()

        # Status icons and colors
        status_config = {
            "idle": ("", "", "color: #b9bbbe;"),
            "queued": ("", "Preparing...", "color: #b9bbbe;"),
            "authenticating": ("", "Authenticating...", "color: #faa61a;"),
            "uploading": ("", message or "Uploading...", "color: #5865f2;"),
            "processing": ("", "Processing...", "color: #faa61a;"),
            "finalizing": ("", "Finalizing...", "color: #faa61a;"),
            "completed": ("", "Complete", "color: #57f287;"),
            "completed_with_url": ("", "Complete", "color: #57f287;"),
            "failed": ("", "Failed", "color: #ed4245;"),
            "cancelled": ("", "Cancelled", "color: #b9bbbe;"),
            "converting": ("", message or "Converting...", "color: #f59e0b;"),
            "ready": ("", message or "Ready", "color: #10b981;"),
            "warning": ("", message or "Warning", "color: #f59e0b;"),
        }

        icon, default_message, color_style = status_config.get(
            self._current_status, ("🔄", "Unknown status", "color: #b9bbbe;")
        )

        # Update UI
        self.status_icon.setText(icon)
        self.status_text.setText(message or default_message)
        self.status_text.setStyleSheet(f"{StyleBuilder.label_status()} {color_style}")

        # Show/hide progress bar
        if self._current_status in [
            "uploading",
            "processing",
            "finalizing",
            "converting",
        ]:
            self.progress.setVisible(True)
            self.progress.setValue(progress)
            # Show percentage text on progress bar
            self.progress.setFormat(f"{progress}%")
        else:
            self.progress.setVisible(False)
            self.progress.setValue(0)
            self.progress.setFormat("")

    def update_progress(self, percent: int, status: str, message: str = ""):
        """Update progress with status and message."""
        self.set_status(status, message, percent)

    def reset(self):
        """Reset to idle state."""
        self.set_status("idle")

    def show_conversion_progress(self, percent: int, message: str = ""):
        """Show conversion progress with percentage."""
        self.set_status("converting", message, percent)

    def show_upload_progress(self, percent: int, message: str = ""):
        """Show upload progress with percentage."""
        self.set_status("uploading", message, percent)
