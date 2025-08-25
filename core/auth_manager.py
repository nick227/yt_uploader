"""
Google Authentication Manager for YouTube API access.
Handles OAuth2 authentication with persistent login across app sessions.
"""

import base64
import hashlib
import json
import logging
import os
import pickle
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from google.auth.exceptions import GoogleAuthError, RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)


@dataclass
class AuthState:
    """Authentication state information."""

    is_authenticated: bool
    user_email: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: list[str] = None
    last_refresh: Optional[datetime] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_authenticated": self.is_authenticated,
            "user_email": self.user_email,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scopes": self.scopes,
            "last_refresh": (
                self.last_refresh.isoformat() if self.last_refresh else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthState":
        """Create from dictionary."""
        return cls(
            is_authenticated=data.get("is_authenticated", False),
            user_email=data.get("user_email"),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            scopes=data.get(
                "scopes", ["https://www.googleapis.com/auth/youtube.upload"]
            ),
            last_refresh=(
                datetime.fromisoformat(data["last_refresh"])
                if data.get("last_refresh")
                else None
            ),
        )


class AuthError(Exception):
    """Custom authentication error."""

    pass


class ClientSecretError(AuthError):
    """Error with client secret configuration."""

    pass


class CredentialError(AuthError):
    """Error with credentials."""

    pass


class GoogleAuthManager:
    """Manages Google OAuth2 authentication for YouTube API."""

    # YouTube API scopes
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def __init__(self, client_secret_path: Optional[str] = None):
        self.client_secret_path = (
            Path(client_secret_path) if client_secret_path else None
        )
        self.credentials_path = Path("private/token.pickle")
        self.auth_state_path = Path("private/auth_state.json")

        # Custom credentials support
        self._custom_client_id: Optional[str] = None
        self._custom_client_secret: Optional[str] = None
        self._custom_auth_uri: Optional[str] = None
        self._custom_token_uri: Optional[str] = None

        # Ensure private directory exists with proper permissions
        self._ensure_private_directory()

        self._credentials: Optional[Credentials] = None
        self._auth_state = AuthState(is_authenticated=False)
        self._user_info_cache: Optional[Dict[str, Any]] = None
        self._last_refresh_attempt: Optional[datetime] = None
        self._refresh_cooldown_seconds = 30  # Prevent frequent refresh attempts

        # Load existing authentication state
        self._load_auth_state()

    def set_custom_credentials(
        self,
        client_id: str,
        client_secret: str,
        auth_uri: str = "https://accounts.google.com/o/oauth2/auth",
        token_uri: str = "https://oauth2.googleapis.com/token",
    ) -> None:
        """
        Set custom OAuth2 credentials for user-provided Google API access.

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
            auth_uri: OAuth2 authorization URI (default: Google's standard)
            token_uri: OAuth2 token URI (default: Google's standard)
        """
        self._custom_client_id = client_id
        self._custom_client_secret = client_secret
        self._custom_auth_uri = auth_uri
        self._custom_token_uri = token_uri

        # Clear existing credentials when switching to custom ones
        self._credentials = None
        self._auth_state = AuthState(is_authenticated=False)
        self._save_auth_state()

        logger.info("Custom credentials set successfully")

    def has_custom_credentials(self) -> bool:
        """Check if custom credentials are configured."""
        return (
            self._custom_client_id is not None
            and self._custom_client_secret is not None
        )

    def get_credentials_info(self) -> Dict[str, Optional[str]]:
        """Get information about current credentials configuration."""
        if self.has_custom_credentials():
            return {
                "type": "custom",
                "client_id": self._custom_client_id,
                "auth_uri": self._custom_auth_uri,
                "token_uri": self._custom_token_uri,
            }
        elif self.client_secret_path and self.client_secret_path.exists():
            return {"type": "file", "path": str(self.client_secret_path)}
        else:
            return {"type": "none", "message": "No credentials configured"}

    def _ensure_private_directory(self) -> None:
        """Ensure private directory exists with proper permissions."""
        private_dir = self.credentials_path.parent
        private_dir.mkdir(exist_ok=True)

        # Set restrictive permissions on Unix-like systems
        try:
            os.chmod(private_dir, 0o700)  # Owner read/write/execute only
        except OSError:
            pass  # Windows doesn't support chmod

    def _validate_client_secret(self) -> bool:
        """Validate client secret file format."""
        try:
            if not self.client_secret_path:
                raise ClientSecretError("No client secret path configured")

            if not self.client_secret_path.exists():
                raise ClientSecretError(
                    f"Client secret file not found: {self.client_secret_path}"
                )

            with open(self.client_secret_path, "r") as f:
                data = json.load(f)

            # Validate required fields
            if "installed" not in data:
                raise ClientSecretError(
                    "Invalid client secret format: missing 'installed' section"
                )

            installed = data["installed"]
            required_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
            missing_fields = [
                field for field in required_fields if field not in installed
            ]

            if missing_fields:
                raise ClientSecretError(
                    f"Missing required fields in client secret: {missing_fields}"
                )

            # Validate client_id format
            if not installed["client_id"].endswith(".apps.googleusercontent.com"):
                raise ClientSecretError("Invalid client_id format")

            return True

        except json.JSONDecodeError as e:
            raise ClientSecretError(f"Invalid JSON in client secret file: {e}")
        except Exception as e:
            raise ClientSecretError(f"Error validating client secret: {e}")

    def _load_auth_state(self) -> None:
        """Load authentication state from file."""
        try:
            if self.auth_state_path.exists():
                with open(self.auth_state_path, "r") as f:
                    data = json.load(f)
                    self._auth_state = AuthState.from_dict(data)
                logger.info("Loaded authentication state from file")
        except Exception as e:
            logger.warning(f"Failed to load auth state: {e}")
            self._auth_state = AuthState(is_authenticated=False)

    def _save_auth_state(self) -> None:
        """Save authentication state to file."""
        try:
            data = self._auth_state.to_dict()
            with open(self.auth_state_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Saved authentication state to file")
        except Exception as e:
            logger.error(f"Failed to save auth state: {e}")

    def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from pickle file with error handling."""
        try:
            if self.credentials_path.exists():
                with open(self.credentials_path, "rb") as token:
                    credentials = pickle.load(token)

                    # Validate credentials object
                    if not isinstance(credentials, Credentials):
                        logger.warning("Invalid credentials object in file")
                        return None

                    logger.info("Loaded credentials from file")
                    return credentials
        except (pickle.PickleError, EOFError) as e:
            logger.warning(f"Corrupted credentials file: {e}")
            # Remove corrupted file
            try:
                self.credentials_path.unlink()
            except OSError:
                pass
        except Exception as e:
            logger.warning(f"Failed to load credentials: {e}")
        return None

    def _save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to pickle file with error handling."""
        try:
            # Create temporary file first
            temp_path = self.credentials_path.with_suffix(".tmp")
            with open(temp_path, "wb") as token:
                pickle.dump(credentials, token)

            # Atomic move
            temp_path.replace(self.credentials_path)
            logger.info("Saved credentials to file")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            # Clean up temp file
            try:
                temp_path.unlink()
            except OSError:
                pass

    def _get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get user information from Google API."""
        if self._user_info_cache:
            return self._user_info_cache

        try:
            if not self._credentials or not self._credentials.valid:
                return None

            # Try to get user info from ID token
            if hasattr(self._credentials, "id_token") and self._credentials.id_token:
                try:
                    import jwt

                    decoded = jwt.decode(
                        self._credentials.id_token, options={"verify_signature": False}
                    )
                    self._user_info_cache = {
                        "email": decoded.get("email"),
                        "name": decoded.get("name"),
                        "picture": decoded.get("picture"),
                    }
                    return self._user_info_cache
                except Exception as e:
                    logger.debug(f"Failed to decode ID token: {e}")

            # Fallback: try to get user info from Google API
            try:
                from googleapiclient.discovery import build

                service = build("oauth2", "v2", credentials=self._credentials)
                user_info = service.userinfo().get().execute()
                self._user_info_cache = user_info
                return user_info
            except Exception as e:
                logger.debug(f"Failed to get user info from API: {e}")

        except Exception as e:
            logger.warning(f"Error getting user info: {e}")

        return None

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self._auth_state.is_authenticated:
            return False

        # Ensure credentials are loaded
        if not self._credentials:
            self._credentials = self._load_credentials()
            if not self._credentials:
                logger.warning("No credentials found despite authenticated state")
                self.logout()
                return False

        # Check if credentials are still valid
        if self._credentials.expired:
            if self._credentials.refresh_token:
                # Check if we're in cooldown period
                if (
                    self._last_refresh_attempt
                    and (datetime.now() - self._last_refresh_attempt).total_seconds()
                    < self._refresh_cooldown_seconds
                ):
                    logger.debug("Refresh cooldown active, skipping refresh attempt")
                    return True  # Assume still valid during cooldown

                try:
                    self._last_refresh_attempt = datetime.now()
                    logger.info("Refreshing expired credentials")
                    self._credentials.refresh(Request())
                    self._save_credentials(self._credentials)
                    self._update_auth_state()
                    return True
                except RefreshError as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    self.logout()
                    return False
                except Exception as e:
                    logger.warning(f"Unexpected error refreshing credentials: {e}")
                    self.logout()
                    return False
            else:
                logger.info("No refresh token available")
                self.logout()
                return False

        return True

    def get_user_email(self) -> Optional[str]:
        """Get the authenticated user's email."""
        if not self.is_authenticated():
            return None

        user_info = self._get_user_info()
        return user_info.get("email") if user_info else None

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get complete user information."""
        if not self.is_authenticated():
            return None
        return self._get_user_info()

    def get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials for API calls."""
        if not self.is_authenticated():
            return None
        return self._credentials

    def login(self) -> bool:
        """Perform OAuth2 login flow with enhanced error handling."""
        try:
            # Load existing credentials
            self._credentials = self._load_credentials()

            # If no valid credentials available, let the user log in
            if not self._credentials or not self._credentials.valid:
                if (
                    self._credentials
                    and self._credentials.expired
                    and self._credentials.refresh_token
                ):
                    logger.info("Refreshing expired credentials")
                    self._credentials.refresh(Request())
                else:
                    logger.info("Starting new OAuth flow")

                    if self.has_custom_credentials():
                        # Use custom credentials
                        flow = self._create_flow_from_custom_credentials()
                    else:
                        # Use file-based credentials
                        self._validate_client_secret()
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(self.client_secret_path), self.SCOPES
                        )

                    self._credentials = flow.run_local_server(port=0)

                # Save the credentials for the next run
                self._save_credentials(self._credentials)

            # Update authentication state
            self._update_auth_state()
            user_email = self.get_user_email()
            logger.info(f"Successfully authenticated as: {user_email}")
            return True

        except ClientSecretError as e:
            logger.error(f"Client secret error: {e}")
            return False
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {e}")
            # Check if it's a verification issue
            if "verification" in str(e).lower() or "not completed" in str(e).lower():
                raise AuthError(
                    "Google OAuth2 verification required. Please:\n"
                    "1. Go to Google Cloud Console → OAuth consent screen\n"
                    "2. Add your email as a test user, OR\n"
                    "3. Complete the verification process\n"
                    "4. Try logging in again"
                )
            self.logout()
            return False
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            # Check if it's a verification issue
            if "verification" in str(e).lower() or "not completed" in str(e).lower():
                raise AuthError(
                    "Google OAuth2 verification required. Please:\n"
                    "1. Go to Google Cloud Console → OAuth consent screen\n"
                    "2. Add your email as a test user, OR\n"
                    "3. Complete the verification process\n"
                    "4. Try logging in again"
                )
            self.logout()
            return False

    def _create_flow_from_custom_credentials(self) -> InstalledAppFlow:
        """Create OAuth flow from custom credentials."""
        if not self.has_custom_credentials():
            raise ClientSecretError("No custom credentials configured")

        # Create client config dict from custom credentials
        client_config = {
            "installed": {
                "client_id": self._custom_client_id,
                "client_secret": self._custom_client_secret,
                "auth_uri": self._custom_auth_uri,
                "token_uri": self._custom_token_uri,
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"],
            }
        }

        return InstalledAppFlow.from_client_config(client_config, self.SCOPES)

    def logout(self) -> None:
        """Logout and clear authentication state."""
        try:
            # Remove credential files
            if self.credentials_path.exists():
                os.remove(self.credentials_path)

            # Clear state and cache
            self._credentials = None
            self._auth_state = AuthState(is_authenticated=False)
            self._user_info_cache = None
            self._save_auth_state()

            logger.info("Successfully logged out")
        except Exception as e:
            logger.error(f"Logout failed: {e}")

    def _update_auth_state(self) -> None:
        """Update authentication state from current credentials."""
        if self._credentials and self._credentials.valid:
            user_info = self._get_user_info()

            self._auth_state = AuthState(
                is_authenticated=True,
                user_email=user_info.get("email") if user_info else None,
                expires_at=(
                    datetime.fromtimestamp(self._credentials.expiry.timestamp())
                    if self._credentials.expiry
                    else None
                ),
                scopes=self._credentials.scopes,
                last_refresh=datetime.now(),
            )
            self._save_auth_state()

    def get_auth_info(self) -> Dict[str, Any]:
        """Get authentication information for display."""
        user_info = self.get_user_info()
        return {
            "is_authenticated": self.is_authenticated(),
            "user_email": self.get_user_email(),
            "user_name": user_info.get("name") if user_info else None,
            "user_picture": user_info.get("picture") if user_info else None,
            "expires_at": (
                self._auth_state.expires_at.isoformat()
                if self._auth_state.expires_at
                else None
            ),
            "last_refresh": (
                self._auth_state.last_refresh.isoformat()
                if self._auth_state.last_refresh
                else None
            ),
            "scopes": self._auth_state.scopes,
        }

    def is_setup_ready(self) -> Tuple[bool, str]:
        """Check if authentication is properly set up."""
        # Check if we have custom credentials configured
        if self.has_custom_credentials():
            return True, "Custom credentials configured"

        # Check if we have a client secret path configured
        if not self.client_secret_path:
            return False, "No client secret path configured"

        if not self.client_secret_path.exists():
            return False, "Client secret file not found"

        try:
            self._validate_client_secret()
            return True, "Ready"
        except ClientSecretError as e:
            return False, str(e)

    @contextmanager
    def get_authenticated_service(self, service_name: str, version: str):
        """Context manager for getting authenticated Google API service."""
        if not self.is_authenticated():
            raise AuthError("Not authenticated")

        credentials = self.get_credentials()
        if not credentials:
            raise AuthError("No valid credentials")

        try:
            from googleapiclient.discovery import build

            service = build(service_name, version, credentials=credentials)
            yield service
        except Exception as e:
            logger.error(f"Failed to create {service_name} service: {e}")
            raise AuthError(f"Service creation failed: {e}")
