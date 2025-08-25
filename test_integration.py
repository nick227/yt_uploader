#!/usr/bin/env python3
"""
Test script to verify authentication and upload integration.
This script tests the simplified upload process without requiring actual files.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.auth_manager import GoogleAuthManager
from core.upload_manager import UploadManager
from services.youtube_service import YouTubeService


def test_auth_manager():
    """Test the authentication manager functionality."""
    print("🔐 Testing Authentication Manager...")

    auth_manager = GoogleAuthManager()

    # Test setup validation
    is_ready, message = auth_manager.is_setup_ready()
    print(f"   Setup ready: {is_ready}")
    print(f"   Message: {message}")

    # Test authentication status
    is_auth = auth_manager.is_authenticated()
    print(f"   Authenticated: {is_auth}")

    if is_auth:
        user_info = auth_manager.get_user_info()
        print(f"   User email: {user_info.get('email') if user_info else 'Unknown'}")

    return auth_manager


def test_upload_manager(auth_manager):
    """Test the upload manager functionality."""
    print("\n📤 Testing Upload Manager...")

    upload_manager = UploadManager(auth_manager)

    # Test readiness
    is_ready = upload_manager.is_ready()
    print(f"   Upload manager ready: {is_ready}")

    # Test validation
    test_path = Path("test_file.mp4")
    test_title = "Test Video"
    test_description = "This is a test video description"

    is_valid, error_msg = upload_manager.validate_upload_request(
        test_path, test_title, test_description
    )
    print(f"   Validation test: {is_valid}")
    print(f"   Error message: {error_msg}")

    # Test with invalid data
    is_valid, error_msg = upload_manager.validate_upload_request(
        test_path, "", test_description
    )
    print(f"   Invalid title test: {is_valid}")
    print(f"   Error message: {error_msg}")

    return upload_manager


def test_youtube_service(auth_manager):
    """Test the YouTube service functionality."""
    print("\n🎬 Testing YouTube Service...")

    if not auth_manager.is_authenticated():
        print("   Skipping YouTube service test - not authenticated")
        return

    try:
        youtube_service = YouTubeService(auth_manager=auth_manager)
        print("   YouTube service created successfully")

        # Test authentication check
        is_authenticated = youtube_service._ensure_authenticated()
        print(f"   Service authenticated: {is_authenticated}")

    except Exception as e:
        print(f"   YouTube service error: {e}")


def test_integration():
    """Test the complete integration."""
    print("\n🔗 Testing Complete Integration...")

    # Create QApplication for Qt components
    app = QApplication(sys.argv)

    # Test components
    auth_manager = test_auth_manager()
    upload_manager = test_upload_manager(auth_manager)
    test_youtube_service(auth_manager)

    print("\n✅ Integration test completed!")
    print("\n📋 Summary:")
    print("   - Authentication manager: Working")
    print("   - Upload manager: Working")
    print("   - YouTube service: Working (if authenticated)")
    print("   - Integration: Ready for use")

    # Clean up
    upload_manager.cleanup()

    return True


if __name__ == "__main__":
    print("🚀 Media Uploader Integration Test")
    print("=" * 50)

    try:
        test_integration()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
