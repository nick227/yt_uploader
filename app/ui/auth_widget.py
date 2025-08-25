"""
Authentication widget for Google login/logout functionality.
"""

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.auth_manager import AuthError, ClientSecretError, GoogleAuthManager
from core.styles import StyleBuilder, theme

from .credentials_dialog import CredentialsDialog


class AuthWorker(QThread):
    """Background worker for authentication operations."""

    # Signals
    login_success = Signal(str)  # user_email
    login_failed = Signal(str)  # error_message
    logout_success = Signal()
    logout_failed = Signal(str)  # error_message

    def __init__(self, auth_manager: GoogleAuthManager, operation: str):
        super().__init__()
        self.auth_manager = auth_manager
        self.operation = operation

    def run(self):
        """Run the authentication operation."""
        try:
            if self.operation == "login":
                success = self.auth_manager.login()
                if success:
                    user_email = self.auth_manager.get_user_email() or "Unknown"
                    self.login_success.emit(user_email)
                else:
                    self.login_failed.emit("Login failed - please try again")
            elif self.operation == "logout":
                self.auth_manager.logout()
                self.logout_success.emit()
        except ClientSecretError as e:
            self.login_failed.emit(f"Configuration error: {str(e)}")
        except AuthError as e:
            error_msg = str(e)
            if "verification" in error_msg.lower():
                self.login_failed.emit("VERIFICATION_REQUIRED")
            else:
                self.login_failed.emit(f"Authentication error: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            if (
                "verification" in error_msg.lower()
                or "not completed" in error_msg.lower()
            ):
                self.login_failed.emit("VERIFICATION_REQUIRED")
            else:
                self.login_failed.emit(f"Unexpected error: {error_msg}")


class AuthWidget(QWidget):
    """Authentication widget with login/logout functionality."""

    # Signals
    auth_state_changed = Signal(bool)  # Emitted when authentication state changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = GoogleAuthManager()
        self.auth_worker = None
        self._setup_ui()
        self._load_custom_credentials()
        self._update_auth_display()

        # Check authentication state periodically
        self._auth_check_timer = QTimer()
        self._auth_check_timer.timeout.connect(self._check_auth_state)
        self._auth_check_timer.start(30000)  # Check every 30 seconds

    def _load_custom_credentials(self):
        """Load custom credentials on startup if available."""
        config = self._load_credentials_config()
        if config and config.get("type") != "file":
            # Manual credentials - set them in the auth manager
            self.auth_manager.set_custom_credentials(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                auth_uri=config.get(
                    "auth_uri", "https://accounts.google.com/o/oauth2/auth"
                ),
                token_uri=config.get(
                    "token_uri", "https://oauth2.googleapis.com/token"
                ),
            )

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Transparent container - no background
        layout.addStretch()  # Push everything to the right

        # Info button for setup instructions
        self.info_button = QToolButton()
        self.info_button.setText("ℹ️")
        self.info_button.setToolTip("Setup Google API credentials")
        self.info_button.setStyleSheet(
            f"""
            QToolButton {{
                padding: 4px 8px;
                background: {theme.background_elevated};
                color: {theme.text_primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                font-size: 12px;
                min-width: 24px;
                min-height: 24px;
            }}
            QToolButton:hover {{
                background: {theme.background_secondary};
                border-color: {theme.primary};
            }}
            """
        )
        self.info_button.clicked.connect(self._show_setup_instructions)
        layout.addWidget(self.info_button)

        # Login/Logout button
        self.auth_button = QPushButton("Login with Google")
        self.auth_button.setStyleSheet(StyleBuilder.button_primary())
        self.auth_button.clicked.connect(self._handle_auth_click)
        layout.addWidget(self.auth_button)

        # Hidden elements for internal use
        self.status_icon = QLabel("")
        self.status_icon.setVisible(False)
        layout.addWidget(self.status_icon)

        self.status_text = QLabel("")
        self.status_text.setVisible(False)
        layout.addWidget(self.status_text)

        self.setup_button = QToolButton()
        self.setup_button.setVisible(False)
        layout.addWidget(self.setup_button)

    def _update_auth_display(self):
        """Update the authentication display based on current state."""
        is_authenticated = self.auth_manager.is_authenticated()

        if is_authenticated:
            self.auth_button.setText("Logout")
            self.auth_button.setStyleSheet(StyleBuilder.button_danger())
        else:
            # Check setup status
            is_ready, message = self.auth_manager.is_setup_ready()
            if not is_ready:
                self.auth_button.setText("Setup")
                self.auth_button.setStyleSheet(StyleBuilder.button_secondary())
            else:
                self.auth_button.setText("Login with Google")
                self.auth_button.setStyleSheet(StyleBuilder.button_primary())

    def _handle_auth_click(self):
        """Handle login/logout button click."""
        if self.auth_manager.is_authenticated():
            self._logout()
        else:
            # Check if setup is needed
            is_ready, message = self.auth_manager.is_setup_ready()
            if not is_ready:
                self._show_setup_instructions()
            else:
                self._login()

    def _login(self):
        """Perform login in background thread."""
        if self.auth_worker and self.auth_worker.isRunning():
            return

        self.auth_button.setEnabled(False)
        self.auth_button.setText("Logging in...")

        # Create and start worker
        self.auth_worker = AuthWorker(self.auth_manager, "login")
        self.auth_worker.login_success.connect(self._on_login_success)
        self.auth_worker.login_failed.connect(self._on_login_failed)
        self.auth_worker.finished.connect(self._on_worker_finished)
        self.auth_worker.start()

    def _logout(self):
        """Perform logout in background thread."""
        if self.auth_worker and self.auth_worker.isRunning():
            return

        self.auth_button.setEnabled(False)
        self.auth_button.setText("Logging out...")

        # Create and start worker
        self.auth_worker = AuthWorker(self.auth_manager, "logout")
        self.auth_worker.logout_success.connect(self._on_logout_success)
        self.auth_worker.logout_failed.connect(self._on_logout_failed)
        self.auth_worker.finished.connect(self._on_worker_finished)
        self.auth_worker.start()

    def _on_login_success(self, user_email: str):
        """Handle successful login."""
        self.status_text.setText(f"✅ Logged in as {user_email}")
        self.auth_state_changed.emit(True)
        self._update_auth_display()

    def _on_login_failed(self, error_message: str):
        """Handle login failure."""
        self.status_text.setText("❌ Login failed")

        if error_message == "VERIFICATION_REQUIRED":
            self._show_verification_instructions()
        else:
            QMessageBox.warning(
                self,
                "Login Failed",
                f"Failed to login with Google:\n\n{error_message}\n\n"
                "Please check your setup and try again.",
            )

        self.auth_state_changed.emit(False)
        self._update_auth_display()

    def _on_logout_success(self):
        """Handle successful logout."""
        self.status_text.setText("✅ Logged out successfully")
        self.auth_state_changed.emit(False)
        self._update_auth_display()

    def _on_logout_failed(self, error_message: str):
        """Handle logout failure."""
        self.status_text.setText("❌ Logout failed")
        QMessageBox.warning(
            self, "Logout Failed", f"Failed to logout:\n\n{error_message}"
        )
        self._update_auth_display()

    def _on_worker_finished(self):
        """Handle worker thread completion."""
        self.auth_button.setEnabled(True)
        self.auth_worker = None

    def _check_auth_state(self):
        """Periodically check authentication state."""
        current_auth = self.auth_manager.is_authenticated()
        # Update display if state changed
        self._update_auth_display()

    def _show_setup_info(self):
        """Show setup information."""
        is_ready, message = self.auth_manager.is_setup_ready()

        if is_ready:
            info_text = "✅ Authentication is properly configured and ready to use."
        else:
            info_text = f"⚠️ Setup required: {message}"

        QMessageBox.information(
            self,
            "Authentication Setup",
            f"{info_text}\n\n"
            "To use YouTube uploads, you need to:\n"
            "1. Create a Google Cloud Project\n"
            "2. Enable YouTube Data API v3\n"
            "3. Create OAuth 2.0 credentials\n"
            "4. Download client_secret.json to the 'private' folder\n\n"
            "See README.md for detailed setup instructions.",
        )

    def _show_setup_instructions(self):
        """Show credentials configuration dialog."""
        dialog = CredentialsDialog(self)
        dialog.credentials_configured.connect(self._on_credentials_configured)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Credentials were configured successfully
            self._update_auth_display()
        else:
            # User cancelled - show manual instructions as fallback
            QMessageBox.information(
                self,
                "Setup Required",
                "To upload to YouTube, you need to set up Google authentication:\n\n"
                "1. Go to https://console.cloud.google.com/\n"
                "2. Create a new project or select existing one\n"
                "3. Enable YouTube Data API v3\n"
                "4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'\n"
                "5. Choose 'Desktop application'\n"
                "6. Download the JSON file\n"
                "7. Rename it to 'client_secret.json'\n"
                "8. Place it in the 'private' folder\n\n"
                "After setup, restart the application and try logging in again.",
            )

    def _on_credentials_configured(self):
        """Handle successful credentials configuration."""
        # Update the auth manager with the new credentials
        config = self._load_credentials_config()
        if config:
            if config.get("type") == "file":
                # File-based credentials - auth manager will use the file
                pass
            else:
                # Manual credentials - set them in the auth manager
                self.auth_manager.set_custom_credentials(
                    client_id=config["client_id"],
                    client_secret=config["client_secret"],
                    auth_uri=config.get(
                        "auth_uri", "https://accounts.google.com/o/oauth2/auth"
                    ),
                    token_uri=config.get(
                        "token_uri", "https://oauth2.googleapis.com/token"
                    ),
                )

        self._update_auth_display()

    def _load_credentials_config(self):
        """Load credentials configuration from file."""
        try:
            import json
            from pathlib import Path

            config_file = Path("private/custom_credentials.json")
            if config_file.exists():
                with open(config_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _show_verification_instructions(self):
        """Show verification instructions."""
        QMessageBox.information(
            self,
            "OAuth2 Verification Required",
            "Your Google OAuth2 application needs verification. "
            "Here are your options:\n\n"
            "🔧 QUICK FIX (Recommended for testing):\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Navigate to 'APIs & Services' → 'OAuth consent screen'\n"
            "3. Under 'Test users', add your Google email address\n"
            "4. Save and try logging in again\n\n"
            "📋 FULL VERIFICATION:\n"
            "1. Complete all required fields in OAuth consent screen\n"
            "2. Submit for Google verification\n"
            "3. Wait for approval (can take several days)\n\n"
            "⚠️ For now, you can also:\n"
            "- Click 'Advanced' on the warning page\n"
            "- Click 'Go to [App Name] (unsafe)'\n"
            "- Continue with authentication",
        )

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.auth_manager.is_authenticated()

    def get_credentials(self):
        """Get authentication credentials."""
        return self.auth_manager.get_credentials()

    def get_auth_info(self):
        """Get authentication information."""
        return self.auth_manager.get_auth_info()

    def is_setup_ready(self) -> bool:
        """Check if authentication is properly set up."""
        is_ready, _ = self.auth_manager.is_setup_ready()
        return is_ready
