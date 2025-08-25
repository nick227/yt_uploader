#!/usr/bin/env python3
"""
Real-time build monitoring with detailed progress tracking.
"""

import os
import time
from datetime import datetime
from pathlib import Path

import psutil


def get_process_info():
    """Get information about PyInstaller process."""
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            if "pyinstaller" in proc.info["name"].lower():
                return {
                    "pid": proc.info["pid"],
                    "cpu": proc.info["cpu_percent"],
                    "memory_mb": proc.info["memory_info"].rss / (1024 * 1024),
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def count_files_in_directory(path):
    """Count files in directory recursively."""
    if not path.exists():
        return 0
    return len(list(path.rglob("*")))


def get_directory_sizes():
    """Get sizes of key build directories."""
    sizes = {}

    # Check build directory
    build_dir = Path("build")
    if build_dir.exists():
        build_size = sum(f.stat().st_size for f in build_dir.rglob("*") if f.is_file())
        sizes["build"] = build_size / (1024 * 1024)  # MB

    # Check dist directory
    dist_dir = Path("dist")
    if dist_dir.exists():
        dist_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
        sizes["dist"] = dist_size / (1024 * 1024)  # MB

    return sizes


def get_detailed_progress():
    """Get detailed build progress information."""
    build_dir = Path("build")
    dist_dir = Path("dist")

    progress = {
        "phase": "unknown",
        "files_collected": 0,
        "key_directories": {},
        "total_size_mb": 0,
        "exe_created": False,
        "exe_size_mb": 0,
    }

    # Check if analysis is complete
    analysis_dir = build_dir / "MediaUploader"
    if analysis_dir.exists():
        progress["phase"] = "collection"
        progress["files_collected"] = count_files_in_directory(analysis_dir)

        # Check key directories
        key_dirs = {
            "PySide6": "Qt Framework",
            "google": "Google APIs",
            "_internal": "Python Runtime",
            "app": "Application Code",
            "core": "Core Modules",
            "services": "Services",
            "infra": "Infrastructure",
        }

        for dir_name, description in key_dirs.items():
            dir_path = analysis_dir / dir_name
            if dir_path.exists():
                file_count = count_files_in_directory(dir_path)
                progress["key_directories"][description] = file_count

    # Check for final EXE
    exe_path = dist_dir / "MediaUploader.exe"
    if exe_path.exists():
        progress["phase"] = "complete"
        progress["exe_created"] = True
        progress["exe_size_mb"] = exe_path.stat().st_size / (1024 * 1024)

    # Calculate total size
    sizes = get_directory_sizes()
    progress["total_size_mb"] = sum(sizes.values())

    return progress


def show_detailed_status():
    """Show detailed build status with real-time updates."""
    print("🔍 Detailed Build Monitor")
    print("=" * 50)

    while True:
        # Clear screen (works on most terminals)
        os.system("cls" if os.name == "nt" else "clear")

        # Get current time
        current_time = datetime.now().strftime("%H:%M:%S")

        # Get process info
        proc_info = get_process_info()

        # Get detailed progress
        progress = get_detailed_progress()

        # Display header
        print(f"🕐 {current_time} - Media Uploader Build Monitor")
        print("=" * 50)

        # Show process status
        if proc_info:
            print(f"⚙️  PyInstaller Process:")
            print(f"   PID: {proc_info['pid']}")
            print(f"   CPU: {proc_info['cpu']:.1f}%")
            print(f"   Memory: {proc_info['memory_mb']:.1f} MB")
        else:
            print("⚙️  PyInstaller Process: Not found (may have completed)")

        print()

        # Show build phase
        phase_icons = {
            "unknown": "❓",
            "analysis": "🔍",
            "collection": "📦",
            "linking": "🔗",
            "complete": "✅",
        }

        phase_name = progress["phase"].title()
        phase_icon = phase_icons.get(progress["phase"], "❓")
        print(f"{phase_icon} Build Phase: {phase_name}")

        # Show file collection progress
        if progress["files_collected"] > 0:
            print(f"📊 Files Collected: {progress['files_collected']:,}")

        # Show key directories
        if progress["key_directories"]:
            print(f"\n📁 Key Components:")
            for desc, count in progress["key_directories"].items():
                print(f"   {desc}: {count:,} files")

        # Show size information
        if progress["total_size_mb"] > 0:
            print(f"\n💾 Build Size: {progress['total_size_mb']:.1f} MB")

        # Show final EXE status
        if progress["exe_created"]:
            print(f"\n🎉 Build Complete!")
            print(f"📁 EXE Size: {progress['exe_size_mb']:.1f} MB")
            print(f"📁 Location: dist/MediaUploader.exe")
            break

        # Show directory status
        print(f"\n📂 Directory Status:")
        print(f"   build/: {'✅ Exists' if Path('build').exists() else '❌ Not found'}")
        print(f"   dist/: {'✅ Exists' if Path('dist').exists() else '❌ Not found'}")
        print(
            f"   MediaUploader.spec: {'✅ Exists' if Path('MediaUploader.spec').exists() else '❌ Not found'}"
        )

        # Show tips
        print(f"\n💡 Tips:")
        if progress["phase"] == "collection":
            print(f"   • Collection phase can take 5-10 minutes")
            print(f"   • PyInstaller is copying Qt libraries and modules")
            print(f"   • File count should increase over time")
        elif progress["phase"] == "unknown":
            print(f"   • Build may be in analysis phase")
            print(f"   • Check if PyInstaller process is running")

        print(f"\n⏳ Monitoring... Press Ctrl+C to stop")

        # Wait before next update
        time.sleep(2)


def show_build_summary():
    """Show a summary of the completed build."""
    print("\n" + "=" * 50)
    print("📋 BUILD SUMMARY")
    print("=" * 50)

    # Check final results
    exe_path = Path("dist/MediaUploader.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ Build Status: SUCCESS")
        print(f"📁 EXE Location: {exe_path.absolute()}")
        print(f"📊 File Size: {size_mb:.1f} MB")

        # Check launcher
        launcher_path = Path("run_media_uploader.bat")
        if launcher_path.exists():
            print(f"📝 Launcher: {launcher_path}")

        # Show what's included
        print(f"\n📦 What's included:")
        print(f"   • Complete Media Uploader application")
        print(f"   • Qt GUI framework (PySide6)")
        print(f"   • YouTube API integration")
        print(f"   • Media processing capabilities")
        print(f"   • All dependencies (standalone)")

    else:
        print(f"❌ Build Status: FAILED")
        print(f"   EXE file not found")


def main():
    """Main monitoring function."""
    try:
        show_detailed_status()
        show_build_summary()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped by user")
        show_build_summary()


if __name__ == "__main__":
    main()
