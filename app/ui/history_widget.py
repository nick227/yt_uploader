# app/ui/history_widget.py
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.styles import LayoutHelper, StyleBuilder, theme


class HistoryItemWidget(QWidget):
    """Individual history item widget."""

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self._setup_ui()

    def _setup_ui(self):
        """Setup the history item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # Icon and type
        icon_label = QLabel()
        if self.item_data.get("item_type") == "upload":
            icon_label.setText("📤")
            type_text = "Upload"
        else:
            icon_label.setText("🔄")
            type_text = "Conversion"

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 16px;
                color: {theme.text_primary};
            }}
        """
        )
        content_layout.addWidget(icon_label)

        # Content
        content_widget = QWidget()
        content_layout_widget = QVBoxLayout(content_widget)
        content_layout_widget.setContentsMargins(0, 0, 0, 0)
        content_layout_widget.setSpacing(2)

        # Title/File name
        title_label = QLabel()
        if self.item_data.get("item_type") == "upload":
            title_label.setText(self.item_data.get("title", "Unknown"))
        else:
            # Show MP3 filename for conversions
            mp3_path = Path(self.item_data.get("mp3_file", ""))
            title_label.setText(mp3_path.name)

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_primary};
                font-size: 12px;
                font-weight: 600;
            }}
        """
        )
        content_layout_widget.addWidget(title_label)

        # Details
        if self.item_data.get("item_type") == "upload":
            video_url = self.item_data.get("video_url", "")
            if video_url:
                # Create clickable link for YouTube URLs
                link_style = f"color: {theme.primary}; text-decoration: none;"
                details_link = QLabel(
                    f"🎥 <a href='{video_url}' style='{link_style}'>{video_url}</a>"
                )
                details_link.setOpenExternalLinks(True)
                details_link.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {theme.text_secondary};
                        font-size: 10px;
                        cursor: pointer;
                    }}
                    QLabel a {{
                        color: {theme.primary};
                        text-decoration: none;
                    }}
                    QLabel a:hover {{
                        color: {theme.primary_hover};
                        text-decoration: underline;
                    }}
                """
                )
                content_layout_widget.addWidget(details_link)
            else:
                details_label = QLabel("🎥 No URL available")
                details_label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {theme.text_secondary};
                        font-size: 10px;
                    }}
                """
                )
                content_layout_widget.addWidget(details_label)
        else:
            mp4_path = Path(self.item_data.get("mp4_file", ""))
            details_label = QLabel(f"📹 {mp4_path.name}")
            details_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {theme.text_secondary};
                    font-size: 10px;
                }}
            """
            )
            content_layout_widget.addWidget(details_label)

        content_layout.addWidget(content_widget, 1)

        # Date
        date_label = QLabel()
        date_str = self.item_data.get("date", "")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_label.setText(dt.strftime("%m/%d/%Y %H:%M"))
            except Exception:
                date_label.setText(date_str)
        else:
            date_label.setText("Unknown date")

        date_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 10px;
                text-align: right;
            }}
        """
        )
        date_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        content_layout.addWidget(date_label)

        layout.addLayout(content_layout)

        # Styling
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {theme.background_elevated};
                border: 1px solid {theme.border};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background: {theme.background_secondary};
                border-color: {theme.primary};
            }}
        """
        )


class HistoryWidget(QWidget):
    """History viewer widget."""

    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """Setup the history viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("📋 History")
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_primary};
                font-size: 16px;
                font-weight: 600;
            }}
        """
        )
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(StyleBuilder.button_secondary())
        refresh_btn.clicked.connect(self._load_history)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Stats
        stats_label = QLabel()
        stats_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 11px;
                padding: 4px 0px;
            }}
        """
        )
        layout.addWidget(stats_label)
        self.stats_label = stats_label

        # Scroll area for history items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
        """
        )

        # Container for history items
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(8)
        self.history_layout.addStretch()  # Push items to top

        scroll_area.setWidget(self.history_container)
        layout.addWidget(scroll_area)

    def _load_history(self):
        """Load and display history items."""
        # Clear existing items
        while self.history_layout.count() > 1:  # Keep the stretch
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get history items
        history_items = self.history_manager.get_all_history(limit=50)

        # Update stats
        stats = self.history_manager.get_stats()
        stats_text = (
            f"📊 {stats['total_uploads']} uploads • "
            f"{stats['total_conversions']} conversions"
        )
        if stats["last_updated"]:
            try:
                dt = datetime.fromisoformat(
                    stats["last_updated"].replace("Z", "+00:00")
                )
                stats_text += f" • Last updated: {dt.strftime('%m/%d/%Y %H:%M')}"
            except Exception:
                pass
        self.stats_label.setText(stats_text)

        # Add history items
        for item_data in history_items:
            history_item = HistoryItemWidget(item_data, self)
            self.history_layout.insertWidget(
                self.history_layout.count() - 1, history_item
            )

        # Show message if no history
        if not history_items:
            no_history_label = QLabel(
                "No history yet. Uploads and conversions will appear here."
            )
            no_history_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {theme.text_secondary};
                    font-size: 12px;
                    text-align: center;
                    padding: 20px;
                }}
            """
            )
            no_history_label.setAlignment(Qt.AlignCenter)
            self.history_layout.insertWidget(
                self.history_layout.count() - 1, no_history_label
            )
