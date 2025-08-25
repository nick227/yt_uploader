#!/usr/bin/env python3
"""
Debug script to test EXE dependencies and imports.
"""

import sys
import traceback


def test_imports():
    """Test all critical imports that the EXE needs."""
    print("Testing critical imports...")

    try:
        print("✓ Testing PySide6 imports...")
        from PySide6.QtCore import Qt, QThread, Signal
        from PySide6.QtMultimedia import QMediaPlayer
        from PySide6.QtMultimediaWidgets import QVideoWidget
        from PySide6.QtWidgets import QApplication, QMainWindow

        print("✓ PySide6 imports successful")
    except Exception as e:
        print(f"✗ PySide6 import failed: {e}")
        return False

    try:
        print("✓ Testing Google API imports...")
        from google.auth.credentials import Credentials
        from googleapiclient.discovery import build

        print("✓ Google API imports successful")
    except Exception as e:
        print(f"✗ Google API import failed: {e}")
        return False

    try:
        print("✓ Testing app imports...")
        from app.splash_screen import show_splash_screen
        from app.ui.main_window import MainWindow

        print("✓ App imports successful")
    except Exception as e:
        print(f"✗ App import failed: {e}")
        traceback.print_exc()
        return False

    return True


def test_basic_functionality():
    """Test basic functionality without creating GUI."""
    print("\nTesting basic functionality...")

    try:
        # Test that we can create a QApplication
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        print("✓ QApplication creation successful")

        # Test that we can create a simple widget
        from PySide6.QtWidgets import QWidget

        widget = QWidget()
        print("✓ Widget creation successful")

        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("=== EXE Debug Test ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")

    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False

    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed!")
        return False

    print("\n✅ All tests passed! The application should work.")
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
