from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.config import WINDOW_MIN_SIZE, WINDOW_TITLE
from core.history_manager import HistoryManager
from core.models import MediaItem
from core.scanner import find_media
from core.styles import LayoutHelper, StyleBuilder, theme
from core.upload_manager import UploadManager

from .auth_widget import AuthWidget
from .folder_chip_bar import FolderChipBar
from .history_widget import HistoryWidget
from .media_row import MediaRow
from .upload_summary import UploadSummaryWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)

        # Apply dark theme to main window
        self.setStyleSheet(StyleBuilder.main_window())

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        layout = QVBoxLayout(central)
        LayoutHelper.set_standard_spacing(layout)

        # Initialize managers (defer auth setup to avoid blocking)
        self.auth_widget = None  # Will be initialized after window shows
        self.upload_manager = None  # Will be initialized after auth
        self.history_manager = HistoryManager()

        # Initialize sorting state
        self.current_sort_field = "name"
        self.current_sort_reverse = False

        # Toolbar area with proper padding
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)  # Align with scroll area padding

        # Combined folder button and path display
        self.folder_btn = QPushButton()
        self.folder_btn.setStyleSheet(
            f"""
            QPushButton {{
                padding: 6px 16px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 8px;
                font-size: 10px;
                font-weight: 500;
                min-height: 20px;
                min-width: 50px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {theme.background_secondary};
                border-color: {theme.primary};
            }}
            QPushButton:pressed {{
                background: {theme.background_tertiary};
            }}
        """
        )
        # Initialize with current directory
        self.current_folder = Path.cwd()

        self.folder_btn.clicked.connect(self._choose_folder)
        self._update_folder_button_text()
        toolbar.addWidget(self.folder_btn, 1)  # Take up available space

        # History button
        self.history_btn = QPushButton("📋 History")
        self.history_btn.setStyleSheet(StyleBuilder.button_secondary())
        self.history_btn.clicked.connect(self._show_history)
        toolbar.addWidget(self.history_btn)

        # Upload button
        self.batch_upload_btn = QPushButton("All")
        self.batch_upload_btn.setStyleSheet(StyleBuilder.button_danger())
        self.batch_upload_btn.clicked.connect(self._upload_selected)
        self.batch_upload_btn.setEnabled(False)
        toolbar.addWidget(self.batch_upload_btn)

        layout.addLayout(toolbar)

        # Sorting controls
        self._setup_sorting_ui(layout)

        # Folder chip bar for filtering
        self.folder_chip_bar = FolderChipBar()
        self.folder_chip_bar.folder_toggled.connect(self._on_folder_toggled)
        layout.addWidget(self.folder_chip_bar)

        # Status label for user feedback
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 11px;
                padding: 4px 0px 0px 20px;
                margin: 0px;
            }}
        """
        )
        layout.addWidget(self.status_label)

        # Upload summary widget
        self.upload_summary = UploadSummaryWidget(self)
        layout.addWidget(self.upload_summary)

        # Media list area with enhanced styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(StyleBuilder.scroll_area())

        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        LayoutHelper.set_compact_spacing(self.media_layout)
        self.media_layout.addStretch()  # Push items to top

        # Auth widget will be added after initialization in _initialize_auth()

        self.scroll_area.setWidget(self.media_container)
        layout.addWidget(self.scroll_area)

        self.media_rows: list[MediaRow] = []
        self.hidden_folders: set[str] = set()  # Track hidden folders
        # Defer initial scan to avoid blocking startup
        # self._scan_current_folder()

        # Update upload button state based on authentication
        self._update_upload_button_state()

    def showEvent(self, event):
        """Handle show event - initialize auth after window is visible."""
        super().showEvent(event)

        # Initialize auth widget after window is shown to avoid blocking
        if self.auth_widget is None:
            self._initialize_auth()
        
        # Trigger initial folder scan after window is shown
        QTimer.singleShot(100, self._scan_current_folder)

    def _initialize_auth(self):
        """Initialize authentication components after window is shown."""
        try:
            self.auth_widget = AuthWidget(self)
            self.auth_widget.auth_state_changed.connect(self._on_auth_state_changed)
            self.upload_manager = UploadManager(self.auth_widget.auth_manager)
            self._connect_upload_manager_signals()

            # Add auth widget to the layout after it's created
            self.media_layout.addWidget(self.auth_widget)

        except Exception as e:
            # If auth initialization fails, show a warning but don't crash
            QMessageBox.warning(
                self,
                "Authentication Warning",
                f"Failed to initialize authentication: {e}\n\nYou can still browse and convert media files.",
            )

    def _on_folder_toggled(self, folder_path: str, is_visible: bool):
        """Handle folder visibility toggle."""
        if is_visible:
            self.hidden_folders.discard(folder_path)
        else:
            self.hidden_folders.add(folder_path)

        # Update media row visibility
        self._update_media_visibility()

    def _update_media_visibility(self):
        """Update visibility of media rows based on folder filters."""
        for row in self.media_rows:
            row_parent = str(row.path.parent)
            is_visible = row_parent not in self.hidden_folders
            row.setVisible(is_visible)

    def _connect_upload_manager_signals(self):
        """Connect upload manager signals to UI handlers."""
        self.upload_manager.upload_started.connect(self._on_upload_started)
        self.upload_manager.upload_progress.connect(self._on_upload_progress)
        self.upload_manager.upload_completed.connect(self._on_upload_completed)
        self.upload_manager.batch_progress.connect(self._on_batch_progress)
        self.upload_manager.batch_completed.connect(self._on_batch_completed)

    def _on_auth_state_changed(self, is_authenticated: bool):
        """Handle authentication state changes."""
        # Update upload manager with new auth manager
        self.upload_manager = UploadManager(self.auth_widget.auth_manager)
        self._connect_upload_manager_signals()

        # Update all media rows with new upload manager
        for row in self.media_rows:
            row.set_upload_manager(self.upload_manager)

        self._update_upload_button_state()

        if is_authenticated:
            self.status_label.setText("")
        else:
            self.status_label.setText("")

    def _update_upload_button_state(self):
        """Update upload button state based on authentication and selection."""
        is_ready = (
            self.upload_manager and self.upload_manager.is_ready()
            if self.upload_manager
            else False
        )
        has_selected = any(row.is_selected() for row in self.media_rows)

        self.batch_upload_btn.setEnabled(is_ready and has_selected)

        if not is_ready:
            self.batch_upload_btn.setToolTip(
                "Please login with Google to upload to YouTube"
            )
        elif not has_selected:
            self.batch_upload_btn.setToolTip("Select files to upload")
        else:
            self.batch_upload_btn.setToolTip("Upload selected files to YouTube")

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Media Folder", str(self.current_folder)
        )
        if folder:
            self.current_folder = Path(folder)
            self._update_folder_button_text()
            self._scan_folder(self.current_folder)

    def _update_folder_button_text(self):
        """Update the folder button text with truncated path."""
        path_str = str(self.current_folder)

        # Truncate path if too long
        max_length = 60
        if len(path_str) > max_length:
            # Try to show the most relevant part (end of path)
            parts = path_str.split("\\")
            if len(parts) > 2:
                # Show last 2 parts with ellipsis
                truncated = "..." + "\\" + "\\".join(parts[-2:])
            else:
                # Just truncate from the beginning
                truncated = "..." + path_str[-(max_length - 3) :]
            path_str = truncated

        self.folder_btn.setText(f"📁 {path_str}")

    def _scan_current_folder(self):
        self._scan_folder(self.current_folder)

    def _reload_current_folder(self):
        """Reload and rescan the current folder."""
        # The _scan_folder method now handles all status updates
        self._scan_folder(self.current_folder)

    def _scan_folder(self, folder_path: Path):
        """Scan a folder for media files and create media rows."""
        try:
            # Show scanning indicator
            self.status_label.setText("🔍 Scanning folder...")
            QApplication.processEvents()  # Update UI immediately

            # Clear existing media rows
            for row in self.media_rows:
                row.cleanup()
                row.deleteLater()
            self.media_rows.clear()

            # Find media files with progress updates
            media_items = self._find_media_with_progress(folder_path)

            # Show processing indicator
            self.status_label.setText(f"📁 Processing {len(media_items)} files...")
            QApplication.processEvents()

            # Create media rows in batches for better responsiveness
            batch_size = 5
            for i in range(0, len(media_items), batch_size):
                batch = media_items[i : i + batch_size]

                for item in batch:
                    row = MediaRow(item, self)
                    self.media_rows.append(row)
                    self.media_layout.addWidget(row)

                # Update progress every batch
                if len(media_items) > batch_size:
                    progress = min(100, int((i + batch_size) / len(media_items) * 100))
                    self.status_label.setText(f"📁 Processing files... {progress}%")
                    QApplication.processEvents()

            # Update folder chip bar with current media paths
            media_paths = [row.path for row in self.media_rows]
            self.folder_chip_bar.update_folders(media_paths)

            # Apply current sorting
            self._apply_sorting()

            # Apply folder filtering
            self._update_media_visibility()

            # Update final status
            if self.media_rows:
                self.status_label.setText(
                    f"✅ Found {len(self.media_rows)} media files"
                )
            else:
                self.status_label.setText("✅ No media files found")

        except Exception as e:
            self.status_label.setText(f"❌ Error scanning folder: {e}")

    def _find_media_with_progress(self, folder_path: Path):
        """Find media files with progress updates (recursive but efficient)."""
        media_items = []

        if not folder_path.exists() or not folder_path.is_dir():
            return media_items

        # Supported media extensions
        media_extensions = {
            ".mp3",
            ".mp4",
            ".wav",
            ".flac",
            ".m4a",
            ".avi",
            ".mov",
            ".mkv",
        }

        # Count total files first for progress (only media files)
        total_files = 0
        for file_path in folder_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                total_files += 1

        processed_files = 0

        # Scan recursively but only process media files
        for file_path in folder_path.rglob("*"):
            # Skip non-files and non-media files early
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in media_extensions:
                continue

            processed_files += 1

            # Update progress every 10 files or 20% progress
            if (
                processed_files % 10 == 0
                or processed_files % max(1, total_files // 5) == 0
            ):
                progress = min(100, int(processed_files / total_files * 100))
                self.status_label.setText(
                    f"Scanning... {progress}% ({processed_files}/{total_files} media files)"
                )
                QApplication.processEvents()

            try:
                # Create MediaItem with only the parameters it accepts
                media_item = MediaItem(
                    path=file_path,
                    title=file_path.stem,  # Use filename without extension as title
                )
                media_items.append(media_item)
            except (OSError, PermissionError) as e:
                continue

        return media_items

    def _update_batch_button(self):
        selected_count = sum(1 for row in self.media_rows if row.is_selected())
        self.batch_upload_btn.setEnabled(
            self.upload_manager.is_ready() and selected_count > 0
        )
        if selected_count > 0:
            self.batch_upload_btn.setText(f"🚀 Upload Selected ({selected_count})")
        else:
            self.batch_upload_btn.setText("🚀 Upload Selected")

    def _setup_sorting_ui(self, parent_layout: QVBoxLayout):
        """Setup the sorting controls UI."""
        # Create a compact horizontal layout for sorting controls
        sort_layout = QHBoxLayout()
        sort_layout.setContentsMargins(12, 4, 12, 4)  # Compact margins
        sort_layout.setSpacing(8)

        # Sort label
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                font-weight: 500;
                padding: 4px 0px;
            }}
        """
        )
        sort_layout.addWidget(sort_label)

        # Sort field dropdown
        self.sort_field_combo = QComboBox()
        self.sort_field_combo.addItems(
            ["Name", "Size", "Duration", "Date", "Type", "Uploaded", "Rendered"]
        )
        self.sort_field_combo.setCurrentText("Name")
        self.sort_field_combo.setStyleSheet(
            f"""
            QComboBox {{
                padding: 4px 8px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 10px;
                min-width: 80px;
                max-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {theme.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {theme.text_secondary};
                margin-right: 4px;
            }}
        """
        )
        self.sort_field_combo.currentTextChanged.connect(self._on_sort_field_changed)
        sort_layout.addWidget(self.sort_field_combo)

        # Sort direction button
        self.sort_direction_btn = QPushButton("↑")
        self.sort_direction_btn.setToolTip(
            "Toggle sort direction (Ascending/Descending)"
        )
        self.sort_direction_btn.setStyleSheet(
            f"""
            QPushButton {{
                padding: 4px 8px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
                min-width: 24px;
                max-width: 24px;
            }}
            QPushButton:hover {{
                border-color: {theme.primary};
                background: {theme.background_secondary};
            }}
        """
        )
        self.sort_direction_btn.clicked.connect(self._on_sort_direction_changed)
        sort_layout.addWidget(self.sort_direction_btn)

        # Clear sort button
        self.clear_sort_btn = QPushButton("Clear")
        self.clear_sort_btn.setToolTip("Clear sorting and restore original order")
        self.clear_sort_btn.setStyleSheet(
            f"""
            QPushButton {{
                padding: 4px 8px;
                background: {theme.background_elevated};
                color: {theme.text_secondary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 10px;
                min-width: 50px;
            }}
            QPushButton:hover {{
                border-color: {theme.primary};
                background: {theme.background_secondary};
                color: {theme.text_primary};
            }}
        """
        )
        self.clear_sort_btn.clicked.connect(self._on_clear_sort)
        sort_layout.addWidget(self.clear_sort_btn)

        # Reload button
        self.reload_btn = QPushButton("🔄")
        self.reload_btn.setToolTip("Rescan and reload current directory")
        self.reload_btn.setStyleSheet(
            f"""
            QPushButton {{
                padding: 4px 8px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 12px;
                min-width: 24px;
                max-width: 24px;
            }}
            QPushButton:hover {{
                border-color: {theme.primary};
                background: {theme.background_secondary};
            }}
            QPushButton:pressed {{
                background: {theme.background_tertiary};
            }}
        """
        )
        self.reload_btn.clicked.connect(self._reload_current_folder)
        sort_layout.addWidget(self.reload_btn)

        sort_layout.addStretch()
        parent_layout.addLayout(sort_layout)

    def _on_sort_field_changed(self, field: str):
        """Handle sort field change."""
        self.current_sort_field = field.lower()
        self._apply_sorting()

    def _on_sort_direction_changed(self):
        """Handle sort direction toggle."""
        self.current_sort_reverse = not self.current_sort_reverse
        self.sort_direction_btn.setText("↓" if self.current_sort_reverse else "↑")
        self._apply_sorting()

    def _on_clear_sort(self):
        """Clear sorting and restore original order."""
        self.current_sort_field = "name"
        self.current_sort_reverse = False
        self.sort_field_combo.setCurrentText("Name")
        self.sort_direction_btn.setText("↑")
        self._apply_sorting()

    def _apply_sorting(self):
        """Apply sorting to media rows."""
        if not self.media_rows:
            return

        # Sort the media rows based on current settings
        self.media_rows.sort(key=self._get_sort_key, reverse=self.current_sort_reverse)

        # Reorder widgets in the layout
        for i, row in enumerate(self.media_rows):
            # Remove from current position
            self.media_layout.removeWidget(row)
            # Insert at new position (before the stretch)
            self.media_layout.insertWidget(i, row)

    def _get_sort_key(self, row):
        """Get sort key for a media row."""
        field = self.current_sort_field

        if field == "name":
            return row.path.name.lower()

        elif field == "size":
            try:
                return row.path.stat().st_size
            except Exception:
                return 0

        elif field == "duration":
            try:
                # Try to get duration from media info widget
                duration_text = row.media_info.duration_label.text()
                if duration_text and duration_text != "Unknown":
                    # Parse MM:SS format
                    if ":" in duration_text:
                        parts = duration_text.split(":")
                        return int(parts[0]) * 60 + int(parts[1])
                return 0
            except Exception:
                return 0

        elif field == "date":
            try:
                return row.path.stat().st_mtime
            except Exception:
                return 0

        elif field == "type":
            return row.path.suffix.lower()

        elif field == "uploaded":
            # Check if this file has been uploaded to YouTube
            try:
                uploads = self.history_manager.get_recent_uploads(
                    limit=1000
                )  # Get all uploads
                for upload in uploads:
                    if upload.get("original_file") == str(row.path):
                        return 1  # Has been uploaded
                return 0  # Not uploaded
            except Exception:
                return 0

        elif field == "rendered":
            # Check if this file has been converted/rendered
            try:
                conversions = self.history_manager.get_recent_conversions(
                    limit=1000
                )  # Get all conversions
                for conversion in conversions:
                    if conversion.get("mp3_file") == str(row.path):
                        return 1  # Has been rendered/converted
                return 0  # Not rendered
            except Exception:
                return 0

        else:
            return row.path.name.lower()

    def refresh_sorting(self):
        """Refresh sorting when media info is updated."""
        if self.current_sort_field != "name":
            self._apply_sorting()

    def _show_history(self):
        """Show the history dialog."""
        from PySide6.QtWidgets import QDialog

        dialog = QDialog(self)
        dialog.setWindowTitle("Media Uploader - History")
        dialog.setModal(True)
        dialog.resize(600, 500)

        # Apply dark theme
        dialog.setStyleSheet(StyleBuilder.main_window())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add history widget
        history_widget = HistoryWidget(self.history_manager, dialog)
        layout.addWidget(history_widget)

        dialog.exec()

    def _upload_selected(self):
        # Check if upload manager is ready
        if not self.upload_manager or not self.upload_manager.is_ready():
            QMessageBox.warning(
                self,
                "Authentication Required",
                "Please login with Google to upload to YouTube.",
            )
            return

        selected_rows = [row for row in self.media_rows if row.is_selected()]
        if not selected_rows:
            return

        # Prepare upload data
        uploads = []
        for row in selected_rows:
            uploads.append(
                (
                    row.path,
                    row.title.text().strip(),
                    row.description.toPlainText().strip(),
                )
            )

        try:
            # Start batch upload
            request_ids = self.upload_manager.start_batch_upload(uploads)

            # Update UI
            self.batch_upload_btn.setEnabled(False)
            self.batch_upload_btn.setText("⏳ Uploading...")
            self.status_label.setText(f"⚡ Started {len(uploads)} uploads")

        except ValueError as e:
            QMessageBox.warning(self, "Upload Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Upload Error", f"Failed to start uploads: {e}")

    def _on_upload_started(self, request_id: str):
        """Handle individual upload started."""
        # Find the media row for this upload and update its status
        for row in self.media_rows:
            if row.upload_request_id == request_id:
                row.upload_status.set_status("uploading", "Upload started...")
                break

    def _on_upload_progress(
        self, request_id: str, percent: int, status: str, message: str
    ):
        """Handle upload progress updates."""
        # Forward to the appropriate media row
        for row in self.media_rows:
            row.on_upload_progress(request_id, percent, status, message)

    def _on_upload_completed(self, request_id: str, success: bool, info: str):
        """Handle individual upload completion."""
        # Forward to the appropriate media row
        for row in self.media_rows:
            row.on_upload_completed(request_id, success, info)

    def _on_batch_progress(self, total: int, completed: int, failed: int):
        """Handle batch upload progress."""
        self.upload_summary.update_progress(completed, failed)

    def _on_batch_completed(self, total_completed: int, total_failed: int):
        """Handle batch upload completion."""
        # Update UI
        self.batch_upload_btn.setEnabled(True)
        self.batch_upload_btn.setText("🚀 Upload Selected")

        # Complete the summary widget
        self.upload_summary.complete_batch(total_completed, total_failed)

        # Update status
        if total_failed == 0:
            self.status_label.setText(f"🎉 All {total_completed} uploads completed!")
        elif total_completed == 0:
            self.status_label.setText(f"💥 All {total_failed} uploads failed")
        else:
            self.status_label.setText(
                f"⚠️ {total_completed} succeeded, {total_failed} failed"
            )

    def closeEvent(self, event):
        """Handle application close event."""
        # Clean up media rows
        for row in self.media_rows:
            row.cleanup()

        # Clear the list
        self.media_rows.clear()

        # Clean up upload manager if it exists
        if self.upload_manager:
            self.upload_manager.cleanup()

        # Accept the close event
        event.accept()
