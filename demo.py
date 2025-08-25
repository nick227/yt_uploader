#!/usr/bin/env python3
"""
Demo script to showcase the Media Uploader's new dark theme and animations.
Run this to see the beautiful Discord + Monokai inspired interface!
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.main import main


def create_demo_files():
    """Create some demo media files for testing."""
    demo_dir = Path("demo_media")
    demo_dir.mkdir(exist_ok=True)

    # Create demo MP3 file
    mp3_file = demo_dir / "demo_audio.mp3"
    if not mp3_file.exists():
        # Create a simple text file as a placeholder
        mp3_file.write_text("Demo MP3 file content")

    # Create demo MP4 file
    mp4_file = demo_dir / "demo_video.mp4"
    if not mp4_file.exists():
        # Create a simple text file as a placeholder
        mp4_file.write_text("Demo MP4 file content")

    print(f"🎵 Created demo files in: {demo_dir.absolute()}")
    return demo_dir


def main():
    """Main demo function."""
    print("🎨 Media Uploader - Dark Theme Demo")
    print("=" * 50)
    print("✨ Features showcased:")
    print("  • Discord-inspired dark theme")
    print("  • Monokai accent colors")
    print("  • Smooth animations and transitions")
    print("  • Glass morphism effects")
    print("  • Gradient buttons and progress bars")
    print("  • Subtle glow effects")
    print("  • Shake animations for validation")
    print("  • Fade-in animations for media rows")
    print()

    # Create demo files
    demo_dir = create_demo_files()
    print(f"📁 Demo files ready in: {demo_dir}")
    print()
    print("🚀 Starting application...")
    print("💡 Try scanning the 'demo_media' folder to see the interface!")
    print()

    # Start the application
    app = QApplication(sys.argv)

    # Set application properties for better appearance
    app.setApplicationName("Media Uploader")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Media Uploader Team")

    # Import and run the main application
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    print("🎉 Application started! Enjoy the beautiful dark theme!")
    print("💫 Look for the subtle animations and modern styling!")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
