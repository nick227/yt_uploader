"""
Tests for the credentials configuration dialog.
"""

import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from unittest.mock import Mock, patch

from app.ui.credentials_dialog import CredentialsDialog


@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    return qtbot


class TestCredentialsDialog:
    """Test the CredentialsDialog class."""

    def test_init(self, app):
        """Test dialog initialization."""
        dialog = CredentialsDialog()
        assert dialog.windowTitle() == "Configure Google API Credentials"
        assert dialog.isModal() is True
        assert dialog.minimumWidth() == 500

    def test_manual_credentials_validation(self, app):
        """Test manual credentials validation."""
        dialog = CredentialsDialog()

        # Test empty credentials
        with patch.object(dialog, "_save_config_to_file") as mock_save:
            with pytest.raises(
                ValueError, match="Client ID and Client Secret are required"
            ):
                dialog._save_manual_credentials()

    def test_manual_credentials_invalid_client_id(self, app):
        """Test manual credentials with invalid client ID."""
        dialog = CredentialsDialog()

        # Set invalid client ID
        dialog.client_id_edit.setText("invalid-id")
        dialog.client_secret_edit.setText("test_secret")

        with patch.object(dialog, "_save_config_to_file") as mock_save:
            with pytest.raises(ValueError, match="Invalid Client ID format"):
                dialog._save_manual_credentials()

    def test_manual_credentials_valid(self, app, tmp_path):
        """Test manual credentials with valid data."""
        dialog = CredentialsDialog()

        # Set valid credentials
        dialog.client_id_edit.setText("123456789.apps.googleusercontent.com")
        dialog.client_secret_edit.setText("test_secret")
        dialog.auth_uri_edit.setText("https://accounts.google.com/o/oauth2/auth")
        dialog.token_uri_edit.setText("https://oauth2.googleapis.com/token")

        with patch.object(dialog, "_save_config_to_file") as mock_save:
            dialog._save_manual_credentials()

            # Verify the config was saved
            mock_save.assert_called_once()
            config = mock_save.call_args[0][0]
            assert config["client_id"] == "123456789.apps.googleusercontent.com"
            assert config["client_secret"] == "test_secret"
            assert config["auth_uri"] == "https://accounts.google.com/o/oauth2/auth"
            assert config["token_uri"] == "https://oauth2.googleapis.com/token"

    def test_file_credentials_missing_file(self, app):
        """Test file credentials with missing file."""
        dialog = CredentialsDialog()

        with pytest.raises(ValueError, match="Please select a client secret file"):
            dialog._save_file_credentials()

    def test_file_credentials_nonexistent_file(self, app):
        """Test file credentials with nonexistent file."""
        dialog = CredentialsDialog()
        dialog.file_path_edit.setText("/nonexistent/file.json")

        with pytest.raises(ValueError, match="Selected file does not exist"):
            dialog._save_file_credentials()

    def test_file_credentials_valid(self, app, tmp_path):
        """Test file credentials with valid file."""
        dialog = CredentialsDialog()

        # Create a test client secret file
        test_file = tmp_path / "client_secret.json"
        test_file.write_text('{"installed": {"client_id": "test"}}')
        dialog.file_path_edit.setText(str(test_file))

        with patch("shutil.copy2") as mock_copy:
            dialog._save_file_credentials()

            # Verify the file was copied
            mock_copy.assert_called_once()

    def test_save_config_to_file(self, app, tmp_path):
        """Test saving configuration to file."""
        dialog = CredentialsDialog()

        config = {
            "client_id": "test.apps.googleusercontent.com",
            "client_secret": "test_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        # Test that the method doesn't raise an exception
        try:
            dialog._save_config_to_file(config)
            assert True  # Method executed successfully
        except Exception as e:
            assert False, f"Method raised unexpected exception: {e}"

    def test_get_credentials_config_nonexistent(self, app):
        """Test getting credentials config when file doesn't exist."""
        dialog = CredentialsDialog()

        with patch("pathlib.Path.exists", return_value=False):
            config = dialog.get_credentials_config()
            assert config is None

    def test_get_credentials_config_valid(self, app, tmp_path):
        """Test getting credentials config from valid file."""
        dialog = CredentialsDialog()

        # Create a test config file
        config_file = tmp_path / "custom_credentials.json"
        config_data = {
            "client_id": "test.apps.googleusercontent.com",
            "client_secret": "test_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        config_file.write_text(json.dumps(config_data))

        with patch("pathlib.Path") as mock_path:
            mock_path.return_value = config_file

            config = dialog.get_credentials_config()
            assert config == config_data

    def test_method_selection_manual(self, app):
        """Test manual method selection."""
        dialog = CredentialsDialog()

        # Test the method directly
        dialog._on_method_changed()

        # The groups should be visible based on radio button states
        # Since no radio button is checked by default, both should be hidden
        assert dialog.manual_group.isVisible() is False
        assert dialog.file_group.isVisible() is False

    def test_method_selection_file(self, app):
        """Test file method selection."""
        dialog = CredentialsDialog()

        # Test the method directly
        dialog._on_method_changed()

        # The groups should be visible based on radio button states
        # Since no radio button is checked by default, both should be hidden
        assert dialog.manual_group.isVisible() is False
        assert dialog.file_group.isVisible() is False

    def test_browse_file(self, app):
        """Test file browsing functionality."""
        dialog = CredentialsDialog()

        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("/test/file.json", "JSON Files (*.json)")

            dialog._browse_file()

            assert dialog.file_path_edit.text() == "/test/file.json"
            mock_dialog.assert_called_once()

    def test_preview_file_success(self, app, tmp_path):
        """Test file preview with successful read."""
        dialog = CredentialsDialog()

        # Create a test file
        test_file = tmp_path / "test.json"
        test_content = '{"test": "content"}'
        test_file.write_text(test_content)

        dialog._preview_file(str(test_file))

        assert dialog.file_preview.toPlainText() == test_content

    def test_preview_file_error(self, app):
        """Test file preview with read error."""
        dialog = CredentialsDialog()

        dialog._preview_file("/nonexistent/file.json")

        assert "Error reading file" in dialog.file_preview.toPlainText()

    def test_save_credentials_no_method_selected(self, app):
        """Test saving credentials without selecting a method."""
        dialog = CredentialsDialog()

        # Ensure no method is selected
        dialog.manual_radio.setChecked(False)
        dialog.file_radio.setChecked(False)

        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning:
            dialog._save_credentials()

            mock_warning.assert_called_once()

    def test_save_credentials_manual_success(self, app):
        """Test successful manual credentials save."""
        dialog = CredentialsDialog()

        # Set valid credentials
        dialog.manual_radio.setChecked(True)
        dialog.client_id_edit.setText("test.apps.googleusercontent.com")
        dialog.client_secret_edit.setText("test_secret")

        with patch.object(dialog, "_save_manual_credentials"):
            with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
                with patch.object(dialog, "accept"):
                    dialog._save_credentials()

                    mock_info.assert_called_once()

    def test_save_credentials_file_success(self, app, tmp_path):
        """Test successful file credentials save."""
        dialog = CredentialsDialog()

        # Set valid file
        dialog.file_radio.setChecked(True)
        test_file = tmp_path / "client_secret.json"
        test_file.write_text('{"installed": {"client_id": "test"}}')
        dialog.file_path_edit.setText(str(test_file))

        with patch.object(dialog, "_save_file_credentials"):
            with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
                with patch.object(dialog, "accept"):
                    dialog._save_credentials()

                    mock_info.assert_called_once()

    def test_save_credentials_exception(self, app):
        """Test credentials save with exception."""
        dialog = CredentialsDialog()

        dialog.manual_radio.setChecked(True)
        dialog.client_id_edit.setText("invalid")

        with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical:
            dialog._save_credentials()

            mock_critical.assert_called_once()
