"""
Settings manager for the Media Uploader application.

Handles saving and loading user preferences and settings.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_data_dir

# Set up logging
logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages application settings and user preferences."""

    def __init__(self):
        self.settings_file = get_data_dir() / "settings.json"
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def _load_settings(self):
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
                logger.debug(f"Loaded settings from {self.settings_file}")
            else:
                logger.debug("No settings file found, starting with empty settings")
        except Exception as e:
            # If loading fails, start with empty settings
            logger.warning(f"Failed to load settings from {self.settings_file}: {e}")
            self._settings = {}

    def _save_settings(self):
        """Save settings to file."""
        try:
            # Ensure data directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved settings to {self.settings_file}")
        except Exception as e:
            # If saving fails, continue without saving
            logger.warning(f"Failed to save settings to {self.settings_file}: {e}")

    def get_last_media_path(self) -> Optional[Path]:
        """Get the last used media folder path."""
        try:
            path_str = self._settings.get('last_media_path')
            if path_str:
                path = Path(path_str)
                # Only return if the path still exists
                if path.exists() and path.is_dir():
                    logger.debug(f"Returning last media path: {path}")
                    return path
                else:
                    logger.debug(f"Last media path no longer exists: {path}")
            return None
        except Exception as e:
            logger.warning(f"Error getting last media path: {e}")
            return None

    def set_last_media_path(self, path: Path):
        """Set the last used media folder path."""
        try:
            self._settings['last_media_path'] = str(path)
            self._save_settings()
            logger.debug(f"Set last media path: {path}")
        except Exception as e:
            logger.warning(f"Error setting last media path: {e}")

    def get_last_image_path(self) -> Optional[Path]:
        """Get the last used image folder path."""
        try:
            path_str = self._settings.get('last_image_path')
            if path_str:
                path = Path(path_str)
                # Only return if the path still exists
                if path.exists() and path.is_dir():
                    logger.debug(f"Returning last image path: {path}")
                    return path
                else:
                    logger.debug(f"Last image path no longer exists: {path}")
            return None
        except Exception as e:
            logger.warning(f"Error getting last image path: {e}")
            return None

    def set_last_image_path(self, path: Path):
        """Set the last used image folder path."""
        try:
            self._settings['last_image_path'] = str(path)
            self._save_settings()
            logger.debug(f"Set last image path: {path}")
        except Exception as e:
            logger.warning(f"Error setting last image path: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        try:
            return self._settings.get(key, default)
        except Exception as e:
            logger.warning(f"Error getting setting '{key}': {e}")
            return default

    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        try:
            self._settings[key] = value
            self._save_settings()
            logger.debug(f"Set setting '{key}': {value}")
        except Exception as e:
            logger.warning(f"Error setting setting '{key}': {e}")

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        try:
            return self._settings.copy()
        except Exception as e:
            logger.warning(f"Error getting all settings: {e}")
            return {}
