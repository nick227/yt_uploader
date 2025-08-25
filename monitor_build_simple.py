#!/usr/bin/env python3
"""
Simple real-time build monitoring without external dependencies.
"""

import os
import time
from datetime import datetime
from pathlib import Path


def count_files_in_directory(path):
    """Count files in directory recursively."""
    if not path.exists():
        return 0
    return len(list(path.rglob("*")))


def get_directory_size_mb(path):
    """Get directory size in MB."""
    if not path.exists():
        return 0
    total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total_size / (1024 * 1024)


def get_build_progress():
    """Get current build progress information."""
    build_dir = Path("build")
    dist_dir = Path("dist")

    progress = {
        "phase": "unknown",
        "files_collected": 0,
        "build_size_mb": 0,
        "dist_size_mb": 0,
        "exe_created": False,
        "exe_size_mb": 0,
        "key_components": {},
    }

    # Check build directory
    if build_dir.exists():
        progress["build_size_mb"] = get_directory_size_mb(build_dir)

        # Check analysis directory
        analysis_dir = build_dir / "MediaUploader"
        if analysis_dir.exists():
            progress["phase"] = "collection"
            progress["files_collected"] = count_files_in_directory(analysis_dir)

            # Check key components
            components = {
                "PySide6": "Qt Framework",
                "google": "Google APIs",
                "_internal": "Python Runtime",
                "app": "Application Code",
                "core": "Core Modules",
                "services": "Services",
                "infra": "Infrastructure",
            }

            for dir_name, description in components.items():
                dir_path = analysis_dir / dir_name
                if dir_path.exists():
                    file_count = count_files_in_directory(dir_path)
                    progress["key_components"][description] = file_count

    # Check dist directory
    if dist_dir.exists():
        progress["dist_size_mb"] = get_directory_size_mb(dist_dir)

        # Check for final EXE
        exe_path = dist_dir / "MediaUploader.exe"
        if exe_path.exists():
            progress["phase"] = "complete"
            progress["exe_created"] = True
            progress["exe_size_mb"] = exe_path.stat().st_size / (1024 * 1024)

    return progress


def show_progress_bar(current, total, width=40):
    """Show a simple progress bar."""
    if total == 0:
        return "[" + " " * width + "] 0%"

    percentage = min(current / total, 1.0)
    filled = int(width * percentage)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage*100:.1f}%"


def show_detailed_status():
    """Show detailed build status with real-time updates."""
    print("🔍 Media Uploader Build Monitor")
    print("=" * 50)

    start_time = time.time()
    last_file_count = 0

    while True:
        # Clear screen
        os.system("cls" if os.name == "nt" else "clear")

        # Get current time and elapsed time
        current_time = datetime.now().strftime("%H:%M:%S")
        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)

        # Get progress
        progress = get_build_progress()

        # Display header
        print(f"🕐 {current_time} - Elapsed: {elapsed_minutes}m {elapsed_seconds}s")
        print("=" * 50)

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

            # Show progress bar (estimate based on typical file counts)
            if progress["phase"] == "collection":
                estimated_total = 5000  # Typical for Qt + Google APIs
                progress_bar = show_progress_bar(
                    progress["files_collected"], estimated_total
                )
                print(f"📈 Progress: {progress_bar}")

                # Show rate of file collection
                if last_file_count > 0:
                    rate = progress["files_collected"] - last_file_count
                    if rate > 0:
                        print(f"⚡ Collection Rate: +{rate} files per update")

        # Show key components
        if progress["key_components"]:
            print(f"\n📁 Key Components:")
            for desc, count in progress["key_components"].items():
                print(f"   {desc}: {count:,} files")

        # Show size information
        total_size = progress["build_size_mb"] + progress["dist_size_mb"]
        if total_size > 0:
            print(f"\n💾 Build Size: {total_size:.1f} MB")
            if progress["build_size_mb"] > 0:
                print(f"   build/: {progress['build_size_mb']:.1f} MB")
            if progress["dist_size_mb"] > 0:
                print(f"   dist/: {progress['dist_size_mb']:.1f} MB")

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

        # Show tips based on phase
        print(f"\n💡 Tips:")
        if progress["phase"] == "collection":
            print(f"   • Collection phase can take 5-10 minutes")
            print(f"   • PyInstaller is copying Qt libraries and modules")
            print(f"   • File count should increase over time")
            if progress["files_collected"] > last_file_count:
                print(f"   • ✅ Activity detected - build is progressing")
            else:
                print(f"   • ⏳ No new files - may be processing large modules")
        elif progress["phase"] == "unknown":
            print(f"   • Build may be in analysis phase")
            print(f"   • Check if PyInstaller process is running")

        print(f"\n⏳ Monitoring... Press Ctrl+C to stop")

        # Update last file count
        last_file_count = progress["files_collected"]

        # Wait before next update
        time.sleep(3)


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
