#!/usr/bin/env python3
"""
Build script for Media Uploader application.
Creates a standalone executable using PyInstaller.
"""

import subprocess
import sys
from pathlib import Path


def build_exe():
    """Build the Media Uploader executable."""
    print("🔨 Building Media Uploader executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=MediaUploader",
        "--icon=assets/icon.ico" if Path("assets/icon.ico").exists() else "",
        "app/main.py"
    ]
    
    # Remove empty icon argument if no icon exists
    cmd = [arg for arg in cmd if arg]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build successful!")
        print(f"📁 Executable created: dist/MediaUploader.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Main build function."""
    if build_exe():
        print("\n🎉 Build completed successfully!")
        print("📁 Location: dist/MediaUploader.exe")
        return 0
    else:
        print("\n💥 Build failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
