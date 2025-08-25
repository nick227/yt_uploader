"""
Unit tests for the Google Authentication Manager.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from unittest.mock import MagicMock, Mock, patch

from core.auth_manager import AuthError, AuthState, ClientSecretError, GoogleAuthManager


class TestAuthState:
    """Test the AuthState dataclass."""

    def test_auth_state_creation(self):
        """Test creating AuthState instances."""
        # Test with minimal data
        state = AuthState(is_authenticated=False)
        assert state.is_authenticated is False
        assert state.user_email is None
        assert state.expires_at is None
        assert state.scopes == ["https://www.googleapis.com/auth/youtube.upload"]

        # Test with full data
        expires_at = datetime.now() + timedelta(hours=1)
        state = AuthState(
            is_authenticated=True,
            user_email="test@example.com",
            expires_at=expires_at,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
        assert state.is_authenticated is True
        assert state.user_email == "test@example.com"
        assert state.expires_at == expires_at

    def test_auth_state_to_dict(self):
        """Test converting AuthState to dictionary."""
        expires_at = datetime.now() + timedelta(hours=1)
        state = AuthState(
            is_authenticated=True, user_email="test@example.com", expires_at=expires_at
        )

        data = state.to_dict()
        assert data["is_authenticated"] is True
        assert data["user_email"] == "test@example.com"
        assert data["expires_at"] == expires_at.isoformat()
        assert data["scopes"] == ["https://www.googleapis.com/auth/youtube.upload"]

    def test_auth_state_from_dict(self):
        """Test creating AuthState from dictionary."""
        expires_at = datetime.now() + timedelta(hours=1)
        data = {
            "is_authenticated": True,
            "user_email": "test@example.com",
            "expires_at": expires_at.isoformat(),
            "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
        }

        state = AuthState.from_dict(data)
        assert state.is_authenticated is True
        assert state.user_email == "test@example.com"
        assert state.expires_at == expires_at


class TestGoogleAuthManager:
    """Test the GoogleAuthManager class."""

    @pytest.fixture
    def temp_private_dir(self, temp_dir):
        """Create a temporary private directory for auth files."""
        private_dir = temp_dir / "private"
        private_dir.mkdir()
        return private_dir

    @pytest.fixture
    def auth_manager(self, temp_private_dir):
        """Create an AuthManager instance for testing."""
        return GoogleAuthManager(str(temp_private_dir / "client_secret.json"))

    def test_init_creates_private_directory(self, temp_dir):
        """Test that initialization creates the private directory."""
        private_dir = temp_dir / "private"
        client_secret_path = private_dir / "client_secret.json"

        with patch("core.auth_manager.Path") as mock_path:
            mock_path.return_value = client_secret_path
            auth_manager = GoogleAuthManager(str(client_secret_path))

            assert private_dir.exists()

    def test_validate_client_secret_missing_file(self, auth_manager):
        """Test validation when client secret file is missing."""
        with pytest.raises(ClientSecretError, match="Client secret file not found"):
            auth_manager._validate_client_secret()

    def test_validate_client_secret_invalid_json(self, auth_manager, temp_private_dir):
        """Test validation with invalid JSON."""
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text("invalid json")

        with pytest.raises(ClientSecretError, match="Invalid JSON"):
            auth_manager._validate_client_secret()

    def test_validate_client_secret_missing_installed_section(
        self, auth_manager, temp_private_dir
    ):
        """Test validation with missing 'installed' section."""
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text('{"invalid": "format"}')

        with pytest.raises(ClientSecretError, match="missing 'installed' section"):
            auth_manager._validate_client_secret()

    def test_validate_client_secret_missing_fields(
        self, auth_manager, temp_private_dir
    ):
        """Test validation with missing required fields."""
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text('{"installed": {"client_id": "test"}}')

        with pytest.raises(ClientSecretError, match="Missing required fields"):
            auth_manager._validate_client_secret()

    def test_validate_client_secret_invalid_client_id(
        self, auth_manager, temp_private_dir
    ):
        """Test validation with invalid client_id format."""
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text(
            """{
            "installed": {
                "client_id": "invalid_id",
                "client_secret": "secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }"""
        )

        with pytest.raises(ClientSecretError, match="Invalid client_id format"):
            auth_manager._validate_client_secret()

    def test_validate_client_secret_valid(self, auth_manager, temp_private_dir):
        """Test validation with valid client secret."""
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text(
            """{
            "installed": {
                "client_id": "123456789.apps.googleusercontent.com",
                "client_secret": "test_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }"""
        )

        assert auth_manager._validate_client_secret() is True

    def test_is_authenticated_not_authenticated(self, auth_manager):
        """Test is_authenticated when not authenticated."""
        auth_manager._auth_state = AuthState(is_authenticated=False)
        assert auth_manager.is_authenticated() is False

    def test_is_authenticated_with_valid_credentials(
        self, auth_manager, mock_credentials
    ):
        """Test is_authenticated with valid credentials."""
        auth_manager._auth_state = AuthState(is_authenticated=True)
        auth_manager._credentials = mock_credentials

        assert auth_manager.is_authenticated() is True

    @patch("core.auth_manager.Request")
    def test_is_authenticated_refresh_expired_credentials(
        self, mock_request, auth_manager, mock_credentials
    ):
        """Test is_authenticated with expired credentials that can be refreshed."""
        auth_manager._auth_state = AuthState(is_authenticated=True)
        mock_credentials.expired = True
        mock_credentials.refresh_token = "refresh_token"
        auth_manager._credentials = mock_credentials

        assert auth_manager.is_authenticated() is True
        mock_credentials.refresh.assert_called_once_with(mock_request.return_value)

    @patch("core.auth_manager.Request")
    def test_is_authenticated_refresh_fails(
        self, mock_request, auth_manager, mock_credentials
    ):
        """Test is_authenticated when refresh fails."""
        auth_manager._auth_state = AuthState(is_authenticated=True)
        mock_credentials.expired = True
        mock_credentials.refresh_token = "refresh_token"
        mock_credentials.refresh.side_effect = Exception("Refresh failed")
        auth_manager._credentials = mock_credentials

        assert auth_manager.is_authenticated() is False

    def test_get_user_email_not_authenticated(self, auth_manager):
        """Test get_user_email when not authenticated."""
        auth_manager._auth_state = AuthState(is_authenticated=False)
        assert auth_manager.get_user_email() is None

    def test_get_user_email_authenticated(self, auth_manager, mock_credentials):
        """Test get_user_email when authenticated."""
        auth_manager._auth_state = AuthState(
            is_authenticated=True, user_email="test@example.com"
        )
        auth_manager._credentials = mock_credentials
        # Mock the _get_user_info method to return the expected email
        with patch.object(auth_manager, "_get_user_info") as mock_get_info:
            mock_get_info.return_value = {"email": "test@example.com"}
            assert auth_manager.get_user_email() == "test@example.com"

    def test_get_credentials_not_authenticated(self, auth_manager):
        """Test get_credentials when not authenticated."""
        auth_manager._auth_state = AuthState(is_authenticated=False)
        assert auth_manager.get_credentials() is None

    def test_get_credentials_authenticated(self, auth_manager, mock_credentials):
        """Test get_credentials when authenticated."""
        auth_manager._auth_state = AuthState(is_authenticated=True)
        auth_manager._credentials = mock_credentials
        assert auth_manager.get_credentials() == mock_credentials

    def test_is_setup_ready_missing_file(self, auth_manager):
        """Test is_setup_ready when client secret file is missing."""
        is_ready, message = auth_manager.is_setup_ready()
        assert is_ready is False
        assert "not found" in message

    def test_is_setup_ready_valid_setup(self, auth_manager, temp_private_dir):
        """Test is_setup_ready with valid setup."""
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text(
            """{
            "installed": {
                "client_id": "123456789.apps.googleusercontent.com",
                "client_secret": "test_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }"""
        )

        is_ready, message = auth_manager.is_setup_ready()
        assert is_ready is True
        assert message == "Ready"

    @patch("core.auth_manager.InstalledAppFlow")
    @patch("core.auth_manager.Request")
    def test_login_success(
        self, mock_request, mock_flow, auth_manager, temp_private_dir, mock_credentials
    ):
        """Test successful login."""
        # Setup valid client secret
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text(
            """{
            "installed": {
                "client_id": "123456789.apps.googleusercontent.com",
                "client_secret": "test_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }"""
        )

        # Update auth manager to use the correct client secret path
        auth_manager.client_secret_path = client_secret_file

        # Ensure no existing credentials are loaded
        auth_manager._credentials = None

        # Mock flow
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_credentials
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance

        # Mock the _save_credentials method to avoid file I/O issues
        with patch.object(auth_manager, "_save_credentials"):
            # Test login
            result = auth_manager.login()
            assert result is True
            assert auth_manager._credentials == mock_credentials

    def test_login_missing_client_secret(self, auth_manager):
        """Test login with missing client secret file."""
        result = auth_manager.login()
        assert result is False

    @patch("core.auth_manager.InstalledAppFlow")
    def test_login_flow_fails(self, mock_flow, auth_manager, temp_private_dir):
        """Test login when OAuth flow fails."""
        # Setup valid client secret
        client_secret_file = temp_private_dir / "client_secret.json"
        client_secret_file.write_text(
            """{
            "installed": {
                "client_id": "123456789.apps.googleusercontent.com",
                "client_secret": "test_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }"""
        )

        # Update auth manager to use the correct client secret path
        auth_manager.client_secret_path = client_secret_file

        # Mock flow to fail
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.side_effect = Exception("OAuth failed")
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance

        # Test login
        result = auth_manager.login()
        assert result is False

    def test_logout_clears_state(self, auth_manager, mock_credentials):
        """Test logout clears authentication state."""
        # Setup authenticated state
        auth_manager._credentials = mock_credentials
        auth_manager._auth_state = AuthState(is_authenticated=True)

        # Test logout
        auth_manager.logout()

        assert auth_manager._credentials is None
        assert auth_manager._auth_state.is_authenticated is False

    def test_get_auth_info(self, auth_manager, mock_credentials):
        """Test get_auth_info returns correct information."""
        auth_manager._auth_state = AuthState(
            is_authenticated=True, user_email="test@example.com"
        )
        auth_manager._credentials = mock_credentials

        # Mock the _get_user_info method to return the expected email
        with patch.object(auth_manager, "_get_user_info") as mock_get_info:
            mock_get_info.return_value = {"email": "test@example.com"}

            info = auth_manager.get_auth_info()
            assert info["is_authenticated"] is True
            assert info["user_email"] == "test@example.com"
            assert "scopes" in info
