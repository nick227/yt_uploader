"""
Simple animation helpers for subtle motion effects.
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtWidgets import QWidget


def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """Create a fade-in animation for a widget."""
    animation = QPropertyAnimation(widget, b"windowOpacity")
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    return animation


def slide_in(
    widget: QWidget, direction: str = "left", duration: int = 300
) -> QPropertyAnimation:
    """Create a slide-in animation for a widget."""
    animation = QPropertyAnimation(widget, b"geometry")
    animation.setDuration(duration)
    animation.setEasingCurve(QEasingCurve.OutCubic)

    current_geometry = widget.geometry()

    if direction == "left":
        start_geometry = current_geometry.translated(-current_geometry.width(), 0)
    elif direction == "right":
        start_geometry = current_geometry.translated(current_geometry.width(), 0)
    elif direction == "up":
        start_geometry = current_geometry.translated(0, -current_geometry.height())
    elif direction == "down":
        start_geometry = current_geometry.translated(0, current_geometry.height())
    else:
        start_geometry = current_geometry

    animation.setStartValue(start_geometry)
    animation.setEndValue(current_geometry)
    return animation


def pulse_glow(widget: QWidget, color: str, duration: int = 1000) -> QPropertyAnimation:
    """Create a pulsing glow effect animation."""
    # This would require custom styling with CSS animations
    # For now, we'll create a simple opacity pulse
    animation = QPropertyAnimation(widget, b"windowOpacity")
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.7)
    animation.setEasingCurve(QEasingCurve.InOutQuad)
    animation.setLoopCount(-1)  # Infinite loop
    return animation


def shake(
    widget: QWidget, intensity: int = 5, duration: int = 500
) -> QPropertyAnimation:
    """Create a shake animation for error feedback."""
    animation = QPropertyAnimation(widget, b"geometry")
    animation.setDuration(duration)
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    current_geometry = widget.geometry()
    animations = []

    # Create multiple keyframes for shake effect
    for i in range(0, duration, 50):
        progress = i / duration
        offset = intensity * (1 - progress) * (1 if i % 100 < 50 else -1)
        new_geometry = current_geometry.translated(offset, 0)
        animations.append((progress, new_geometry))

    # Add final position
    animations.append((1.0, current_geometry))

    # Set keyframes
    for progress, geometry in animations:
        animation.setKeyValueAt(progress, geometry)

    return animation


def delayed_animation(widget: QWidget, animation_func, delay: int = 100, **kwargs):
    """Execute an animation after a delay."""
    timer = QTimer()
    timer.setSingleShot(True)

    def execute_animation():
        anim = animation_func(widget, **kwargs)
        anim.start()

    timer.timeout.connect(execute_animation)
    timer.start(delay)
    return timer
