#!/usr/bin/env python3
"""
Test script to verify the build environment and dependencies.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        import PySide6

        print(f"✓ PySide6: {PySide6.__version__}")
    except ImportError as e:
        print(f"✗ PySide6: {e}")
        return False

    try:
        import google.auth

        print("✓ google.auth")
    except ImportError as e:
        print(f"✗ google.auth: {e}")
        return False

    try:
        import googleapiclient

        print("✓ googleapiclient")
    except ImportError as e:
        print(f"✗ googleapiclient: {e}")
        return False

    try:
        import PyInstaller

        print(f"✓ PyInstaller: {PyInstaller.__version__}")
    except ImportError as e:
        print(f"✗ PyInstaller: {e}")
        print("  Install with: pip install pyinstaller")
        return False

    return True


def test_app_imports():
    """Test that the application modules can be imported."""
    print("\nTesting application imports...")

    try:
        from app.main import main

        print("✓ app.main")
    except ImportError as e:
        print(f"✗ app.main: {e}")
        return False

    try:
        from app.ui.main_window import MainWindow

        print("✓ app.ui.main_window")
    except ImportError as e:
        print(f"✗ app.ui.main_window: {e}")
        return False

    try:
        from core.auth_manager import GoogleAuthManager

        print("✓ core.auth_manager")
    except ImportError as e:
        print(f"✗ core.auth_manager: {e}")
        return False

    try:
        from services.youtube_service import YouTubeService

        print("✓ services.youtube_service")
    except ImportError as e:
        print(f"✗ services.youtube_service: {e}")
        return False

    return True


def test_qt_conflicts():
    """Test for Qt binding conflicts."""
    print("\nTesting for Qt binding conflicts...")

    qt_modules = []

    try:
        import PySide6

        qt_modules.append("PySide6")
    except ImportError:
        pass

    try:
        import PyQt6

        qt_modules.append("PyQt6")
    except ImportError:
        pass

    try:
        import PyQt5

        qt_modules.append("PyQt5")
    except ImportError:
        pass

    if len(qt_modules) > 1:
        print(f"⚠ Multiple Qt bindings found: {', '.join(qt_modules)}")
        print("  This may cause PyInstaller conflicts. Consider excluding unused ones.")
        return False
    else:
        print(f"✓ Single Qt binding: {qt_modules[0] if qt_modules else 'None'}")
        return True


def test_file_structure():
    """Test that required files exist."""
    print("\nTesting file structure...")

    required_files = [
        "app/main.py",
        "app/ui/main_window.py",
        "core/auth_manager.py",
        "services/youtube_service.py",
        "requirements.txt",
    ]

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            return False

    return True


def main():
    """Run all tests."""
    print("🔍 Testing Media Uploader build environment...\n")

    tests = [
        ("File Structure", test_file_structure),
        ("Qt Conflicts", test_qt_conflicts),
        ("Dependencies", test_imports),
        ("Application Modules", test_app_imports),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Error in {test_name}: {e}")
            results.append((test_name, False))
        print()

    # Summary
    print("--- Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✅ Build environment is ready!")
        print("You can now run: python build_simple.py")
    else:
        print("\n❌ Build environment has issues.")
        print("Please fix the failing tests before building.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
