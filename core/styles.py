"""
Centralized styling system for the Media Uploader application.

Provides consistent spacing, colors, and component styles.
"""

from dataclasses import dataclass
from typing import Final

# Ultra dark gray/black theme (Professional elegance)
COLORS = {
    # Primary colors (Dark gray theme)
    "primary": "#6b7280",
    "primary_hover": "#4b5563",
    "primary_pressed": "#374151",
    # Secondary colors (Neutral gray)
    "secondary": "#9ca3af",
    "secondary_hover": "#6b7280",
    "secondary_pressed": "#4b5563",
    # Success/Error/Warning (Very muted)
    "success": "#059669",
    "error": "#dc2626",
    "warning": "#d97706",
    # Text colors (High contrast, readable)
    "text_primary": "#f9fafb",
    "text_secondary": "#e5e7eb",
    "text_muted": "#9ca3af",
    # Background colors (Ultra dark gray/black)
    "background_primary": "#000000",
    "background_secondary": "#111111",
    "background_tertiary": "#1a1a1a",
    "background_elevated": "#2a2a2a",
    # Border colors (Minimal, elegant)
    "border": "#404040",
    "border_focus": "#6b7280",
    "border_error": "#404040",  # No red borders
    # Special effects (Subtle)
    "glow": "#6b7280",
    "shadow": "rgba(0, 0, 0, 0.5)",
}


# Spacing Scale (8px base unit)
class Spacing:
    """Spacing scale based on 8px increments."""

    XS: Final[int] = 4  # 4px
    S: Final[int] = 8  # 8px
    M: Final[int] = 12  # 12px
    L: Final[int] = 16  # 16px
    XL: Final[int] = 24  # 24px
    XXL: Final[int] = 32  # 32px
    XXXL: Final[int] = 48  # 48px


# Border Radius Scale
class BorderRadius:
    """Border radius scale."""

    S: Final[int] = 4  # 4px
    M: Final[int] = 8  # 8px
    L: Final[int] = 12  # 12px
    XL: Final[int] = 16  # 16px


# Font Sizes
class FontSize:
    """Font size scale."""

    XS: Final[int] = 10  # 10px
    S: Final[int] = 12  # 12px
    M: Final[int] = 14  # 14px
    L: Final[int] = 16  # 16px
    XL: Final[int] = 18  # 18px
    XXL: Final[int] = 24  # 24px


@dataclass
class StyleTheme:
    """Complete style theme with all styling information."""

    # Colors
    primary: str = COLORS["primary"]
    primary_hover: str = COLORS["primary_hover"]
    primary_pressed: str = COLORS["primary_pressed"]
    secondary: str = COLORS["secondary"]
    secondary_hover: str = COLORS["secondary_hover"]
    secondary_pressed: str = COLORS["secondary_pressed"]
    success: str = COLORS["success"]
    error: str = COLORS["error"]
    warning: str = COLORS["warning"]
    text_primary: str = COLORS["text_primary"]
    text_secondary: str = COLORS["text_secondary"]
    text_muted: str = COLORS["text_muted"]
    background_primary: str = COLORS["background_primary"]
    background_secondary: str = COLORS["background_secondary"]
    background_tertiary: str = COLORS["background_tertiary"]
    background_elevated: str = COLORS["background_elevated"]
    border: str = COLORS["border"]
    border_focus: str = COLORS["border_focus"]
    border_error: str = COLORS["border_error"]
    glow: str = COLORS["glow"]
    shadow: str = COLORS["shadow"]

    # Spacing
    spacing_xs: int = Spacing.XS
    spacing_s: int = Spacing.S
    spacing_m: int = Spacing.M
    spacing_l: int = Spacing.L
    spacing_xl: int = Spacing.XL
    spacing_xxl: int = Spacing.XXL

    # Border radius
    radius_s: int = BorderRadius.S
    radius_m: int = BorderRadius.M
    radius_l: int = BorderRadius.L

    # Font sizes
    font_xs: int = FontSize.XS
    font_s: int = FontSize.S
    font_m: int = FontSize.M
    font_l: int = FontSize.L


# Global theme instance
theme = StyleTheme()


class StyleBuilder:
    """Helper class for building CSS-style strings."""

    @staticmethod
    def button_primary() -> str:
        """Primary button style - uniform, small, rounded."""
        return f"""
            QPushButton {{
                padding: 6px 16px;
                background: {theme.primary};
                color: {theme.text_primary};
                border: 1px solid {theme.primary};
                border-radius: 8px;
                font-size: 10px;
                font-weight: 500;
                min-height: 20px;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background: {theme.primary_hover};
                border-color: {theme.primary_hover};
            }}
            QPushButton:pressed {{
                background: {theme.primary_pressed};
            }}
            QPushButton:disabled {{
                background: {theme.background_tertiary};
                color: {theme.text_muted};
                border-color: {theme.border};
            }}
        """

    @staticmethod
    def button_danger() -> str:
        """Danger button style - uniform, small, rounded."""
        return f"""
            QPushButton {{
                padding: 6px 16px;
                background: {theme.error};
                color: {theme.text_primary};
                border: 1px solid {theme.error};
                border-radius: 8px;
                font-size: 10px;
                font-weight: 500;
                min-height: 20px;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background: #b91c1c;
                border-color: #b91c1c;
            }}
            QPushButton:pressed {{
                background: #991b1b;
            }}
            QPushButton:disabled {{
                background: {theme.background_tertiary};
                color: {theme.text_muted};
                border-color: {theme.border};
            }}
        """

    @staticmethod
    def button_secondary() -> str:
        """Secondary button style - uniform, small, rounded."""
        return f"""
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
            }}
            QPushButton:hover {{
                background: {theme.background_secondary};
                border-color: {theme.primary};
            }}
            QPushButton:pressed {{
                background: {theme.background_tertiary};
            }}
            QPushButton:disabled {{
                background: {theme.background_tertiary};
                color: {theme.text_muted};
                border-color: {theme.border};
            }}
        """

    @staticmethod
    def input_field(has_error: bool = False) -> str:
        """Input field style - elegant, no red borders."""
        return f"""
            QLineEdit, QTextEdit {{
                padding: {theme.spacing_s}px;
                background: {theme.background_elevated};
                border: 1px solid {theme.border};
                border-radius: {theme.radius_s}px;
                color: {theme.text_primary};
                font-size: {theme.font_s}px;
                selection-background-color: {theme.primary};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {theme.border_focus};
                background: {theme.background_secondary};
            }}
            QLineEdit::placeholder, QTextEdit::placeholder {{
                color: {theme.text_muted};
            }}
        """

    @staticmethod
    def label_primary() -> str:
        """Primary label style."""
        return f"""
            color: {theme.text_primary};
            font-size: {theme.font_s}px;
            font-weight: 500;
        """

    @staticmethod
    def label_secondary() -> str:
        """Secondary label style."""
        return f"""
            color: {theme.text_secondary};
            font-size: {theme.font_xs}px;
            font-weight: 400;
        """

    @staticmethod
    def label_status() -> str:
        """Status label style."""
        return f"""
            color: {theme.text_secondary};
            font-size: {theme.font_xs}px;
            font-weight: 400;
        """

    @staticmethod
    def label_success() -> str:
        """Success status label style."""
        return f"""
            color: {theme.success};
            font-weight: 500;
            font-size: {theme.font_xs}px;
        """

    @staticmethod
    def label_error() -> str:
        """Error status label style."""
        return f"""
            color: {theme.error};
            font-weight: 500;
            font-size: {theme.font_xs}px;
        """

    @staticmethod
    def label_warning() -> str:
        """Warning status label style."""
        return f"""
            color: {theme.warning};
            font-weight: 500;
            font-size: {theme.font_xs}px;
        """

    @staticmethod
    def progress_bar() -> str:
        """Progress bar style - minimal and elegant."""
        return f"""
            QProgressBar {{
                border: 1px solid {theme.border};
                border-radius: {theme.radius_s}px;
                text-align: center;
                background: {theme.background_tertiary};
                height: {theme.spacing_s}px;
                color: {theme.text_primary};
                font-weight: 400;
                font-size: {theme.font_xs}px;
            }}
            QProgressBar::chunk {{
                background: {theme.primary};
                border-radius: {theme.radius_s - 1}px;
            }}
        """

    @staticmethod
    def media_badge() -> str:
        """Media badge style - minimal and elegant."""
        return f"""
            QLabel {{
                padding: {theme.spacing_l}px;
                border-radius: {theme.radius_s}px;
                background: {theme.background_elevated};
                border: 1px solid {theme.border};
                font-weight: 500;
                color: {theme.text_secondary};
                font-size: {theme.font_m}px;
                cursor: pointer;
            }}
            QLabel:hover {{
                background: {theme.background_secondary};
                border-color: {theme.primary};
            }}
        """

    @staticmethod
    def checkbox() -> str:
        """Checkbox style - simple and clean."""
        return f"""
            QCheckBox {{
                spacing: {theme.spacing_s}px;
                font-size: {theme.font_s}px;
                color: {theme.text_primary};
                font-weight: 400;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {theme.border};
                border-radius: 2px;
                background: {theme.background_elevated};
            }}
            QCheckBox::indicator:hover {{
                border-color: {theme.primary};
            }}
            QCheckBox::indicator:checked {{
                background: {theme.primary};
                border-color: {theme.primary};
            }}
        """

    @staticmethod
    def combobox() -> str:
        """ComboBox style - consistent with other controls."""
        return f"""
            QComboBox {{
                padding: 6px 12px;
                background: {theme.background_elevated};
                border: 1px solid {theme.border};
                border-radius: 8px;
                color: {theme.text_primary};
                font-size: {theme.font_s}px;
                font-weight: 400;
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {theme.primary};
                background: {theme.background_secondary};
            }}
            QComboBox:focus {{
                border-color: {theme.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {theme.text_secondary};
                margin-right: 8px;
            }}
            QComboBox::down-arrow:hover {{
                border-top-color: {theme.text_primary};
            }}
            QComboBox QAbstractItemView {{
                background: {theme.background_elevated};
                border: 1px solid {theme.border};
                border-radius: 8px;
                color: {theme.text_primary};
                selection-background-color: {theme.primary};
                selection-color: {theme.text_primary};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
                border: none;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {theme.background_secondary};
            }}
        """

    @staticmethod
    def scroll_area() -> str:
        """Scroll area style with dark theme."""
        return f"""
            QScrollArea {{
                border: none;
                background: {theme.background_secondary};
            }}
            QScrollBar:vertical {{
                background: {theme.background_tertiary};
                width: {theme.spacing_l}px;
                border-radius: {theme.radius_m}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme.background_elevated};
                border-radius: {theme.radius_m}px;
                min-height: {theme.spacing_xl}px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme.primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

    @staticmethod
    def group_box() -> str:
        """Group box style with modern design."""
        return f"""
            QGroupBox {{
                font-weight: 600;
                font-size: {theme.font_m}px;
                border: 2px solid {theme.border};
                border-radius: {theme.radius_m}px;
                margin-top: {theme.spacing_l}px;
                padding-top: {theme.spacing_s}px;
                color: {theme.text_primary};
                background: {theme.background_secondary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {theme.spacing_s}px;
                padding: 0 {theme.spacing_s}px 0 {theme.spacing_s}px;
                color: {theme.text_primary};
            }}
        """

    @staticmethod
    def main_window() -> str:
        """Apply main window style with ultra dark theme."""
        return f"""
            QMainWindow {{
                background: {theme.background_primary};
                color: {theme.text_primary};
            }}
            QWidget {{
                background: {theme.background_primary};
                color: {theme.text_primary};
                font-size: {theme.font_s}px;
            }}
        """


class LayoutHelper:
    """Helper class for consistent layout spacing."""

    @staticmethod
    def set_standard_margins(layout) -> None:
        """Set standard margins for layouts."""
        layout.setContentsMargins(
            theme.spacing_s, theme.spacing_s, theme.spacing_s, theme.spacing_s
        )

    @staticmethod
    def set_compact_margins(layout) -> None:
        """Set compact margins for layouts."""
        layout.setContentsMargins(
            theme.spacing_xs, theme.spacing_xs, theme.spacing_xs, theme.spacing_xs
        )

    @staticmethod
    def set_standard_spacing(layout) -> None:
        """Set standard spacing for layouts."""
        layout.setSpacing(theme.spacing_m)

    @staticmethod
    def set_compact_spacing(layout) -> None:
        """Set compact spacing for layouts."""
        layout.setSpacing(theme.spacing_s)

    @staticmethod
    def set_tight_spacing(layout) -> None:
        """Set tight spacing for layouts."""
        layout.setSpacing(theme.spacing_xs)

    @staticmethod
    def set_loose_spacing(layout) -> None:
        """Set loose spacing for layouts."""
        layout.setSpacing(theme.spacing_l)
