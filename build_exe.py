#!/usr/bin/env python3
"""
Build script for creating a standalone EXE file of the Media Uploader application.
Uses PyInstaller to package the application with all dependencies.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def create_icon():
    """Create a simple icon file if it doesn't exist."""
    icon_path = Path("assets/icon.ico")

    if icon_path.exists():
        print(f"✓ Icon already exists: {icon_path}")
        return str(icon_path)

    # Create assets directory if it doesn't exist
    icon_path.parent.mkdir(exist_ok=True)

    # Create a simple placeholder icon using PIL if available
    try:
        from PIL import Image, ImageDraw

        # Create a 256x256 icon with a simple design
        size = 256
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw a simple upload icon (arrow pointing up)
        margin = 40
        arrow_width = size - 2 * margin
        arrow_height = arrow_width * 0.6

        # Arrow body
        points = [
            (size // 2, margin),  # Top point
            (size // 2 - arrow_width // 4, margin + arrow_height // 2),  # Left
            (size // 2 - arrow_width // 8, margin + arrow_height // 2),  # Left inner
            (size // 2 - arrow_width // 8, size - margin),  # Bottom left
            (size // 2 + arrow_width // 8, size - margin),  # Bottom right
            (size // 2 + arrow_width // 8, margin + arrow_height // 2),  # Right inner
            (size // 2 + arrow_width // 4, margin + arrow_height // 2),  # Right
        ]

        # Draw with a nice blue color
        draw.polygon(points, fill=(52, 152, 219, 255))

        # Save as ICO
        img.save(
            str(icon_path),
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
        )
        print(f"✓ Created icon: {icon_path}")
        return str(icon_path)

    except ImportError:
        print("⚠ PIL not available, creating a placeholder icon file")
        # Create a minimal ICO file header
        with open(icon_path, "wb") as f:
            # Minimal ICO file structure
            f.write(b"\x00\x00")  # Reserved
            f.write(b"\x01\x00")  # Type (1 = ICO)
            f.write(b"\x01\x00")  # Number of images
            f.write(b"\x10\x10")  # Width/Height (16x16)
            f.write(b"\x00")  # Color count
            f.write(b"\x00")  # Reserved
            f.write(b"\x01\x00")  # Color planes
            f.write(b"\x20\x00")  # Bits per pixel
            f.write(b"\x00\x00\x00\x00")  # Size of image data
            f.write(b"\x16\x00\x00\x00")  # Offset to image data
            # Minimal PNG data (1x1 transparent pixel)
            f.write(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82"
            )

        print(f"✓ Created placeholder icon: {icon_path}")
        return str(icon_path)


def build_exe():
    """Build the EXE file using PyInstaller."""
    print("🚀 Starting Media Uploader EXE build process...")

    # Check if PyInstaller is installed
    try:
        import PyInstaller

        print(f"✓ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            "Installing PyInstaller",
        ):
            return False

    # Create icon
    icon_path = create_icon()

    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("media_uploader.spec")

    if dist_dir.exists():
        print(f"🧹 Cleaning previous build: {dist_dir}")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print(f"🧹 Cleaning previous build: {build_dir}")
        shutil.rmtree(build_dir)

    if spec_file.exists():
        print(f"🧹 Removing previous spec file: {spec_file}")
        spec_file.unlink()

    # Build the EXE
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable
        "--windowed",  # No console window
        f"--icon={icon_path}",
        "--name=MediaUploader",
        "--add-data=assets;assets",  # Include assets directory
        "--exclude=PyQt6",  # Exclude PyQt6 to avoid conflicts
        "--exclude=PyQt5",  # Exclude PyQt5 as well
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtMultimedia",
        "--hidden-import=PySide6.QtMultimediaWidgets",
        "--hidden-import=google.auth",
        "--hidden-import=google.auth.oauthlib",
        "--hidden-import=googleapiclient",
        "--hidden-import=googleapiclient.discovery",
        "--hidden-import=googleapiclient.http",
        "--hidden-import=googleapiclient.errors",
        "--collect-all=PySide6",
        "--collect-all=google",
        "app/main.py",
    ]

    if not run_command(cmd, "Building EXE with PyInstaller"):
        return False

    # Check if the EXE was created
    exe_path = dist_dir / "MediaUploader.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 Build successful!")
        print(f"📁 EXE location: {exe_path.absolute()}")
        print(f"📊 File size: {size_mb:.1f} MB")

        # Create a simple batch file for easy launching
        batch_path = Path("run_media_uploader.bat")
        with open(batch_path, "w") as f:
            f.write(f'@echo off\n"{exe_path.absolute()}"\n')
        print(f"📝 Created launcher: {batch_path}")

        return True
    else:
        print("✗ EXE file not found after build")
        return False


def main():
    """Main build function."""
    if build_exe():
        print("\n✅ Build completed successfully!")
        print("\nTo run the application:")
        print("1. Double-click MediaUploader.exe in the dist/ folder")
        print("2. Or use the run_media_uploader.bat file")
        print("\nNote: The first run may take longer as it extracts resources.")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
