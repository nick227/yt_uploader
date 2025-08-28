from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, Signal
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

# Lazy imports for better performance
from core.config import WINDOW_MIN_SIZE, WINDOW_TITLE
from core.models import MediaItem
from .auth_widget import AuthWidget
from .folder_chip_bar import FolderChipBar
from .media_row import MediaRow
from .upload_summary import UploadSummaryWidget
from core.upload_manager import UploadManager


class LazyLoadingThread(QThread):
    """Thread for lazy loading media items to prevent UI blocking."""
    
    progress_updated = Signal(int, int)  # current, total
    items_loaded = Signal(list)  # list of MediaItem paths
    loading_complete = Signal()
    
    def __init__(self, folder_path: Path, batch_size: int = 50):
        super().__init__()
        self.folder_path = folder_path
        self.batch_size = batch_size
        self._is_cancelled = False
        
    def cancel(self):
        """Cancel the loading operation."""
        self._is_cancelled = True
        
    def run(self):
        """Scan folder and emit media items in batches."""
        try:
            media_extensions = {".mp3", ".mp4", ".wav", ".flac", ".m4a", ".avi", ".mov", ".mkv"}
            
            # First pass: count total files
            total_files = 0
            for file_path in self.folder_path.rglob("*"):
                if self._is_cancelled:
                    return
                if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                    total_files += 1
            
            if total_files == 0:
                self.loading_complete.emit()
                return
            
            # Second pass: emit items in batches
            current_batch = []
            processed_files = 0
            
            for file_path in self.folder_path.rglob("*"):
                if self._is_cancelled:
                    return
                    
                if not file_path.is_file() or file_path.suffix.lower() not in media_extensions:
                    continue
                
                try:
                    # Create lightweight MediaItem (no heavy operations)
                    media_item = MediaItem(
                        path=file_path,
                        title=file_path.stem,
                    )
                    current_batch.append(media_item)
                    processed_files += 1
                    
                    # Emit batch when full
                    if len(current_batch) >= self.batch_size:
                        self.items_loaded.emit(current_batch)
                        self.progress_updated.emit(processed_files, total_files)
                        current_batch = []
                        
                except (OSError, PermissionError):
                    continue
            
            # Emit final batch
            if current_batch:
                self.items_loaded.emit(current_batch)
                self.progress_updated.emit(processed_files, total_files)
            
            self.loading_complete.emit()
            
        except Exception as e:
            print(f"Error in lazy loading thread: {e}")
            self.loading_complete.emit()


class VirtualScrollArea(QScrollArea):
    """Virtual scrolling area that only creates widgets for visible items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_items = []  # All MediaItem objects
        self.visible_widgets = {}  # Dict of visible widgets: index -> MediaRow
        self.widget_height = 120  # Estimated height of each MediaRow
        self.buffer_size = 5  # Number of widgets to keep above/below visible area
        
    def set_items(self, items):
        """Set all items and clear visible widgets."""
        self.all_items = items
        self.visible_widgets.clear()
        self._update_visible_widgets()
        
    def _update_visible_widgets(self):
        """Update which widgets are visible based on scroll position."""
        if not self.all_items:
            return
            
        # Get current scroll position
        scroll_pos = self.verticalScrollBar().value()
        viewport_height = self.viewport().height()
        
        # Calculate visible range
        start_index = max(0, scroll_pos // self.widget_height - self.buffer_size)
        end_index = min(len(self.all_items), (scroll_pos + viewport_height) // self.widget_height + self.buffer_size)
        
        # Remove widgets that are no longer visible
        widgets_to_remove = []
        for index, widget in self.visible_widgets.items():
            if index < start_index or index >= end_index:
                widgets_to_remove.append(index)
                
        for index in widgets_to_remove:
            widget = self.visible_widgets.pop(index)
            widget.setParent(None)
            widget.deleteLater()
        
        # Add widgets that are now visible
        for index in range(start_index, end_index):
            if index not in self.visible_widgets:
                item = self.all_items[index]
                widget = self._create_widget_for_item(item, index)
                self.visible_widgets[index] = widget
                
    def _create_widget_for_item(self, item, index):
        """Create a widget for a specific item."""
        # This will be implemented by the parent class
        pass
        
    def resizeEvent(self, event):
        """Handle resize events to update visible widgets."""
        super().resizeEvent(event)
        self._update_visible_widgets()
        
    def scrollContentsBy(self, dx, dy):
        """Handle scroll events to update visible widgets."""
        super().scrollContentsBy(dx, dy)
        self._update_visible_widgets()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)

        # Set initial opacity to 0 for fade-in effect
        self.setWindowOpacity(0.0)

        # Lazy load heavy modules
        from core.styles import StyleBuilder

        self.setStyleSheet(StyleBuilder.main_window())

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        layout = QVBoxLayout(central)
        from core.styles import LayoutHelper

        LayoutHelper.set_standard_spacing(layout)
        layout.setSpacing(4)  # Reduce spacing between sections
        
        # Create loading overlay to prevent jitter visibility
        self.loading_overlay = QWidget(central)
        self.loading_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(35, 35, 35, 0.95);
                border: none;
            }
        """)
        self.loading_overlay.setVisible(True)
        self.loading_overlay.raise_()

        # Initialize managers (defer auth setup to avoid blocking)
        self.auth_widget = None  # Will be initialized after window shows
        self.upload_manager = None  # Will be initialized after auth
        from core.history_manager import HistoryManager

        self.history_manager = HistoryManager()

        # Initialize settings manager
        from core.settings_manager import SettingsManager
        try:
            self.settings_manager = SettingsManager()
        except Exception as e:
            # If settings manager fails to initialize, create a minimal one
            print(f"Warning: Failed to initialize settings manager: {e}")
            self.settings_manager = None

        # Initialize media persistence service
        from core.media_persistence_service import MediaPersistenceService
        try:
            self.media_persistence_service = MediaPersistenceService()

            # Perform initial cleanup of invalid paths
            if self.media_persistence_service:
                cleaned_count = self.media_persistence_service.cleanup_invalid_paths()
                if cleaned_count > 0:
                    print(f"🧹 Initial cleanup: Removed {cleaned_count} invalid paths")

        except Exception as e:
            # If persistence service fails to initialize, create a minimal one
            print(f"Warning: Failed to initialize media persistence service: {e}")
            self.media_persistence_service = None

        # Initialize sorting state
        self.current_sort_field = "name"
        self.current_sort_reverse = False

        # Lazy loading state
        self.all_media_items = []  # All MediaItem objects (lightweight)
        self.media_rows = []  # Only visible MediaRow widgets
        self.lazy_loading_thread = None
        self.is_loading = False

        # Top toolbar with fixed height
        toolbar_container = QWidget()
        toolbar_container.setFixedHeight(40)  # Fixed height for toolbar
        toolbar_container.setStyleSheet("QWidget { background: transparent; }")

        toolbar = QHBoxLayout(toolbar_container)
        toolbar.setContentsMargins(12, 2, 12, 2)  # Very compact margins
        toolbar.setSpacing(8)  # Reduce spacing between elements

        # Combined folder button and path display
        self.folder_btn = QPushButton()
        from core.styles import theme

        self.folder_btn.setStyleSheet(
            f"""
            QPushButton {{
                padding: 4px 12px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 10px;
                font-weight: 500;
                min-height: 16px;
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
        # Initialize with current directory or last used path
        try:
            last_media_path = self.settings_manager.get_last_media_path() if self.settings_manager else None
            if last_media_path:
                self.current_folder = last_media_path
            else:
                self.current_folder = Path.cwd()
        except Exception as e:
            # If there's any error, fall back to current directory
            print(f"Warning: Failed to load last media path: {e}")
            self.current_folder = Path.cwd()

        self.folder_btn.clicked.connect(self._choose_folder)
        self._update_folder_button_text()
        toolbar.addWidget(self.folder_btn, 1)  # Take up available space

        # History button
        self.history_btn = QPushButton("📋 History")
        from core.styles import StyleBuilder

        self.history_btn.setStyleSheet(StyleBuilder.button_secondary())
        self.history_btn.clicked.connect(self._show_history)
        toolbar.addWidget(self.history_btn)

        # Upload button
        self.batch_upload_btn = QPushButton("All")
        self.batch_upload_btn.setStyleSheet(StyleBuilder.button_danger())
        self.batch_upload_btn.clicked.connect(self._upload_selected)
        self.batch_upload_btn.setEnabled(False)
        toolbar.addWidget(self.batch_upload_btn)

        layout.addWidget(toolbar_container)

        # Sorting controls (now includes folder chips in two-column layout)
        self._setup_sorting_ui(layout)

        # Status label for user feedback with fixed height
        status_container = QWidget()
        status_container.setFixedHeight(40)  # Fixed height for status
        status_container.setStyleSheet("QWidget { background: transparent; }")

        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(20, 0, 20, 0)  # Left padding for alignment

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 11px;
                margin: 0px;
            }}
        """
        )
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_container)

        # Upload summary widget with fixed height
        self.upload_summary = UploadSummaryWidget(self)
        self.upload_summary.setFixedHeight(0)  # Start with zero height
        self.upload_summary.setVisible(False)  # Initially hidden
        layout.addWidget(self.upload_summary)

        # Media list area with enhanced styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(StyleBuilder.scroll_area())
        
        # Connect scroll events for lazy loading
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

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
        
        # Start fade-in animation after a short delay
        QTimer.singleShot(50, self._start_fade_in_animation)

    def _start_fade_in_animation(self):
        """Start the fade-in animation for smooth appearance."""
        # Hide loading overlay first
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setVisible(False)
        
        # Create fade-in animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(800)  # 800ms fade-in
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Start the animation
        self.fade_animation.start()

    def resizeEvent(self, event):
        """Handle window resize to ensure loading overlay covers entire window."""
        super().resizeEvent(event)
        
        # Update loading overlay size to match window
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(0, 0, self.width(), self.height())

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
        # Filter the all_media_items list first
        visible_items = []
        for item in self.all_media_items:
            item_parent = str(item.path.parent)
            if item_parent not in self.hidden_folders:
                visible_items.append(item)
        
        # Update the all_media_items list with filtered items
        self.all_media_items = visible_items
        
        # Recreate visible widgets
        self._recreate_visible_widgets()

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

        # Update all visible media rows with new upload manager
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
        # Check selection across all items, not just visible widgets
        has_selected = any(
            hasattr(item, 'is_selected') and item.is_selected() 
            for item in self.all_media_items
        ) or any(row.is_selected() for row in self.media_rows)

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
            # Save the selected path for next time
            try:
                if self.settings_manager:
                    self.settings_manager.set_last_media_path(self.current_folder)
            except Exception as e:
                print(f"Warning: Failed to save last media path: {e}")
            self._update_folder_button_text()
            self._start_lazy_loading(self.current_folder)

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
                truncated = "..." + path_str[-(max_length - 3):]
            path_str = truncated

        self.folder_btn.setText(f"📁 {path_str}")

    def _scan_current_folder(self):
        """Start lazy loading of the current folder."""
        self._start_lazy_loading(self.current_folder)

    def _reload_current_folder(self):
        """Reload and rescan the current folder."""
        self._start_lazy_loading(self.current_folder)

    def _start_lazy_loading(self, folder_path: Path):
        """Start lazy loading of media items from a folder."""
        if self.is_loading:
            # Cancel previous loading operation
            if self.lazy_loading_thread:
                self.lazy_loading_thread.cancel()
                self.lazy_loading_thread.wait()
        
        try:
            # Clear existing items and widgets
            self.all_media_items.clear()
            for row in self.media_rows:
                row.cleanup()
                row.deleteLater()
            self.media_rows.clear()
            
            # Clear the media layout
            while self.media_layout.count() > 1:  # Keep the stretch item
                child = self.media_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Show scanning indicator
            self.status_label.setText("🔍 Scanning folder...")
            QApplication.processEvents()
            
            # Start lazy loading thread
            self.is_loading = True
            self.lazy_loading_thread = LazyLoadingThread(folder_path, batch_size=20)
            self.lazy_loading_thread.progress_updated.connect(self._on_loading_progress)
            self.lazy_loading_thread.items_loaded.connect(self._on_items_loaded)
            self.lazy_loading_thread.loading_complete.connect(self._on_loading_complete)
            self.lazy_loading_thread.start()
            
        except Exception as e:
            self.status_label.setText(f"❌ Error starting scan: {e}")
            self.is_loading = False

    def _on_loading_progress(self, current: int, total: int):
        """Handle loading progress updates."""
        if total > 0:
            progress = min(100, int(current / total * 100))
            self.status_label.setText(f"🔍 Scanning... {progress}% ({current}/{total} files)")
        else:
            self.status_label.setText("🔍 Scanning folder...")
        QApplication.processEvents()

    def _on_items_loaded(self, items: list):
        """Handle new items loaded from the background thread."""
        try:
            # Add items to our collection
            self.all_media_items.extend(items)
            
            # Create widgets only for the first batch (visible items)
            if len(self.media_rows) == 0:
                self._create_initial_widgets()
            
            # Update status
            self.status_label.setText(f"📁 Found {len(self.all_media_items)} media files")
            
        except Exception as e:
            print(f"Error processing loaded items: {e}")

    def _on_loading_complete(self):
        """Handle completion of lazy loading."""
        try:
            self.is_loading = False
            
            # Apply sorting to all items
            self._apply_sorting_to_items()
            
            # Update folder chip bar
            media_paths = [item.path for item in self.all_media_items]
            self.folder_chip_bar.update_folders(media_paths)
            
            # Apply folder filtering
            self._update_media_visibility()
            
            # Update final status
            if self.all_media_items:
                self.status_label.setText(f"✅ Loaded {len(self.all_media_items)} media files")
            else:
                self.status_label.setText("✅ No media files found")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error completing scan: {e}")

    def _create_initial_widgets(self):
        """Create widgets for the first visible items."""
        try:
            # Create widgets for first 10 items (or all if less than 10)
            initial_count = min(10, len(self.all_media_items))
            
            for i in range(initial_count):
                item = self.all_media_items[i]
                row = self._create_media_row(item)
                self.media_rows.append(row)
                self.media_layout.insertWidget(i, row)  # Insert before stretch
                
        except Exception as e:
            print(f"Error creating initial widgets: {e}")

    def _create_media_row(self, item: MediaItem):
        """Create a MediaRow widget for a MediaItem."""
        from .media_row import MediaRow
        return MediaRow(item, self)

    def _apply_sorting_to_items(self):
        """Apply sorting to the all_media_items list."""
        try:
            if self.current_sort_field == "name":
                self.all_media_items.sort(key=lambda x: x.filename.lower(), reverse=self.current_sort_reverse)
            elif self.current_sort_field == "size":
                self.all_media_items.sort(key=lambda x: x.size_mb, reverse=self.current_sort_reverse)
            elif self.current_sort_field == "duration":
                self.all_media_items.sort(key=lambda x: x.duration_ms or 0, reverse=self.current_sort_reverse)
            elif self.current_sort_field == "date":
                self.all_media_items.sort(key=lambda x: x.path.stat().st_mtime, reverse=self.current_sort_reverse)
                
        except Exception as e:
            print(f"Error applying sorting: {e}")

    def _on_scroll(self, value):
        """Handle scroll events to trigger lazy loading."""
        if not self.all_media_items or self.is_loading:
            return
            
        # Check if we're near the bottom (within 2 items)
        scrollbar = self.scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()
        threshold = max_value - (2 * 120)  # 2 items worth of scrolling
        
        if value >= threshold:
            self._load_more_widgets()

    def _load_more_widgets(self):
        """Load more widgets when user scrolls near the bottom."""
        if self.is_loading or len(self.media_rows) >= len(self.all_media_items):
            return
            
        # Load next batch of widgets
        current_count = len(self.media_rows)
        batch_size = 5
        end_index = min(current_count + batch_size, len(self.all_media_items))
        
        for i in range(current_count, end_index):
            item = self.all_media_items[i]
            row = self._create_media_row(item)
            self.media_rows.append(row)
            self.media_layout.insertWidget(i, row)  # Insert before stretch

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
        """Setup the sorting controls UI with two-column layout."""
        from core.styles import theme

        # Create a container widget with fixed height for the sorting row
        sort_row_container = QWidget()
        sort_row_container.setFixedHeight(36)  # Fixed height for sorting row
        sort_row_container.setStyleSheet("QWidget { background: transparent; }")

        # Create a horizontal layout for the two-column structure
        sort_row_layout = QHBoxLayout(sort_row_container)
        sort_row_layout.setContentsMargins(12, 2, 12, 2)  # Very compact margins
        sort_row_layout.setSpacing(12)  # Space between left and right columns

        # LEFT COLUMN: Sorting controls
        sort_layout = QHBoxLayout()
        sort_layout.setContentsMargins(0, 0, 0, 0)  # No margins for nested layout
        sort_layout.setSpacing(6)  # Reduce spacing between controls

        # Sort label
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                font-weight: 500;
                padding: 2px 0px;
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
                padding: 2px 6px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 4px;
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
                padding: 2px 6px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                min-width: 20px;
                max-width: 20px;
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
                padding: 2px 6px;
                background: {theme.background_elevated};
                color: {theme.text_secondary};
                border: 1px solid {theme.border};
                border-radius: 4px;
                font-size: 10px;
                min-width: 40px;
            }}
            QPushButton:hover {{
                border-color: {theme.primary};
                background: {theme.background_secondary};
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

        # Add left column to main row layout
        sort_row_layout.addLayout(sort_layout)

        # RIGHT COLUMN: Folder chips
        # Create folder chip bar for filtering
        from .folder_chip_bar import FolderChipBar

        self.folder_chip_bar = FolderChipBar()
        self.folder_chip_bar.folder_toggled.connect(self._on_folder_toggled)
        sort_row_layout.addWidget(self.folder_chip_bar, 1)  # Take remaining space

        # Add the two-column row to parent layout
        parent_layout.addWidget(sort_row_container)

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
        """Apply sorting to media rows (for backward compatibility)."""
        # This method now delegates to the new lazy loading system
        if self.all_media_items:
            self._apply_sorting_to_items()
            self._recreate_visible_widgets()

    def _recreate_visible_widgets(self):
        """Recreate visible widgets after sorting."""
        try:
            # Clear existing widgets
            for row in self.media_rows:
                row.cleanup()
                row.deleteLater()
            self.media_rows.clear()
            
            # Clear the media layout
            while self.media_layout.count() > 1:  # Keep the stretch item
                child = self.media_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Recreate initial widgets
            self._create_initial_widgets()
            
        except Exception as e:
            print(f"Error recreating widgets: {e}")

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
        from core.styles import StyleBuilder

        dialog.setStyleSheet(StyleBuilder.main_window())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add history widget
        from .history_widget import HistoryWidget

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
        """Handle window close event."""
        try:
            # Cleanup persistence service
            if hasattr(self, 'media_persistence_service') and self.media_persistence_service:
                self.media_persistence_service.shutdown()
                print("✅ Persistence service shutdown completed")

            # Cleanup settings manager
            if hasattr(self, 'settings_manager') and self.settings_manager:
                # Settings are auto-saved, just log
                print("✅ Settings manager cleanup completed")

            # Cleanup media rows
            for row in self.media_rows:
                row.cleanup()

            print("✅ MainWindow cleanup completed")

        except Exception as e:
            print(f"⚠️ Warning: Error during cleanup: {e}")

        # Accept the close event
        event.accept()

    def _show_persistence_stats(self):
        """Show persistence statistics for monitoring."""
        if not hasattr(self, 'media_persistence_service') or not self.media_persistence_service:
            QMessageBox.information(self, "Persistence Stats", "Persistence service not available")
            return

        try:
            stats = self.media_persistence_service.get_statistics()

            message = f"""
📊 Persistence Statistics:

📁 Total Media Entries: {stats.get('total_entries', 0) }
📝 Titles Saved: {stats.get('titles_saved', 0) }
📄 Descriptions Saved: {stats.get('descriptions_saved', 0) }
🖼️ Images Saved: {stats.get('images_saved', 0)}
💾 File Size: {stats.get('file_size_mb', 0) :.2f} MB
            """.strip()

            QMessageBox.information(self, "Persistence Statistics", message)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to get persistence statistics: {e}")
