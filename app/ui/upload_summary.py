"""
Upload summary component for displaying batch upload progress and results.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from core.styles import StyleBuilder, theme


class UploadSummaryWidget(QWidget):
    """Compact upload summary widget for batch operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._total_uploads = 0
        self._completed_uploads = 0
        self._failed_uploads = 0

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Summary frame with glass effect
        self.summary_frame = QFrame()
        self.summary_frame.setFrameStyle(QFrame.StyledPanel)
        self.summary_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {theme.background_elevated};
                border: 1px solid {theme.border};
                border-radius: {theme.radius_m}px;
                padding: 8px;
            }}
        """
        )

        frame_layout = QVBoxLayout(self.summary_frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(6)

        # Title
        self.title_label = QLabel("Upload Summary")
        self.title_label.setStyleSheet(
            f"""
            {StyleBuilder.label_primary()}
            font-weight: 600;
            margin-bottom: 4px;
        """
        )
        frame_layout.addWidget(self.title_label)

        # Progress info
        self.progress_layout = QHBoxLayout()

        # Status icon (hidden)
        self.status_icon = QLabel("")
        self.status_icon.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                min-width: 0px;
            }
        """
        )
        self.status_icon.setVisible(False)
        self.progress_layout.addWidget(self.status_icon)

        # Progress text
        self.progress_text = QLabel("Ready")
        self.progress_text.setStyleSheet(StyleBuilder.label_status())
        self.progress_layout.addWidget(self.progress_text, 1)

        # Progress percentage
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet(
            f"""
            {StyleBuilder.label_status()}
            color: {theme.text_secondary};
            font-weight: 600;
        """
        )
        self.progress_layout.addWidget(self.progress_percent)

        frame_layout.addLayout(self.progress_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: #4f46e5;
                border-radius: 3px;
            }
        """
        )
        frame_layout.addWidget(self.progress_bar)

        # Results summary (hidden by default)
        self.results_layout = QHBoxLayout()

        self.success_count = QLabel("Success: 0")
        self.success_count.setStyleSheet(
            f"""
            {StyleBuilder.label_status()}
            color: {theme.success};
            font-weight: 600;
        """
        )
        self.results_layout.addWidget(self.success_count)

        self.failed_count = QLabel("Failed: 0")
        self.failed_count.setStyleSheet(
            f"""
            {StyleBuilder.label_status()}
            color: {theme.error};
            font-weight: 600;
        """
        )
        self.results_layout.addWidget(self.failed_count)

        self.results_layout.addStretch()
        frame_layout.addLayout(self.results_layout)

        # Add frame to main layout
        layout.addWidget(self.summary_frame)

        # Initially hidden
        self.setVisible(False)

    def start_batch(self, total_uploads: int):
        """Start a new batch upload."""
        self._total_uploads = total_uploads
        self._completed_uploads = 0
        self._failed_uploads = 0

        self.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_layout.setVisible(False)

        self._update_display()

    def update_progress(self, completed: int, failed: int = 0):
        """Update batch progress."""
        self._completed_uploads = completed
        self._failed_uploads = failed

        self._update_display()

    def complete_batch(self, total_completed: int, total_failed: int):
        """Complete the batch upload."""
        self._completed_uploads = total_completed
        self._failed_uploads = total_failed

        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.results_layout.setVisible(True)

        self._update_display()

        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.hide)

    def _update_display(self):
        """Update the display with current progress."""
        total = self._total_uploads
        completed = self._completed_uploads
        failed = self._failed_uploads
        in_progress = total - completed - failed

        # Update progress bar
        if total > 0:
            progress_percent = int(((completed + failed) / total) * 100)
            self.progress_bar.setValue(progress_percent)
            self.progress_percent.setText(f"{progress_percent}%")

        # Update status
        if completed + failed == total:
            if failed == 0:
                self.status_icon.setText("")
                self.progress_text.setText("All uploads completed!")
            elif completed == 0:
                self.status_icon.setText("")
                self.progress_text.setText("All uploads failed")
            else:
                self.status_icon.setText("")
                self.progress_text.setText(f"{completed} succeeded, {failed} failed")
        else:
            self.status_icon.setText("")
            if in_progress > 0:
                self.progress_text.setText(f"{in_progress} uploads in progress...")
            else:
                self.progress_text.setText("Preparing uploads...")

        # Update counts
        self.success_count.setText(f"Success: {completed}")
        self.failed_count.setText(f"Failed: {failed}")

    def hide(self):
        """Hide the summary widget."""
        super().hide()
        self._total_uploads = 0
        self._completed_uploads = 0
        self._failed_uploads = 0
