# app/ui/media_preview.py
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

# Import constants from core config
from core.config import SUPPORTED_EXTENSIONS
from core.styles import theme


class ContainedVideoWidget(QVideoWidget):
    """Video widget that respects container bounds."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def resizeEvent(self, event):
        """Override resize to ensure we stay within bounds."""
        super().resizeEvent(event)
        # Force the widget to stay within its allocated space
        if self.parent():
            parent_rect = self.parent().rect()
            # Account for border and margins
            border_width = 3
            margin = 4
            available_width = parent_rect.width() - (2 * border_width) - (2 * margin)
            available_height = parent_rect.height() - (2 * border_width) - (2 * margin)
            x = border_width + margin
            y = border_width + margin
            self.setGeometry(x, y, available_width, available_height)


class VideoContainer(QWidget):
    """Container widget that properly clips video content."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("media_preview")
        self.video_widget = None

    def setVideoWidget(self, video_widget):
        """Set the video widget and position it properly."""
        self.video_widget = video_widget
        if self.video_widget:
            self.video_widget.setParent(self)
            self.updateVideoPosition()

    def updateVideoPosition(self):
        """Update video widget position to stay within bounds."""
        if self.video_widget:
            # Calculate available space accounting for border and margins
            border_width = 3
            margin = 4
            available_width = self.width() - (2 * border_width) - (2 * margin)
            available_height = self.height() - (2 * border_width) - (2 * margin)

            # Center the video widget within available space
            x = (
                border_width
                + margin
                + (available_width - self.video_widget.width()) // 2
            )
            y = (
                border_width
                + margin
                + (available_height - self.video_widget.height()) // 2
            )

            # Ensure video widget doesn't exceed available space
            video_width = min(available_width, self.video_widget.width())
            video_height = min(available_height, self.video_widget.height())

            # Ensure x and y are within bounds
            x = max(
                border_width + margin,
                min(x, self.width() - border_width - margin - video_width),
            )
            y = max(
                border_width + margin,
                min(y, self.height() - border_width - margin - video_height),
            )

            self.video_widget.setGeometry(x, y, video_width, video_height)

    def resizeEvent(self, event):
        """Handle resize events to reposition video widget."""
        super().resizeEvent(event)
        self.updateVideoPosition()

    def paintEvent(self, event):
        """Custom paint event to ensure proper clipping."""
        super().paintEvent(event)
        # The video widget will be clipped by the container's bounds


def create_media_badge(text: str) -> QLabel:
    """Create a styled badge for audio files or other non-video content."""
    badge = QLabel("▶ " + text)
    badge.setAlignment(Qt.AlignCenter)
    badge.setFrameShape(QFrame.Panel)
    badge.setFrameShadow(QFrame.Sunken)
    badge.setStyleSheet(
        f"""
        QLabel {{
            border: 3px solid {theme.primary};
            border-radius: 8px;
            background: {theme.background_elevated};
            color: {theme.text_secondary};
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            padding: 8px;
        }}
        QLabel:hover {{
            border-color: {theme.text_primary};
            background: {theme.background_secondary};
        }}
    """
    )
    return badge


class MediaPreview(QWidget):
    """Handles media preview display and playback controls."""

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path = path

        # Initialize media player
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        # Start with muted audio to prevent jarring sounds during initialization
        self.audio.setVolume(0.0)

        # Connect playback state changes to update visual state
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)

        # Setup error handling
        self.player.errorOccurred.connect(self._on_media_error)

        # Callback for button text updates
        self.button_text_callback = None

        # Media loading state
        self.media_loaded = False
        self.loading_media = False

        self._setup_preview()
        self._load_media()

    @property
    def is_mp3(self) -> bool:
        """Check if this is an MP3 file."""
        return self.path.suffix.lower() == ".mp3"

    @property
    def is_mp4(self) -> bool:
        """Check if this is an MP4 file."""
        return self.path.suffix.lower() == ".mp4"

    def _setup_preview(self):
        """Setup the media preview area (video widget or audio badge)."""
        thumbnail_width = 120
        thumbnail_height = 90

        if self.is_mp4:
            # Create outer container with border styling
            self.preview = QFrame()
            self.preview.setFixedSize(QSize(thumbnail_width, thumbnail_height))
            self.preview.setObjectName("media_preview")

            # Create video widget with proper size
            self.video_widget = QVideoWidget()
            video_size = min(
                thumbnail_width - 10, thumbnail_height - 10
            )  # Leave 5px margin on each side
            self.video_widget.setFixedSize(QSize(video_size, video_size))

            # Create layout with proper centering
            layout = QVBoxLayout(self.preview)
            layout.setContentsMargins(5, 5, 5, 5)  # 5px margin all around
            layout.setSpacing(0)
            layout.addWidget(self.video_widget, 0, Qt.AlignCenter)  # Center the widget

            # Apply the same styling as MP3 to the outer container
            self.preview.setStyleSheet(
                f"""
                QFrame#media_preview {{
                    border: 3px solid {theme.primary};
                    border-radius: 8px;
                    background: {theme.background_elevated};
                }}
                QFrame#media_preview:hover {{
                    border-color: {theme.text_primary};
                    background: {theme.background_secondary};
                }}
            """
            )

            # Make clickable
            self.preview.mousePressEvent = self._on_preview_clicked
        else:
            # Audio badge
            self.preview = create_media_badge("Audio")
            self.preview.setFixedSize(QSize(thumbnail_width, thumbnail_height))
            self.preview.setObjectName("media_preview")

            # Apply the same styling as MP4
            self.preview.setStyleSheet(
                f"""
                QLabel#media_preview {{
                    border: 3px solid {theme.primary};
                    border-radius: 8px;
                    background: {theme.background_elevated};
                    color: {theme.text_secondary};
                    font-size: 12px;
                    font-weight: 500;
                    cursor: pointer;
                    padding: 8px;
                }}
                QLabel#media_preview:hover {{
                    border-color: {theme.text_primary};
                    background: {theme.background_secondary};
                }}
            """
            )

            # Make clickable
            self.preview.mousePressEvent = self._on_preview_clicked

    def _load_media(self):
        """Load the media file into the player."""
        if self.loading_media:
            return

        self.loading_media = True

        try:
            # Basic file validation
            if not self.path.exists():
                raise ValueError(f"Media file does not exist: {self.path}")

            if self.path.stat().st_size == 0:
                raise ValueError(f"Media file is empty: {self.path}")

            # Set up video output if this is MP4
            if self.is_mp4 and hasattr(self, "video_widget"):
                self.player.setVideoOutput(self.video_widget)

            self.player.setSource(QUrl.fromLocalFile(str(self.path)))

            # Initialize video at frame 1 and ensure it shows
            if self.is_mp4:
                # Connect to media status change to set position when loaded
                self.player.mediaStatusChanged.connect(self._on_media_status_changed)
                # Also try to set position immediately after a short delay
                QTimer.singleShot(100, lambda: self._ensure_first_frame())
                # Try a more aggressive approach - set position without playing
                QTimer.singleShot(200, lambda: self._force_first_frame())

            self.media_loaded = True

        except Exception as e:
            pass
            self._handle_media_error()
        finally:
            self.loading_media = False

    def _on_media_error(self, error, error_string):
        """Handle media player errors."""
        try:
            # Handle the error gracefully
            self._handle_media_error()
        except Exception as e:
            # Fallback error handling
            pass

    def _handle_media_error(self):
        """Handle media loading errors."""
        # For video files, show a placeholder instead of trying to decode
        if self.is_mp4 and hasattr(self, "preview"):
            self.preview.setStyleSheet(
                f"""
                QWidget {{
                    border: 3px solid #ff6b6b;
                    border-radius: 8px;
                    background: {theme.background_elevated};
                    color: {theme.text_secondary};
                }}
            """
            )

    def _ensure_first_frame(self):
        """Ensure the first frame is displayed."""
        if self.is_mp4 and self.player:
            # Try to set position to 0 and force a redraw
            self.player.setPosition(0)
            # Force the video widget to update
            if hasattr(self.preview, "update"):
                self.preview.update()

    def _force_first_frame(self):
        """Force the first frame to display without playing audio."""
        if self.is_mp4 and self.player:
            try:
                # Only try to play if the media loaded successfully
                if self.player.mediaStatus() == self.player.MediaStatus.LoadedMedia:
                    # Play briefly with muted audio to load the first frame
                    self.player.play()
                    QTimer.singleShot(50, lambda: self._safe_pause())
                    QTimer.singleShot(100, lambda: self._safe_set_position(0))
            except Exception as e:
                pass

    def _safe_pause(self):
        """Safely pause the player."""
        try:
            if (
                self.player
                and self.player.playbackState()
                == self.player.PlaybackState.PlayingState
            ):
                self.player.pause()
        except Exception as e:
            pass

    def _safe_set_position(self, position: int):
        """Safely set player position."""
        try:
            if self.player:
                self.player.setPosition(position)
        except Exception as e:
            pass

    def _on_media_status_changed(self, status):
        """Handle media status changes to show first frame."""
        if status == self.player.MediaStatus.LoadedMedia:
            # Try multiple approaches to show the first frame
            self.player.setPosition(0)  # Start at the very beginning
            # Use exponential backoff for frame loading attempts
            self._schedule_frame_load(attempt=1)
            # Disconnect to avoid repeated calls
            self.player.mediaStatusChanged.disconnect(self._on_media_status_changed)

    def _schedule_frame_load(self, attempt: int = 1):
        """Schedule frame loading with exponential backoff."""
        if attempt <= 3 and self.is_mp4 and self.player:
            delay = 50 * (2 ** (attempt - 1))  # 50ms, 100ms, 200ms
            QTimer.singleShot(delay, lambda: self._try_load_frame(attempt))

    def _try_load_frame(self, attempt: int):
        """Try to load the first frame."""
        if self.is_mp4 and self.player:
            self.player.setPosition(0)
            if attempt < 3:
                self._schedule_frame_load(attempt + 1)

    def toggle_play(self):
        """Toggle media playback."""
        if not self.player:
            return

        if self.player.playbackState() == self.player.PlaybackState.PlayingState:
            self.player.pause()
            self._update_playing_state(False)
        else:
            # Restore volume when user wants to play
            if self.audio.volume() == 0.0:
                self.audio.setVolume(1.0)
            self.player.play()
            self._update_playing_state(True)

    def _on_preview_clicked(self, event):
        """Handle preview area clicks to toggle playback."""
        self.toggle_play()
        event.accept()

    def _update_playing_state(self, is_playing: bool):
        """Update the visual state of the thumbnail when playing/paused."""
        if not self.player:
            return

        if is_playing:
            # Green border when playing - same for both MP3 and MP4
            if self.is_mp4:
                self.preview.setStyleSheet(
                    f"""
                    QFrame#media_preview {{
                        border: 3px solid {theme.success};
                        border-radius: 8px;
                        background: {theme.background_elevated};
                    }}
                    QFrame#media_preview:hover {{
                        border-color: {theme.success};
                        background: {theme.background_secondary};
                    }}
                """
                )
            else:
                self.preview.setStyleSheet(
                    f"""
                    QLabel#media_preview {{
                        border: 3px solid {theme.success};
                        border-radius: 8px;
                        background: {theme.background_elevated};
                        color: {theme.text_secondary};
                        font-size: 12px;
                        font-weight: 500;
                        cursor: pointer;
                        padding: 8px;
                    }}
                    QLabel#media_preview:hover {{
                        border-color: {theme.success};
                        background: {theme.background_secondary};
                    }}
                """
                )
        else:
            # Reset to normal styling when not playing - same for both MP3 and MP4
            if self.is_mp4:
                self.preview.setStyleSheet(
                    f"""
                    QFrame#media_preview {{
                        border: 3px solid {theme.primary};
                        border-radius: 8px;
                        background: {theme.background_elevated};
                    }}
                    QFrame#media_preview:hover {{
                        border-color: {theme.text_primary};
                        background: {theme.background_secondary};
                    }}
                """
                )
            else:
                self.preview.setStyleSheet(
                    f"""
                    QLabel#media_preview {{
                        border: 3px solid {theme.primary};
                        border-radius: 8px;
                        background: {theme.background_elevated};
                        color: {theme.text_secondary};
                        font-size: 12px;
                        font-weight: 500;
                        cursor: pointer;
                        padding: 8px;
                    }}
                    QLabel#media_preview:hover {{
                        border-color: {theme.text_primary};
                        background: {theme.background_secondary};
                    }}
                """
                )

    def _on_playback_state_changed(self, state):
        """Handle playback state changes to update visual indicators."""
        if state == self.player.PlaybackState.PlayingState:
            self._update_playing_state(True)
            self._update_button_text("Pause")
        else:
            self._update_playing_state(False)
            self._update_button_text("Play")

    def set_button_text_callback(self, callback):
        """Set callback function to update button text."""
        self.button_text_callback = callback
        # Initialize button text based on current state
        if (
            self.player
            and self.player.playbackState() == self.player.PlaybackState.PlayingState
        ):
            self._update_button_text("Pause")
        else:
            self._update_button_text("Play")

    def _update_button_text(self, text: str):
        """Update button text via callback."""
        if self.button_text_callback:
            try:
                self.button_text_callback(text)
            except Exception as e:
                pass

    def get_player(self) -> QMediaPlayer:
        """Get the media player instance."""
        return self.player

    def get_preview_widget(self) -> QWidget:
        """Get the preview widget."""
        return self.preview

    def cleanup(self):
        """Clean up resources."""
        # Stop playback
        if (
            self.player
            and self.player.playbackState() == self.player.PlaybackState.PlayingState
        ):
            self.player.pause()

        # Clear the media source
        if self.player:
            self.player.setSource(QUrl())

        # Disconnect signals
        if self.player:
            try:
                self.player.playbackStateChanged.disconnect()
                self.player.errorOccurred.disconnect()
                self.player.mediaStatusChanged.disconnect()
            except Exception:
                pass  # Signals might already be disconnected

    def force_cleanup_for_file_move(self):
        """Force cleanup to release file handles for file operations."""
        try:
            # Stop playback
            if (
                self.player
                and self.player.playbackState()
                == self.player.PlaybackState.PlayingState
            ):
                self.player.pause()

            # Clear source
            if self.player:
                self.player.setSource(QUrl())

            # Disconnect signals
            if self.player:
                try:
                    self.player.playbackStateChanged.disconnect()
                    self.player.errorOccurred.disconnect()
                    self.player.mediaStatusChanged.disconnect()
                except Exception:
                    pass

            # Reset state
            self.media_loaded = False
            self.loading_media = False

            # Force garbage collection
            import gc

            gc.collect()

        except Exception:
            pass
