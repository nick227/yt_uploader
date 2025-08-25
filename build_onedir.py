#!/usr/bin/env python3
"""
Build script using --onedir mode to show folder structure.
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
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        return False


def build_onedir():
    """Build using --onedir mode to show folder structure."""
    print("🚀 Building Media Uploader with --onedir mode...")

    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("MediaUploader_onedir.spec")

    if dist_dir.exists():
        print(f"🧹 Cleaning previous build: {dist_dir}")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print(f"🧹 Cleaning previous build: {build_dir}")
        shutil.rmtree(build_dir)

    if spec_file.exists():
        print(f"🧹 Removing previous spec file: {spec_file}")
        spec_file.unlink()

    # Build with --onedir
    cmd = [
        "pyinstaller",
        "--onedir",  # Folder mode instead of --onefile
        "--windowed",
        "--icon=assets/icon.ico",
        "--name=MediaUploader_onedir",
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

    if not run_command(cmd, "Building with --onedir mode"):
        return False

    # Check results
    exe_path = dist_dir / "MediaUploader_onedir" / "MediaUploader_onedir.exe"
    if exe_path.exists():
        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        folder_size_mb = sum(
            f.stat().st_size for f in dist_dir.rglob("*") if f.is_file()
        ) / (1024 * 1024)

        print(f"\n🎉 --onedir build successful!")
        print(f"📁 EXE location: {exe_path}")
        print(f"📊 EXE size: {exe_size_mb:.1f} MB")
        print(f"📊 Total folder size: {folder_size_mb:.1f} MB")

        # Show folder structure
        print(f"\n📂 Folder structure:")
        show_folder_structure(dist_dir / "MediaUploader_onedir", max_depth=3)

        return True
    else:
        print("✗ EXE file not found after build")
        return False


def show_folder_structure(path, prefix="", max_depth=3, current_depth=0):
    """Show the folder structure."""
    if current_depth >= max_depth:
        return

    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = "    " if is_last else "│   "

        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            print(f"{prefix}{current_prefix}{item.name} ({size_mb:.1f} MB)")
        else:
            print(f"{prefix}{current_prefix}{item.name}/")
            if current_depth < max_depth - 1:
                show_folder_structure(
                    item, prefix + next_prefix, max_depth, current_depth + 1
                )


def compare_modes():
    """Compare --onefile vs --onedir modes."""
    print("\n" + "=" * 60)
    print("COMPARISON: --onefile vs --onedir")
    print("=" * 60)

    comparison = {
        "Distribution": {
            "onefile": "Single EXE file (72MB)",
            "onedir": "Folder with multiple files (~50MB total)",
        },
        "User Experience": {
            "onefile": "Double-click EXE, slower startup (extracts first)",
            "onedir": "Double-click EXE in folder, faster startup",
        },
        "File Management": {
            "onefile": "One file to manage",
            "onedir": "Many files, but organized structure",
        },
        "Size": {
            "onefile": "72MB (compressed, includes extraction overhead)",
            "onedir": "~50MB (uncompressed, no extraction needed)",
        },
        "Debugging": {
            "onefile": "Harder to debug (everything packed)",
            "onedir": "Easier to debug (files accessible)",
        },
    }

    for aspect, modes in comparison.items():
        print(f"\n📋 {aspect}:")
        print(f"   --onefile: {modes['onefile']}")
        print(f"   --onedir:  {modes['onedir']}")


def main():
    """Main function."""
    if build_onedir():
        compare_modes()

        print(f"\n💡 Summary:")
        print(f"• --onefile: Single file, larger size, slower startup")
        print(f"• --onedir:  Multiple files, smaller size, faster startup")
        print(f"• Both work the same way for end users")
        print(f"• Choose based on your distribution preferences")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
