#!/usr/bin/env python3
"""
Debug build script for creating a console EXE to see error messages.
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


def build_debug_exe():
    """Build the EXE file with console output for debugging."""
    print("🚀 Starting Media Uploader Debug EXE build process...")

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

    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("media_uploader_debug.spec")

    if dist_dir.exists():
        print(f"🧹 Cleaning previous build: {dist_dir}")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print(f"🧹 Cleaning previous build: {build_dir}")
        shutil.rmtree(build_dir)

    if spec_file.exists():
        print(f"🧹 Removing previous spec file: {spec_file}")
        spec_file.unlink()

    # Build the EXE with console output
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable
        "--console",  # Show console window for debugging
        "--name=MediaUploaderDebug",
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

    if not run_command(cmd, "Building Debug EXE with PyInstaller"):
        return False

    # Check if the EXE was created
    exe_path = dist_dir / "MediaUploaderDebug.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 Debug build successful!")
        print(f"📁 EXE location: {exe_path.absolute()}")
        print(f"📊 File size: {size_mb:.1f} MB")
        return True
    else:
        print("✗ EXE file not found after build")
        return False


def main():
    """Main build function."""
    if build_debug_exe():
        print("\n✅ Debug build completed successfully!")
        print("\nTo test the application:")
        print("1. Run: .\\dist\\MediaUploaderDebug.exe")
        print("2. Look for any error messages in the console")
    else:
        print("\n❌ Debug build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
