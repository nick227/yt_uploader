"""
Credentials configuration dialog for user-provided Google API credentials.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from core.styles import StyleTheme


class CredentialsDialog(QDialog):
    """Dialog for configuring Google API credentials."""

    # Signal emitted when credentials are successfully configured
    credentials_configured = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Google API Credentials")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._setup_ui()
        self._load_existing_credentials()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Title and description
        title_label = QLabel("Google API Credentials Configuration")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 8px;"
        )
        layout.addWidget(title_label)

        desc_label = QLabel(
            "To upload videos to YouTube, you need to provide your own Google API credentials.\n"
            "This allows you to upload to your own YouTube channel with your own API quota."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 16px;")
        layout.addWidget(desc_label)

        # Method selection
        self._setup_method_selection(layout)

        # Manual credentials section
        self._setup_manual_credentials(layout)

        # File import section
        self._setup_file_import(layout)

        # Instructions section
        self._setup_instructions(layout)

        # Buttons
        self._setup_buttons(layout)

    def _setup_method_selection(self, layout):
        """Setup method selection radio buttons."""
        method_group = QGroupBox("Configuration Method")
        method_layout = QVBoxLayout(method_group)

        self.manual_radio = QCheckBox("Enter credentials manually")
        self.file_radio = QCheckBox("Import from client_secret.json file")

        self.manual_radio.toggled.connect(self._on_method_changed)
        self.file_radio.toggled.connect(self._on_method_changed)

        method_layout.addWidget(self.manual_radio)
        method_layout.addWidget(self.file_radio)

        layout.addWidget(method_group)

    def _setup_manual_credentials(self, layout):
        """Setup manual credentials input fields."""
        self.manual_group = QGroupBox("Manual Credentials")
        manual_layout = QVBoxLayout(self.manual_group)

        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText(
            "your-client-id.apps.googleusercontent.com"
        )
        client_id_layout.addWidget(self.client_id_edit)
        manual_layout.addLayout(client_id_layout)

        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_layout.addWidget(QLabel("Client Secret:"))
        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_edit.setPlaceholderText("Enter your client secret")
        client_secret_layout.addWidget(self.client_secret_edit)
        manual_layout.addLayout(client_secret_layout)

        # Auth URI (optional, with default)
        auth_uri_layout = QHBoxLayout()
        auth_uri_layout.addWidget(QLabel("Auth URI:"))
        self.auth_uri_edit = QLineEdit("https://accounts.google.com/o/oauth2/auth")
        auth_uri_layout.addWidget(self.auth_uri_edit)
        manual_layout.addLayout(auth_uri_layout)

        # Token URI (optional, with default)
        token_uri_layout = QHBoxLayout()
        token_uri_layout.addWidget(QLabel("Token URI:"))
        self.token_uri_edit = QLineEdit("https://oauth2.googleapis.com/token")
        token_uri_layout.addWidget(self.token_uri_edit)
        manual_layout.addLayout(token_uri_layout)

        layout.addWidget(self.manual_group)
        self.manual_group.setVisible(False)

    def _setup_file_import(self, layout):
        """Setup file import section."""
        self.file_group = QGroupBox("Import from File")
        file_layout = QVBoxLayout(self.file_group)

        # File path
        file_path_layout = QHBoxLayout()
        file_path_layout.addWidget(QLabel("Client Secret File:"))
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select client_secret.json file")
        file_path_layout.addWidget(self.file_path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_path_layout.addWidget(browse_btn)

        file_layout.addLayout(file_path_layout)

        # File preview
        self.file_preview = QTextEdit()
        self.file_preview.setMaximumHeight(100)
        self.file_preview.setPlaceholderText("File contents will be shown here...")
        self.file_preview.setReadOnly(True)
        file_layout.addWidget(self.file_preview)

        layout.addWidget(self.file_group)
        self.file_group.setVisible(False)

    def _setup_instructions(self, layout):
        """Setup instructions section."""
        instructions_group = QGroupBox("How to Get Credentials")
        instructions_layout = QVBoxLayout(instructions_group)

        instructions_text = """
1. Go to <a href="https://console.cloud.google.com/">Google Cloud Console</a>
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Desktop application" as the application type
6. Download the client_secret.json file
7. Use the credentials from the file or enter them manually above

Note: You'll need to add your email as a test user in the OAuth consent screen.
        """

        instructions_label = QLabel(instructions_text)
        instructions_label.setOpenExternalLinks(True)
        instructions_label.setWordWrap(True)
        instructions_layout.addWidget(instructions_label)

        layout.addWidget(instructions_group)

    def _setup_buttons(self, layout):
        """Setup dialog buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Credentials")
        save_btn.clicked.connect(self._save_credentials)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_method_changed(self):
        """Handle method selection change."""
        self.manual_group.setVisible(self.manual_radio.isChecked())
        self.file_group.setVisible(self.file_radio.isChecked())

    def _browse_file(self):
        """Browse for client secret file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Client Secret File",
            str(Path.home()),
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            self.file_path_edit.setText(file_path)
            self._preview_file(file_path)

    def _preview_file(self, file_path: str):
        """Preview the contents of the selected file and prefill manual fields."""
        try:
            with open(file_path, "r") as f:
                content = f.read()
                self.file_preview.setPlainText(content)

                # Parse JSON and prefill manual input fields
                import json

                data = json.loads(content)

                if "installed" in data:
                    installed = data["installed"]

                    # Prefill manual input fields with values from JSON
                    if "client_id" in installed:
                        self.client_id_edit.setText(installed["client_id"])
                    if "client_secret" in installed:
                        self.client_secret_edit.setText(installed["client_secret"])
                    if "auth_uri" in installed:
                        self.auth_uri_edit.setText(installed["auth_uri"])
                    if "token_uri" in installed:
                        self.token_uri_edit.setText(installed["token_uri"])

        except Exception as e:
            self.file_preview.setPlainText(f"Error reading file: {e}")

    def _load_existing_credentials(self):
        """Load existing credentials if any."""
        # This could be enhanced to load from a saved configuration
        pass

    def _save_credentials(self):
        """Save the configured credentials."""
        try:
            # Check if we have a file selected and manual fields are filled
            file_path = self.file_path_edit.text().strip()
            manual_fields_filled = (
                self.client_id_edit.text().strip()
                and self.client_secret_edit.text().strip()
            )

            # If file is selected and manual fields are filled, prefer manual entry
            if file_path and manual_fields_filled:
                self._save_manual_credentials()
            elif self.manual_radio.isChecked():
                self._save_manual_credentials()
            elif self.file_radio.isChecked():
                self._save_file_credentials()
            else:
                QMessageBox.warning(
                    self, "Configuration Error", "Please select a configuration method."
                )
                return

            QMessageBox.information(
                self,
                "Success",
                "Credentials saved successfully! You can now log in to YouTube.",
            )
            self.credentials_configured.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save credentials: {str(e)}")

    def _save_manual_credentials(self):
        """Save manually entered credentials."""
        client_id = self.client_id_edit.text().strip()
        client_secret = self.client_secret_edit.text().strip()
        auth_uri = self.auth_uri_edit.text().strip()
        token_uri = self.token_uri_edit.text().strip()

        if not client_id or not client_secret:
            raise ValueError("Client ID and Client Secret are required")

        if not client_id.endswith(".apps.googleusercontent.com"):
            raise ValueError("Invalid Client ID format")

        # Save to configuration file
        config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": auth_uri,
            "token_uri": token_uri,
        }

        self._save_config_to_file(config)

    def _save_file_credentials(self):
        """Save credentials from file."""
        file_path = self.file_path_edit.text().strip()

        if not file_path:
            raise ValueError("Please select a client secret file")

        if not Path(file_path).exists():
            raise ValueError("Selected file does not exist")

        # Copy file to private directory
        private_dir = Path("private")
        private_dir.mkdir(exist_ok=True)

        import shutil

        shutil.copy2(file_path, private_dir / "client_secret.json")

    def _save_config_to_file(self, config: dict):
        """Save configuration to file."""
        import json

        config_dir = Path("private")
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "custom_credentials.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_credentials_config(self) -> Optional[dict]:
        """Get the configured credentials for use by the auth manager."""
        try:
            config_file = Path("private/custom_credentials.json")
            if config_file.exists():
                import json

                with open(config_file, "r") as f:
                    return json.load(f)

            # Check for file-based credentials
            client_secret_file = Path("private/client_secret.json")
            if client_secret_file.exists():
                return {"type": "file", "path": str(client_secret_file)}

        except Exception:
            pass

        return None
