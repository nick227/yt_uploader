#!/usr/bin/env python3
"""
Simple build script for creating a standalone EXE file.
This version handles locked build directories gracefully.
"""

import os
import shutil
import subprocess
import sys
import time
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


def safe_remove_directory(path, max_retries=5):
    """Safely remove a directory with retries."""
    if not path.exists():
        return True

    for attempt in range(max_retries):
        try:
            shutil.rmtree(path)
            print(f"✓ Removed {path}")
            return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(
                    f"⚠️  Directory {path} is locked, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(2)
            else:
                print(f"❌ Could not remove {path} after {max_retries} attempts")
                print(f"   Error: {e}")
                return False
    return False


def safe_remove_file(path, max_retries=5):
    """Safely remove a file with retries."""
    if not path.exists():
        return True

    for attempt in range(max_retries):
        try:
            path.unlink()
            print(f"✓ Removed {path}")
            return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(
                    f"⚠️  File {path} is locked, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(2)
            else:
                print(f"❌ Could not remove {path} after {max_retries} attempts")
                print(f"   Error: {e}")
                return False
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
    """Build the EXE file using PyInstaller with minimal options."""
    print("🚀 Starting simple Media Uploader EXE build...")
    print("📊 Expected size: ~70-80 MB (optimized)")

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

    # Clean previous builds with retry logic
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("MediaUploader.spec")

    print("\n🧹 Cleaning previous builds...")

    if not safe_remove_directory(dist_dir):
        print("⚠️  Continuing with existing dist/ directory")

    if not safe_remove_directory(build_dir):
        print("⚠️  Continuing with existing build/ directory")

    if not safe_remove_file(spec_file):
        print("⚠️  Continuing with existing spec file")

    # Build the EXE with minimal options for speed
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        "--name=MediaUploader",
        "--exclude=PyQt6",
        "--exclude=PyQt5",
        "--exclude=matplotlib",
        "--exclude=pytest",
        "--exclude=IPython",
        "--exclude=jupyter",
        "--exclude=notebook",
        "--exclude=sphinx",
        "--exclude=docutils",
        "--exclude=black",
        "--exclude=flake8",
        "--exclude=mypy",
        "--exclude=isort",
        "--exclude=pre-commit",
        "--exclude=tox",
        "app/main.py",
    ]

    if not run_command(cmd, "Building EXE with PyInstaller (simple mode)"):
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
