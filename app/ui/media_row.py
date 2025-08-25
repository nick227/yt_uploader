# app/ui/media_row.py
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.animations import fade_in, shake

# Import constants from core config
from core.config import SUPPORTED_EXTENSIONS
from core.history_manager import HistoryManager
from core.models import MediaItem
from core.styles import LayoutHelper, StyleBuilder, theme

from .media_converter import ConversionError, MediaConverter
from .media_info_widget import MediaInfoWidget
from .media_preview import MediaPreview
from .media_row_updater import MediaRowUpdater
from .schedule_dialog import ScheduleDialog
from .upload_status import UploadStatusWidget


class MediaRow(QWidget):
    def __init__(self, media_item: MediaItem, parent=None):
        super().__init__(parent)
        self.media_item = media_item
        self.path = media_item.path

        # Initialize components
        self.upload_manager = parent.upload_manager if parent else None
        self.history_manager = HistoryManager()
        self.upload_request_id = None  # Initialize upload request ID

        # Initialize media preview
        self.media_preview = MediaPreview(self.path, self)
        self.player = self.media_preview.get_player()
        self.preview = self.media_preview.get_preview_widget()

        # Setup UI
        self._setup_ui()

        # Set up button text callback
        self.media_preview.set_button_text_callback(self._update_play_button_text)
        self._connect_signals()

        # Initialize media converter after UI setup
        self.media_converter = MediaConverter(
            progress_callback=self.upload_status.show_conversion_progress
        )

        # Validate media file
        self._validate()

        # Add subtle fade-in animation
        self.setWindowOpacity(0.0)
        fade_in(self, duration=400).start()

    @property
    def is_mp3(self) -> bool:
        """Check if this is an MP3 file."""
        return self.path.suffix.lower() == ".mp3"

    @property
    def is_mp4(self) -> bool:
        """Check if this is an MP4 file."""
        return self.path.suffix.lower() == ".mp4"

    def _get_upload_button(self) -> Optional[QPushButton]:
        """Get the upload button if it exists."""
        return getattr(self, "upload_btn", None)

    def _apply_button_style(self, button: QPushButton, style_type: str):
        """Apply consistent button styling."""
        if style_type == "primary":
            button.setStyleSheet(StyleBuilder.button_primary())
        elif style_type == "secondary":
            button.setStyleSheet(StyleBuilder.button_secondary())
        elif style_type == "danger":
            button.setStyleSheet(StyleBuilder.button_danger())

    def _setup_ui(self):
        """Setup the user interface layout."""
        layout = QHBoxLayout(self)
        LayoutHelper.set_standard_margins(layout)
        LayoutHelper.set_standard_spacing(layout)

        # Media preview area
        layout.addWidget(self.preview, 0, Qt.AlignTop)

        # Right side: metadata and controls
        right = QVBoxLayout()
        LayoutHelper.set_tight_spacing(right)
        layout.addLayout(right, 1)

        self._setup_metadata_section(right)
        self._setup_controls_section(right)
        self._setup_progress_section(right)

    def _setup_metadata_section(self, parent_layout: QVBoxLayout):
        """Setup the metadata input fields."""
        # Title input with filename pre-filled (without extension)
        self.title = QLineEdit(self)
        filename_without_ext = self.path.stem  # Remove extension
        self.title.setText(filename_without_ext)
        self.title.setPlaceholderText("Enter video title")
        self.title.setStyleSheet(StyleBuilder.input_field())
        parent_layout.addWidget(self.title)

        # Description input
        self.description = QTextEdit(self)
        self.description.setPlaceholderText("Enter video description")
        self.description.setFixedHeight(60)
        self.description.setStyleSheet(StyleBuilder.input_field())
        parent_layout.addWidget(self.description)

        # Media info widget (includes status indicators)
        self.media_info = MediaInfoWidget(self.path, self)
        parent_layout.addWidget(self.media_info)

        # Update status indicators
        self._update_status_indicators()

    def _update_status_indicators(self):
        """Update the status indicators based on history."""
        try:
            # Find the main window to access history manager
            parent = self.parent()
            while parent:
                if hasattr(parent, "history_manager"):
                    history_manager = parent.history_manager
                    break
                parent = parent.parent()
            else:
                return

            # Check upload status
            uploads = history_manager.get_recent_uploads(limit=1000)
            is_uploaded = any(
                upload.get("original_file") == str(self.path) for upload in uploads
            )

            if is_uploaded:
                self.media_info.upload_status_indicator.setText("✅ Uploaded")
                self.media_info.upload_status_indicator.setStyleSheet(
                    """
                    QLabel {
                        color: #10b981;
                        font-size: 10px;
                        padding: 2px 6px;
                        border-radius: 4px;
                        background: rgba(16, 185, 129, 0.1);
                    }
                """
                )
            else:
                self.media_info.upload_status_indicator.setText("")
                self.media_info.upload_status_indicator.setStyleSheet(
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

            # Check render status (only for MP3s)
            if self.is_mp3:
                conversions = history_manager.get_recent_conversions(limit=1000)
                is_rendered = any(
                    conversion.get("mp3_file") == str(self.path)
                    for conversion in conversions
                )

                if is_rendered:
                    self.media_info.render_status_indicator.setText("🎬 Rendered")
                    self.media_info.render_status_indicator.setStyleSheet(
                        """
                        QLabel {
                            color: #3b82f6;
                            font-size: 10px;
                            padding: 2px 6px;
                            border-radius: 4px;
                            background: rgba(59, 130, 246, 0.1);
                        }
                    """
                    )
                else:
                    self.media_info.render_status_indicator.setText("")
                    self.media_info.render_status_indicator.setStyleSheet(
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
            else:
                # MP4s don't need render status
                self.media_info.render_status_indicator.setText("")

        except Exception as e:
            pass

    def _update_play_button_text(self, text: str):
        """Update the play button text."""
        if hasattr(self, "play_btn"):
            self.play_btn.setText(text)

    def _setup_controls_section(self, parent_layout: QVBoxLayout):
        """Setup the control buttons."""
        controls = QHBoxLayout()
        LayoutHelper.set_compact_spacing(controls)

        # Play/Pause button
        self.play_btn = QPushButton("Play")
        self.play_btn.setStyleSheet(StyleBuilder.button_secondary())
        self.play_btn.clicked.connect(self.media_preview.toggle_play)
        controls.addWidget(self.play_btn)

        # Handle different file types
        if self.is_mp3:
            # MP3: Add image upload and convert buttons
            self.image_btn = QPushButton("Add Image")
            self._apply_button_style(self.image_btn, "secondary")
            self.image_btn.clicked.connect(self.on_image_clicked)
            controls.addWidget(self.image_btn)

            # Overlay selection dropdown
            self.overlay_combo = QComboBox()
            self.overlay_combo.addItems(["No Overlay", "Waveform Bar"])
            self.overlay_combo.setStyleSheet(StyleBuilder.combobox())
            self.overlay_combo.setToolTip("Select visual overlay effect for the video")
            controls.addWidget(self.overlay_combo)

            self.convert_btn = QPushButton("Convert to MP4")
            self._apply_button_style(self.convert_btn, "primary")
            self.convert_btn.clicked.connect(self.on_convert_clicked)
            self.convert_btn.setEnabled(True)  # Always enabled - image is optional
            self.convert_btn.setToolTip(
                "Convert MP3 to MP4. Image is optional. If merge is checked, will combine with other selected MP3s."
            )
            controls.addWidget(self.convert_btn)

            # Store image path for conversion
            self.image_path = None
        else:
            # MP4: Add upload button and schedule checkbox
            self.upload_btn = QPushButton("Upload")
            self._apply_button_style(self.upload_btn, "primary")
            self.upload_btn.clicked.connect(self.on_upload_clicked)
            controls.addWidget(self.upload_btn)

            # Schedule checkbox
            self.schedule_checkbox = QCheckBox("Schedule")
            self.schedule_checkbox.setToolTip("Schedule video for future publication")
            self.schedule_checkbox.setStyleSheet(StyleBuilder.checkbox())
            controls.addWidget(self.schedule_checkbox)

        # Select/Merge checkbox
        checkbox_text = "Merge" if self.is_mp3 else "Select"
        self.select_box = QCheckBox(checkbox_text)
        self.select_box.setStyleSheet(StyleBuilder.checkbox())
        if self.is_mp3:
            self.select_box.setToolTip(
                "Merge this MP3 with other selected MP3s when converting"
            )
        else:
            self.select_box.setToolTip("Select for batch upload")
        controls.addWidget(self.select_box)

        controls.addStretch()
        parent_layout.addLayout(controls)

        # Update convert button text if this is an MP3
        if self.is_mp3:
            self._update_convert_button_text()

        # Connect merge checkbox signal after creation
        if self.is_mp3 and hasattr(self, "select_box"):
            self.select_box.toggled.connect(self._update_convert_button_text)

    def _setup_progress_section(self, parent_layout: QVBoxLayout):
        """Setup the upload progress display."""
        # Upload status widget
        self.upload_status = UploadStatusWidget(self)
        parent_layout.addWidget(self.upload_status)

    def _connect_signals(self):
        """Connect input signals for validation."""
        self.title.textChanged.connect(self._validate)
        self.description.textChanged.connect(self._validate)

    def _validate(self):
        """Validate the media file and update UI accordingly."""
        if not self.path.exists():
            self._handle_missing_file()
        elif self.path.stat().st_size == 0:
            self._handle_invalid_file("File is empty")
        else:
            self._handle_valid_file()

    def _handle_missing_file(self):
        """Handle when the media file is missing."""
        self._disable_interactions()
        if hasattr(self, "upload_status"):
            self.upload_status.set_status("error", "File not found")
        if hasattr(self, "play_btn"):
            self.play_btn.setText("N/A")
            self.play_btn.setToolTip("File not found")

    def _handle_invalid_file(self, reason: str):
        """Handle when the media file is invalid."""
        self._disable_interactions()
        if hasattr(self, "upload_status"):
            self.upload_status.set_status("error", f"Invalid file: {reason}")
        if hasattr(self, "play_btn"):
            self.play_btn.setText("N/A")
            self.play_btn.setToolTip(f"Invalid file: {reason}")

    def _handle_valid_file(self):
        """Handle when the media file is valid."""
        self._enable_interactions()
        if hasattr(self, "play_btn"):
            self.play_btn.setText("Play")
            self.play_btn.setToolTip("Click to play/pause")

    def _disable_interactions(self):
        """Disable all interactive elements."""
        if hasattr(self, "upload_btn"):
            self.upload_btn.setEnabled(False)
        if hasattr(self, "convert_btn"):
            self.convert_btn.setEnabled(False)
        if hasattr(self, "schedule_checkbox"):
            self.schedule_checkbox.setEnabled(False)
        if hasattr(self, "play_btn"):
            self.play_btn.setEnabled(False)

    def _enable_interactions(self):
        """Enable all interactive elements."""
        if hasattr(self, "upload_btn"):
            self.upload_btn.setEnabled(True)
        if hasattr(self, "convert_btn"):
            self.convert_btn.setEnabled(True)
        if hasattr(self, "schedule_checkbox"):
            self.schedule_checkbox.setEnabled(True)
        if hasattr(self, "play_btn"):
            self.play_btn.setEnabled(True)

    def cleanup(self):
        """Clean up resources and release file handles."""
        # Clean up media preview
        if hasattr(self, "media_preview"):
            self.media_preview.cleanup()

        # Clean up media converter
        if hasattr(self, "media_converter"):
            # Cancel any ongoing conversion
            pass  # MediaConverter doesn't have a cleanup method yet

        # Cancel any ongoing upload
        if self.upload_request_id and self.upload_manager:
            try:
                self.upload_manager.cancel_upload(self.upload_request_id)
            except Exception:
                pass  # Upload might already be finished

        # Clear references
        self.upload_request_id = None

    def closeEvent(self, event):
        """Handle widget close event to ensure proper cleanup."""
        self.cleanup()
        super().closeEvent(event)

    def deleteLater(self):
        """Override deleteLater to ensure cleanup."""
        self.cleanup()
        super().deleteLater()

    def is_selected(self) -> bool:
        """Check if this media item is selected for batch operations."""
        return self.select_box.isChecked()

    def on_image_clicked(self):
        """Handle image selection for MP3 conversion."""
        if not self.is_mp3:
            return

        # Open file dialog for image selection
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image for MP3 Thumbnail",
            str(self.path.parent),
            "Image Files (*.jpg *.jpeg *.png *.bmp *.gif);;All Files (*)",
        )

        if image_path:
            self.image_path = Path(image_path)
            self.image_btn.setText(f"Image: {self.image_path.name}")
            self._apply_button_style(self.image_btn, "primary")
            self.convert_btn.setEnabled(True)
            self._update_convert_button_text()  # Update button text based on merge state

    def on_convert_clicked(self):
        """Handle MP3 to MP4 conversion with optional merging."""
        # Check if image path exists and is valid (if one was selected)
        if self.image_path and not self.image_path.exists():
            QMessageBox.warning(
                self, "Image Not Found", "The selected image file no longer exists."
            )
            return

        try:
            # Show conversion progress
            self.convert_btn.setEnabled(False)
            self.upload_status.show_conversion_progress(0, "Starting conversion...")

            # Check if merge is enabled and find other MP3s to merge
            mp3_files_to_merge = self._get_mp3_files_to_merge()

            # Get overlay selection
            overlay_type = self._get_overlay_type()

            if len(mp3_files_to_merge) > 1:
                # Merge multiple MP3s (overlays not supported for merging yet)
                self.upload_status.show_conversion_progress(
                    10, f"Merging {len(mp3_files_to_merge)} MP3 files..."
                )
                # For merging, we need an image - use black background if none provided
                if self.image_path:
                    output_path = self.media_converter.merge_mp3s_to_mp4(
                        mp3_files_to_merge, self.image_path
                    )
                else:
                    # Create a temporary black background for merging
                    output_path = self.media_converter.merge_mp3s_to_mp4_black(
                        mp3_files_to_merge
                    )
            elif len(mp3_files_to_merge) == 1:
                # Single MP3 conversion with overlay
                if overlay_type == "waveform":
                    output_path = self.media_converter.convert_mp3_to_mp4_with_overlay(
                        self.path, self.image_path, "waveform"
                    )
                else:
                    if self.image_path:
                        output_path = self.media_converter.convert_mp3_to_mp4(
                            self.path, self.image_path
                        )
                    else:
                        output_path = (
                            self.media_converter.convert_mp3_to_mp4_with_overlay(
                                self.path, None, "none"
                            )
                        )
            else:
                # No files to merge (shouldn't happen, but handle gracefully)
                raise ConversionError("No MP3 files selected for conversion")

            if output_path and output_path.exists():
                # Record conversion in history
                self._record_conversion_in_history(output_path, mp3_files_to_merge)

                # Update status indicators
                self._update_status_indicators()

                # Add the new MP4 row to the main window
                self._add_mp4_row(output_path)
            else:
                raise ConversionError("Conversion failed - output file not created")

        except ConversionError as e:
            self.convert_btn.setEnabled(True)
            self.upload_status.set_status("failed", f"Conversion failed: {e}")
            QMessageBox.critical(
                self, "Conversion Error", f"Failed to convert MP3: {e}"
            )
        except Exception as e:
            self.convert_btn.setEnabled(True)
            self.upload_status.set_status("failed", f"Unexpected error: {e}")
            QMessageBox.critical(
                self, "Conversion Error", f"Unexpected error during conversion: {e}"
            )

    def _get_overlay_type(self) -> str:
        """Get the selected overlay type from the combo box."""
        if not hasattr(self, "overlay_combo") or not self.is_mp3:
            return "none"

        overlay_text = self.overlay_combo.currentText()
        if overlay_text == "Waveform Bar":
            return "waveform"
        else:
            return "none"

    def _update_convert_button_text(self):
        """Update convert button text based on merge state."""
        if not hasattr(self, "convert_btn") or not self.is_mp3:
            return

        mp3_files_to_merge = self._get_mp3_files_to_merge()
        if len(mp3_files_to_merge) > 1:
            self.convert_btn.setText(f"Merge {len(mp3_files_to_merge)} MP3s to MP4")
            self.convert_btn.setToolTip(
                f"Merge {len(mp3_files_to_merge)} selected MP3 files into a single MP4. Image is optional."
            )
        else:
            self.convert_btn.setText("Convert to MP4")
            self.convert_btn.setToolTip("Convert MP3 to MP4. Image is optional.")

    def _get_mp3_files_to_merge(self) -> list[Path]:
        """Get list of MP3 files to merge (including current file if merge is checked)."""
        mp3_files = []

        # Add current file if merge is checked
        if self.select_box.isChecked():
            mp3_files.append(self.path)

        # Find other MP3 rows with merge checkbox checked
        try:
            parent = self.parent()
            while parent:
                if hasattr(parent, "media_rows"):
                    for media_row in parent.media_rows:
                        if (
                            media_row != self
                            and media_row.is_mp3
                            and media_row.select_box.isChecked()
                        ):
                            mp3_files.append(media_row.path)
                    break
                parent = parent.parent()
        except Exception as e:
            pass

        # If no merge files found, just use current file
        if not mp3_files:
            mp3_files = [self.path]

        return mp3_files

    def _record_conversion_in_history(
        self, mp4_path: Path, mp3_files: list[Path] = None
    ):
        """Record the conversion in the history manager."""
        if mp3_files is None:
            mp3_files = [self.path]

        try:
            # Find the main window to access history manager
            parent = self.parent()
            while parent:
                if hasattr(parent, "history_manager"):
                    # Record each MP3 file that was converted
                    for mp3_file in mp3_files:
                        parent.history_manager.add_conversion(
                            mp3_file=str(mp3_file),
                            mp4_file=str(mp4_path),
                            image_file=(
                                str(self.image_path) if self.image_path else None
                            ),
                        )
                    break
                parent = parent.parent()
        except Exception as e:
            pass

    def _record_upload_in_history(self, video_url: str, video_id: str):
        """Record the upload in the history manager."""
        try:
            # Find the main window to access history manager
            parent = self.parent()
            while parent:
                if hasattr(parent, "history_manager"):
                    parent.history_manager.add_upload(
                        original_file=str(self.path),
                        title=self.title.text().strip(),
                        video_url=video_url,
                        video_id=video_id,
                    )
                    break
                parent = parent.parent()
        except Exception as e:
            pass

    def _add_mp4_row(self, mp4_path: Path):
        """Trigger a rescan to show the new MP4 file."""
        try:
            # Get the main window and trigger a rescan
            parent = self.parent()
            while parent:
                if hasattr(parent, "_scan_current_folder") and hasattr(
                    parent, "current_sort_field"
                ):
                    # Set sort to date (newest first) to show new file at top
                    parent.current_sort_field = "date"
                    parent.current_sort_reverse = True  # Newest first
                    parent.sort_field_combo.setCurrentText("Date")
                    parent.sort_direction_btn.setText("↓")

                    # Rescan the folder to pick up the new MP4
                    parent._scan_current_folder()

                    # Show success message
                    parent.status_label.setText(
                        f"✅ Converted and added: {mp4_path.name}"
                    )
                    self.upload_status.set_status(
                        "completed", f"Converted to: {mp4_path.name}"
                    )
                    break
                parent = parent.parent()
            else:
                # Fallback if we can't find the main window
                self.upload_status.set_status(
                    "completed", f"Converted to: {mp4_path.name}"
                )
                QMessageBox.information(
                    self,
                    "Conversion Complete",
                    f"MP3 successfully converted to MP4!\n\nFile: {mp4_path.name}\n\n"
                    "The file has been saved. Please refresh to see it in the list.",
                )
        except Exception as e:
            self.upload_status.set_status("failed", f"Failed to refresh view: {e}")

    def on_upload_clicked(self):
        """Handle upload button click."""
        if not self.upload_manager:
            QMessageBox.warning(
                self,
                "Upload Manager Not Available",
                "Upload manager is not initialized.",
            )
            return

        if not self.upload_btn.isEnabled():
            # Shake animation for validation error
            shake(self, intensity=5, duration=400).start()
            QMessageBox.warning(
                self,
                "Missing Fields",
                "Title and Description are required before uploading.",
            )
            return

        try:
            # Check if scheduling is requested
            scheduled_time = None
            if (
                hasattr(self, "schedule_checkbox")
                and self.schedule_checkbox.isChecked()
            ):
                # Show scheduling dialog
                schedule_dialog = ScheduleDialog(self)
                if schedule_dialog.exec() == QDialog.Accepted:
                    scheduled_time = schedule_dialog.get_scheduled_time()
                else:
                    # User cancelled scheduling
                    return

            # Start upload through upload manager
            self.upload_request_id = self.upload_manager.start_upload(
                self.path,
                self.title.text().strip(),
                self.description.toPlainText().strip(),
                scheduled_time=scheduled_time,
            )

            # Disable upload button during upload
            self.upload_btn.setEnabled(False)
            self.upload_status.set_status("queued", "Preparing upload...")

        except ValueError as e:
            # Validation error
            QMessageBox.warning(self, "Upload Error", str(e))
            shake(self, intensity=4, duration=500).start()
        except Exception as e:
            # Unexpected error
            QMessageBox.critical(self, "Upload Error", f"Failed to start upload: {e}")
            shake(self, intensity=4, duration=500).start()

    def on_upload_started(self, request_id: str):
        """Handle upload started."""
        if request_id == self.upload_request_id:
            self.upload_status.set_status("uploading", "Upload started...")

    def on_upload_progress(
        self, request_id: str, percent: int, status: str, message: str
    ):
        """Handle upload progress updates."""
        if request_id == self.upload_request_id:
            self.upload_status.update_progress(percent, status, message)

    def on_upload_completed(self, request_id: str, success: bool, info: str):
        """Handle upload completion."""
        if request_id == self.upload_request_id:
            self.upload_btn.setEnabled(True)
            self.upload_request_id = None

            if success:
                # Check if info contains a video ID or URL
                if info and (
                    info.startswith("http") or len(info) == 11
                ):  # YouTube video IDs are 11 chars
                    if info.startswith("http"):
                        video_url = info
                        video_id = info.split("v=")[-1] if "v=" in info else info
                    else:
                        video_id = info
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                    # Record upload in history
                    self._record_upload_in_history(video_url, video_id)

                    # Organize uploaded file
                    self._organize_uploaded_file()

                    # Update status indicators
                    self._update_status_indicators()

                    # Show success message with URL
                    success_message = (
                        f"✅ Upload complete!\n🎥 Video: {video_url}\n"
                        "📝 Note: Video is set to PRIVATE by default"
                    )
                    self.upload_status.set_status("completed", success_message)

                    # Show success dialog with URL
                    QMessageBox.information(
                        self,
                        "Upload Successful!",
                        f"Your video has been uploaded successfully!\n\n"
                        f"🎥 Video URL: {video_url}\n\n"
                        f"📝 Note: The video is set to PRIVATE by default for safety.\n"
                        f"You can change the privacy settings in your YouTube Studio.",
                    )
                else:
                    self.upload_status.set_status("completed", "Upload complete!")
            else:
                self.upload_status.set_status("failed", "Upload failed")
                # Shake animation for error feedback
                shake(self, intensity=4, duration=500).start()
                QMessageBox.critical(
                    self, "Upload Failed", info or "Unknown error occurred"
                )

    def set_upload_manager(self, upload_manager):
        """Set the upload manager for this media row."""
        self.upload_manager = upload_manager
        self._validate()  # Re-validate with new manager

    def _organize_uploaded_file(self):
        """Organize the uploaded file by moving it to the uploaded folder."""
        try:
            if not self.upload_manager:
                return

            # Organize the file
            success, message = self.upload_manager.organize_uploaded_file(self.path)

            if success:
                # Extract the new path from the message
                # Message format: "File moved to: path/to/file"
                if "File moved to: " in message:
                    new_path_str = message.replace("File moved to: ", "")
                    new_path = Path(new_path_str)

                    # Update this MediaRow to point to the new location
                    MediaRowUpdater.update_media_row_for_moved_file(
                        self, self.path, new_path
                    )

                    # Show organization success message
                    QMessageBox.information(
                        self,
                        "File Organized",
                        f"Uploaded file has been moved to:\n{new_path_str}\n\n"
                        "The file is now organized in the uploaded folder structure.",
                    )
                else:
                    # Show generic success message
                    QMessageBox.information(
                        self,
                        "File Organized",
                        "Uploaded file has been organized successfully.",
                    )
            else:
                # Show warning that file couldn't be moved
                QMessageBox.warning(
                    self,
                    "File Organization",
                    f"Upload was successful, but file could not be organized:\n{message}\n\n"
                    "The file remains in its original location.",
                )

        except Exception:
            # Silently handle organization errors (upload was still successful)
            pass
