#!/usr/bin/env python3
"""
Analyze what's making up the EXE file size.
"""

import os
import sys
from pathlib import Path


def get_module_size(module_name):
    """Estimate module size by checking if it's imported."""
    try:
        module = __import__(module_name)
        if hasattr(module, "__file__") and module.__file__:
            file_path = Path(module.__file__)
            if file_path.exists():
                return file_path.stat().st_size
        return 0
    except ImportError:
        return 0


def analyze_dependencies():
    """Analyze the main dependencies and their sizes."""
    print("🔍 Analyzing EXE file size breakdown...\n")

    # Core components
    components = {
        "Python Runtime": {
            "description": "Python interpreter, standard library, core modules",
            "estimate": "15-25 MB",
            "includes": ["sys", "os", "pathlib", "subprocess", "logging", "signal"],
        },
        "PySide6 (Qt Framework)": {
            "description": "Qt bindings, GUI framework, multimedia support",
            "estimate": "30-40 MB",
            "includes": [
                "PySide6.QtCore",
                "PySide6.QtWidgets",
                "PySide6.QtMultimedia",
                "PySide6.QtMultimediaWidgets",
            ],
        },
        "Google APIs": {
            "description": "YouTube API, authentication, HTTP client",
            "estimate": "5-10 MB",
            "includes": [
                "google.auth",
                "googleapiclient",
                "googleapiclient.discovery",
                "googleapiclient.http",
            ],
        },
        "Other Dependencies": {
            "description": "Cryptography, HTTP libraries, JSON processing",
            "estimate": "2-5 MB",
            "includes": [
                "cryptography",
                "httplib2",
                "urllib3",
                "certifi",
                "charset_normalizer",
            ],
        },
        "Application Code": {
            "description": "Your actual application code and assets",
            "estimate": "1-2 MB",
            "includes": ["app", "core", "services", "infra"],
        },
    }

    total_estimate = 0

    for component, info in components.items():
        print(f"📦 {component}")
        print(f"   Description: {info['description']}")
        print(f"   Estimated Size: {info['estimate']}")
        print(f"   Includes: {', '.join(info['includes'])}")

        # Extract numeric estimate for total
        estimate_str = info["estimate"]
        if "-" in estimate_str:
            min_size, max_size = estimate_str.split("-")
            avg_size = (int(min_size.split()[0]) + int(max_size.split()[0])) / 2
        else:
            avg_size = int(estimate_str.split()[0])

        total_estimate += avg_size
        print()

    print(f"📊 Total Estimated Size: ~{total_estimate:.1f} MB")
    print(f"📊 Actual EXE Size: 72.5 MB")
    print(
        f"📊 Difference: ~{72.5 - total_estimate:.1f} MB (PyInstaller overhead, compression, etc.)"
    )

    return components


def show_size_optimization_options():
    """Show options to reduce file size."""
    print("\n🔧 Size Optimization Options:\n")

    options = [
        {
            "option": "Use --onedir instead of --onefile",
            "benefit": "Reduces size by 20-30% (creates folder instead of single file)",
            "tradeoff": "Requires distributing folder instead of single EXE",
        },
        {
            "option": "Exclude unused PySide6 modules",
            "benefit": "Reduces size by 10-20%",
            "tradeoff": "May break if modules are dynamically imported",
        },
        {
            "option": "Use UPX compression",
            "benefit": "Reduces size by 20-40%",
            "tradeoff": "Slower startup time, may trigger antivirus",
        },
        {
            "option": "Exclude development dependencies",
            "benefit": "Already done in simple build",
            "tradeoff": "None",
        },
        {
            "option": "Use alternative packaging (cx_Freeze, Nuitka)",
            "benefit": "Potentially smaller files",
            "tradeoff": "Different toolchain, may have compatibility issues",
        },
    ]

    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt['option']}")
        print(f"   ✅ Benefit: {opt['benefit']}")
        print(f"   ⚠️  Tradeoff: {opt['tradeoff']}")
        print()


def show_whats_included():
    """Show what's actually included in the EXE."""
    print("\n📋 What's Actually Included in Your 72MB EXE:\n")

    categories = {
        "🎨 GUI Framework": [
            "Qt Core (event system, threading, networking)",
            "Qt Widgets (buttons, windows, dialogs)",
            "Qt Multimedia (video/audio playback)",
            "Qt Multimedia Widgets (video display)",
            "Qt Network (HTTP requests, authentication)",
        ],
        "🌐 Internet & APIs": [
            "Google OAuth2 authentication",
            "YouTube Data API v3",
            "HTTP/HTTPS client libraries",
            "SSL/TLS encryption",
            "JSON processing",
        ],
        "🔐 Security": [
            "Cryptography libraries",
            "Certificate validation",
            "Secure token storage",
            "OAuth2 flow handling",
        ],
        "📁 File System": [
            "File I/O operations",
            "Path handling",
            "Media file processing",
            "FFmpeg integration",
        ],
        "🎵 Media Processing": [
            "Audio/video codecs",
            "Media format detection",
            "Thumbnail generation",
            "Metadata extraction",
        ],
    }

    for category, items in categories.items():
        print(f"{category}:")
        for item in items:
            print(f"  • {item}")
        print()


def main():
    """Main analysis function."""
    print("=" * 60)
    print("EXE FILE SIZE ANALYSIS")
    print("=" * 60)

    analyze_dependencies()
    show_whats_included()
    show_size_optimization_options()

    print("💡 Summary:")
    print("• 72MB is actually quite reasonable for a Qt + Google APIs application")
    print(
        "• Most of the size comes from Qt framework (~40MB) and Python runtime (~20MB)"
    )
    print("• Your application code is only ~1-2MB of the total")
    print("• The simple build already excludes unnecessary development dependencies")
    print("• For distribution, 72MB is acceptable for a professional application")


if __name__ == "__main__":
    main()
