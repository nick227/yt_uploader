#!/usr/bin/env python3
"""
Improved build script with progress indicators and verbose output.
"""

import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def show_progress_dots():
    """Show animated progress dots during long operations."""
    import sys
    import time

    dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while True:
        sys.stdout.write(f"\r⏳ Building... {dots[i]} ")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(dots)


def run_command_with_progress(cmd, description):
    """Run a command with progress indicators."""
    print(f"\n{description}...")
    print(f"Running: {' '.join(cmd)}")
    print("This may take 5-15 minutes on first build...")

    # Start progress animation in background
    progress_thread = threading.Thread(target=show_progress_dots, daemon=True)
    progress_thread.start()

    try:
        # Run with verbose output
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # Show output in real-time
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Stop progress animation
        sys.stdout.write("\r" + " " * 50 + "\r")  # Clear progress line
        print("✓ Success")
        return True

    except subprocess.CalledProcessError as e:
        # Stop progress animation
        sys.stdout.write("\r" + " " * 50 + "\r")  # Clear progress line
        print(f"✗ Failed: {e}")
        return False


def create_icon():
    """Create a simple icon file if it doesn't exist."""
    icon_path = Path("assets/icon.ico")

    if icon_path.exists():
        print(f"✓ Icon already exists: {icon_path}")
        return str(icon_path)

    # Create assets directory if it doesn't exist
    icon_path.parent.mkdir(exist_ok=True)

    # Create a minimal ICO file
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
    """Build the EXE file using PyInstaller with progress indicators."""
    print("🚀 Starting Media Uploader EXE build process...")
    print("⏱️  Estimated time: 5-15 minutes (first build)")
    print("📊 Expected file size: ~70-80MB")

    # Check if PyInstaller is installed
    try:
        import PyInstaller

        print(f"✓ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        if not run_command_with_progress(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            "Installing PyInstaller",
        ):
            return False

    # Create icon
    icon_path = create_icon()

    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("MediaUploader.spec")

    if dist_dir.exists():
        print(f"🧹 Cleaning previous build: {dist_dir}")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print(f"🧹 Cleaning previous build: {build_dir}")
        shutil.rmtree(build_dir)

    if spec_file.exists():
        print(f"🧹 Removing previous spec file: {spec_file}")
        spec_file.unlink()

    print("\n🔧 Build phases:")
    print("   1. Analysis (2-5 min) - PyInstaller analyzes dependencies")
    print("   2. Collection (3-8 min) - Copies Qt libraries and modules")
    print("   3. Linking (1-3 min) - Creates final EXE file")

    # Build the EXE with verbose output
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

    if not run_command_with_progress(cmd, "Building EXE with PyInstaller"):
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
    start_time = time.time()

    if build_exe():
        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print(f"\n✅ Build completed successfully!")
        print(f"⏱️  Total build time: {minutes}m {seconds}s")
        print("\nTo run the application:")
        print("1. Double-click MediaUploader.exe in the dist/ folder")
        print("2. Or use the run_media_uploader.bat file")
        print("\nNote: The first run may take longer as it extracts resources.")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
