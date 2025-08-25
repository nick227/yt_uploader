# Styling Guide

This document describes the centralized styling system used in the Media Uploader application.

## Overview

The styling system is built around three core principles:

1. **Consistency**: All spacing, colors, and typography follow a systematic scale
2. **Maintainability**: Centralized configuration makes updates easy
3. **Reusability**: Pre-built components reduce code duplication

## Architecture

### Core Components

- **`core/styles.py`**: Main styling module containing all styles and helpers
- **`core/config.py`**: Configuration constants (window sizes, limits, etc.)
- **`StyleBuilder`**: Static class for generating CSS-style strings
- **`LayoutHelper`**: Static class for consistent layout spacing
- **`StyleTheme`**: Dataclass containing all theme values

### Spacing Scale

The application uses an 8px base unit system:

```python
class Spacing:
    XS = 4    # 4px
    S = 8     # 8px
    M = 12    # 12px
    L = 16    # 16px
    XL = 24   # 24px
    XXL = 32  # 32px
    XXXL = 48 # 48px
```

### Color Palette

```python
COLORS = {
    "primary": "#0078d4",      # Blue - main actions
    "primary_hover": "#106ebe", # Darker blue - hover states
    "primary_pressed": "#005a9e", # Even darker - pressed states
    "success": "#28a745",      # Green - success states
    "error": "#dc3545",        # Red - error states
    "warning": "#ffc107",      # Yellow - warning states
    "text_secondary": "#666666", # Gray - secondary text
    "border": "#dddddd",       # Light gray - borders
    "background_light": "#f0f0f0", # Very light gray - backgrounds
}
```

## Usage Examples

### Basic Button Styling

```python
from core.styles import StyleBuilder

# Primary button (blue)
button = QPushButton("Click Me")
button.setStyleSheet(StyleBuilder.button_primary())

# Danger button (red)
upload_btn = QPushButton("Upload")
upload_btn.setStyleSheet(StyleBuilder.button_danger())

# Secondary button (outlined)
cancel_btn = QPushButton("Cancel")
cancel_btn.setStyleSheet(StyleBuilder.button_secondary())
```

### Input Field Styling

```python
# Basic input field
title_input = QLineEdit()
title_input.setStyleSheet(StyleBuilder.input_field())

# Input field with error state
description_input = QTextEdit()
description_input.setStyleSheet(StyleBuilder.input_field(has_error=True))
```

### Label Styling

```python
# Different label types
primary_label = QLabel("Main Title")
primary_label.setStyleSheet(StyleBuilder.label_primary())

secondary_label = QLabel("Subtitle")
secondary_label.setStyleSheet(StyleBuilder.label_secondary())

status_label = QLabel("Status")
status_label.setStyleSheet(StyleBuilder.label_status())

# Status-specific labels
success_label = QLabel("Success!")
success_label.setStyleSheet(StyleBuilder.label_success())

error_label = QLabel("Error!")
error_label.setStyleSheet(StyleBuilder.label_error())

warning_label = QLabel("Warning!")
warning_label.setStyleSheet(StyleBuilder.label_warning())
```

### Layout Spacing

```python
from core.styles import LayoutHelper

# Standard layout
layout = QVBoxLayout()
LayoutHelper.set_standard_margins(layout)  # 8px margins
LayoutHelper.set_standard_spacing(layout)  # 12px spacing

# Compact layout
compact_layout = QHBoxLayout()
LayoutHelper.set_compact_margins(layout)   # 4px margins
LayoutHelper.set_compact_spacing(layout)   # 8px spacing

# Tight layout
tight_layout = QVBoxLayout()
LayoutHelper.set_tight_spacing(layout)     # 4px spacing

# Loose layout
loose_layout = QHBoxLayout()
LayoutHelper.set_loose_spacing(layout)     # 16px spacing
```

### Progress Bar

```python
progress = QProgressBar()
progress.setStyleSheet(StyleBuilder.progress_bar())
```

### Checkbox

```python
checkbox = QCheckBox("Select me")
checkbox.setStyleSheet(StyleBuilder.checkbox())
```

### Scroll Area

```python
scroll_area = QScrollArea()
scroll_area.setStyleSheet(StyleBuilder.scroll_area())
```

### Media Badge

```python
badge = QLabel("🎵 Audio")
badge.setStyleSheet(StyleBuilder.media_badge())
```

## Creating Custom Styles

### Adding New Style Methods

To add a new style, extend the `StyleBuilder` class:

```python
@staticmethod
def custom_widget() -> str:
    """Custom widget style."""
    return f"""
        QWidget {{
            background-color: {theme.background_light};
            border: 1px solid {theme.border};
            border-radius: {theme.radius_s}px;
            padding: {theme.spacing_s}px;
        }}
    """
```

### Using Theme Values

Access theme values directly:

```python
from core.styles import theme

# Use theme values in custom styles
custom_style = f"""
    QLabel {{
        color: {theme.text_primary};
        font-size: {theme.font_l}px;
        padding: {theme.spacing_m}px;
    }}
"""
```

## Best Practices

### 1. Always Use StyleBuilder

❌ **Don't** write inline styles:
```python
button.setStyleSheet("padding: 8px; background: blue;")
```

✅ **Do** use StyleBuilder:
```python
button.setStyleSheet(StyleBuilder.button_primary())
```

### 2. Use LayoutHelper for Spacing

❌ **Don't** hardcode spacing:
```python
layout.setSpacing(12)
layout.setContentsMargins(8, 8, 8, 8)
```

✅ **Do** use LayoutHelper:
```python
LayoutHelper.set_standard_spacing(layout)
LayoutHelper.set_standard_margins(layout)
```

### 3. Leverage Error States

Use the `has_error` parameter for validation feedback:

```python
# Update style based on validation
is_valid = validate_input(text)
input_field.setStyleSheet(StyleBuilder.input_field(has_error=not is_valid))
```

### 4. Consistent Component Usage

Use the same style patterns across similar components:

```python
# All primary actions use button_primary()
save_btn.setStyleSheet(StyleBuilder.button_primary())
cancel_btn.setStyleSheet(StyleBuilder.button_secondary())
delete_btn.setStyleSheet(StyleBuilder.button_danger())
```

## Migration Guide

### From Manual Styling

**Before:**
```python
button.setStyleSheet("""
    QPushButton {
        padding: 8px 16px;
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 4px;
    }
""")
```

**After:**
```python
button.setStyleSheet(StyleBuilder.button_primary())
```

### From Hardcoded Spacing

**Before:**
```python
layout.setSpacing(12)
layout.setContentsMargins(8, 8, 8, 8)
```

**After:**
```python
LayoutHelper.set_standard_spacing(layout)
LayoutHelper.set_standard_margins(layout)
```

## Theme Customization

To create a different theme, modify the `StyleTheme` class:

```python
# Dark theme example
dark_theme = StyleTheme(
    primary="#1a73e8",
    text_primary="#ffffff",
    text_secondary="#b0b0b0",
    background_white="#2d2d2d",
    background_light="#3d3d3d",
    border="#555555"
)
```

## Troubleshooting

### Common Issues

1. **Styles not applying**: Ensure you're calling `setStyleSheet()` after widget creation
2. **Inconsistent spacing**: Use `LayoutHelper` methods instead of manual spacing
3. **Color mismatches**: Always use theme colors, never hardcode hex values

### Debugging

To debug styling issues:

```python
# Print the generated CSS
print(StyleBuilder.button_primary())

# Check theme values
print(f"Primary color: {theme.primary}")
print(f"Standard spacing: {theme.spacing_m}")
```

## Future Enhancements

Potential improvements to the styling system:

1. **Dark mode support**: Add theme switching capability
2. **Responsive design**: Scale spacing based on screen size
3. **Animation support**: Add transition effects
4. **Accessibility**: High contrast mode support
5. **Custom themes**: User-configurable themes
