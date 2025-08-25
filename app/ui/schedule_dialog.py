# app/ui/schedule_dialog.py
from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.styles import StyleBuilder, theme


class ScheduleDialog(QDialog):
    """Dialog for scheduling YouTube video publication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduled_time = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the scheduling dialog UI."""
        self.setWindowTitle("Schedule Video Publication")
        self.setModal(True)
        self.resize(400, 200)
        self.setStyleSheet(StyleBuilder.main_window())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title_label = QLabel("📅 Schedule Video Publication")
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_primary};
                font-size: 16px;
                font-weight: 600;
                padding: 8px 0px;
            }}
        """
        )
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Choose when you want your video to be published on YouTube. "
            "The video will be uploaded immediately but won't be visible "
            "until the scheduled time."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 12px;
                line-height: 1.4;
                padding: 8px 0px;
            }}
        """
        )
        layout.addWidget(desc_label)

        # Date and time picker
        datetime_layout = QHBoxLayout()
        datetime_layout.setSpacing(12)

        # Date picker
        date_label = QLabel("Date & Time:")
        date_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_primary};
                font-size: 12px;
                font-weight: 500;
                padding: 4px 0px;
            }}
        """
        )
        datetime_layout.addWidget(date_label)

        # Set minimum date to tomorrow (YouTube requires future dates)
        tomorrow = datetime.now() + timedelta(days=1)
        min_datetime = QDateTime.fromString(
            tomorrow.strftime("%Y-%m-%d 12:00"), "yyyy-MM-dd HH:mm"
        )

        # Set default to tomorrow at 12:00 PM
        default_datetime = QDateTime.fromString(
            tomorrow.strftime("%Y-%m-%d 12:00"), "yyyy-MM-dd HH:mm"
        )

        self.datetime_picker = QDateTimeEdit(default_datetime)
        self.datetime_picker.setMinimumDateTime(min_datetime)
        self.datetime_picker.setCalendarPopup(True)
        self.datetime_picker.setDisplayFormat("MMM dd, yyyy h:mm AP")
        self.datetime_picker.setStyleSheet(
            f"""
            QDateTimeEdit {{
                padding: 8px 12px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 12px;
                min-width: 180px;
            }}
            QDateTimeEdit:hover {{
                border-color: {theme.primary};
            }}
            QDateTimeEdit:focus {{
                border-color: {theme.primary};
                background: {theme.background_secondary};
            }}
        """
        )
        datetime_layout.addWidget(self.datetime_picker)

        datetime_layout.addStretch()
        layout.addLayout(datetime_layout)

        # Quick time presets
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(8)

        presets_label = QLabel("Quick presets:")
        presets_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.text_secondary};
                font-size: 11px;
                padding: 4px 0px;
            }}
        """
        )
        presets_layout.addWidget(presets_label)

        # Preset buttons
        preset_times = [
            ("Tomorrow 9 AM", 1, 9),
            ("Tomorrow 12 PM", 1, 12),
            ("Tomorrow 6 PM", 1, 18),
            ("Next Week", 7, 12),
        ]

        for text, days, hour in preset_times:
            preset_btn = QPushButton(text)
            preset_btn.setStyleSheet(
                f"""
                QPushButton {{
                    padding: 4px 8px;
                    background: {theme.background_elevated};
                    color: {theme.text_secondary};
                    border: 1px solid {theme.border};
                    border-radius: 4px;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    border-color: {theme.primary};
                    color: {theme.primary};
                }}
            """
            )
            preset_btn.clicked.connect(
                lambda checked, d=days, h=hour: self._set_preset_time(d, h)
            )
            presets_layout.addWidget(preset_btn)

        presets_layout.addStretch()
        layout.addLayout(presets_layout)

        # Spacer
        layout.addStretch()

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        buttons_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(StyleBuilder.button_secondary())
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        # Schedule button
        schedule_btn = QPushButton("Schedule Upload")
        schedule_btn.setStyleSheet(StyleBuilder.button_primary())
        schedule_btn.clicked.connect(self._accept_schedule)
        buttons_layout.addWidget(schedule_btn)

        layout.addLayout(buttons_layout)

    def _set_preset_time(self, days: int, hour: int):
        """Set the datetime picker to a preset time."""
        target_date = datetime.now() + timedelta(days=days)
        target_date = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
        qdatetime = QDateTime.fromString(
            target_date.strftime("%Y-%m-%d %H:%M"), "yyyy-MM-dd HH:mm"
        )
        self.datetime_picker.setDateTime(qdatetime)

    def _accept_schedule(self):
        """Accept the scheduled time and close dialog."""
        selected_datetime = self.datetime_picker.dateTime().toPython()

        # Convert to ISO format for YouTube API
        self.scheduled_time = selected_datetime.isoformat() + "Z"

        self.accept()

    def get_scheduled_time(self) -> str:
        """Get the selected scheduled time in ISO format."""
        return self.scheduled_time
