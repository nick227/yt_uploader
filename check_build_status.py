#!/usr/bin/env python3
"""
Check the current build status and show progress.
"""

import os
import time
from pathlib import Path


def check_build_status():
    """Check what's happening during the build."""
    print("🔍 Checking build status...\n")

    # Check if build directories exist
    build_dir = Path("build")
    dist_dir = Path("dist")
    spec_file = Path("MediaUploader.spec")

    print("📁 Directory Status:")
    print(
        f"   build/ directory: {'✅ Exists' if build_dir.exists() else '❌ Not found'}"
    )
    print(f"   dist/ directory: {'✅ Exists' if dist_dir.exists() else '❌ Not found'}")
    print(
        f"   MediaUploader.spec: {'✅ Exists' if spec_file.exists() else '❌ Not found'}"
    )

    # Check build progress
    if build_dir.exists():
        print(f"\n🔧 Build Progress:")

        # Check for analysis files
        analysis_dir = build_dir / "MediaUploader"
        if analysis_dir.exists():
            print(f"   ✅ Analysis phase completed")

            # Count collected files
            collected_files = list(analysis_dir.rglob("*"))
            print(f"   📊 Collected {len(collected_files)} files")

            # Show some key directories
            key_dirs = ["PySide6", "google", "_internal"]
            for key_dir in key_dirs:
                key_path = analysis_dir / key_dir
                if key_path.exists():
                    file_count = len(list(key_path.rglob("*")))
                    print(f"   📦 {key_dir}/: {file_count} files")
        else:
            print(f"   ⏳ Analysis phase in progress...")

    # Check for final EXE
    exe_path = dist_dir / "MediaUploader.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 Build Complete!")
        print(f"   📁 EXE location: {exe_path}")
        print(f"   📊 File size: {size_mb:.1f} MB")
    else:
        print(f"\n⏳ Build in progress...")
        print(f"   Final EXE not yet created")

    # Check for any error logs
    log_files = list(Path(".").glob("*.log"))
    if log_files:
        print(f"\n📋 Log files found:")
        for log_file in log_files:
            print(f"   📄 {log_file.name}")

    # Show current time for reference
    print(f"\n⏰ Current time: {time.strftime('%H:%M:%S')}")


def show_build_tips():
    """Show tips for the build process."""
    print(f"\n💡 Build Tips:")
    print(f"   • First build takes 5-15 minutes")
    print(f"   • Subsequent builds are faster (3-8 minutes)")
    print(f"   • The long pause is normal during collection phase")
    print(f"   • PyInstaller is copying hundreds of Qt library files")
    print(f"   • Don't interrupt the process - let it complete")
    print(f"   • Check Task Manager to see PyInstaller activity")


def main():
    """Main function."""
    check_build_status()
    show_build_tips()


if __name__ == "__main__":
    main()
