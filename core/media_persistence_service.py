"""
Media persistence service for the Media Uploader application.
Handles saving and loading user changes to media items.
"""

import json
import logging
import threading
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import get_data_dir

# Set up logging
logger = logging.getLogger(__name__)


class DataType(Enum):
    """Enumeration of supported data types."""
    IMAGE_THUMBNAIL = "image_thumbnail"
    TITLE = "title"
    DESCRIPTION = "description"


@dataclass
class DataField:
    """Represents a data field with validation and transformation logic."""
    key: str
    validator: Optional[Callable[[Any], bool]] = None
    transformer: Optional[Callable[[Any], Any]] = None

    def validate(self, value: Any) -> bool:
        """Validate the value using the validator function."""
        if self.validator is None:
            return True
        return self.validator(value)

    def transform(self, value: Any) -> Any:
        """Transform the value using the transformer function."""
        if self.transformer is None:
            return value
        return self.transformer(value)


class DataManager:
    """Manages data storage and retrieval operations with performance optimizations."""

    def __init__(self, persistence_file: Path):
        self.persistence_file = persistence_file
        self._data: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self._lock = threading.RLock()  # Thread-safe operations
        self._load_data()

    def _load_data(self) -> None:
        """Load data from file."""
        with self._lock:
            try:
                if self.persistence_file.exists():
                    with open(self.persistence_file, 'r', encoding='utf-8') as f:
                        self._data = json.load(f)
                    logger.debug(f"Loaded data from {self.persistence_file}")
                else:
                    logger.debug("No persistence file found, starting with empty data")
            except Exception as e:
                logger.warning(f"Failed to load data from {self.persistence_file}: {e}")
                self._data = {}

    def _save_data(self) -> None:
        """Save data to file if dirty."""
        with self._lock:
            if not self._dirty:
                return

            try:
                self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.persistence_file, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
                self._dirty = False
                logger.debug(f"Saved data to {self.persistence_file}")
            except Exception as e:
                logger.warning(f"Failed to save data to {self.persistence_file}: {e}")

    def get_media_data(self, media_key: str) -> Dict[str, Any]:
        """Get data for a media key."""
        with self._lock:
            return self._data.get(media_key, {})

    def set_media_data(self, media_key: str, data: Dict[str, Any]) -> None:
        """Set data for a media key."""
        with self._lock:
            self._data[media_key] = data
            self._dirty = True
            self._save_data()

    def update_media_data(self, media_key: str, key: str, value: Any) -> None:
        """Update a specific key in media data."""
        with self._lock:
            if media_key not in self._data:
                self._data[media_key] = {}
            self._data[media_key][key] = value
            self._dirty = True
            self._save_data()

    def batch_update_media_data(self, updates: List[tuple]) -> None:
        """Batch update multiple media data entries for better performance."""
        with self._lock:
            for media_key, key, value in updates:
                if media_key not in self._data:
                    self._data[media_key] = {}
                self._data[media_key][key] = value
            self._dirty = True
            self._save_data()

    def remove_media_data(self, media_key: str, key: Optional[str] = None) -> None:
        """Remove media data or a specific key."""
        with self._lock:
            if key is None:
                if media_key in self._data:
                    del self._data[media_key]
                    self._dirty = True
            else:
                if media_key in self._data and key in self._data[media_key]:
                    del self._data[media_key][key]
                    # Remove empty media entry
                    if not self._data[media_key]:
                        del self._data[media_key]
                    self._dirty = True
            self._save_data()

    def get_all_keys(self) -> list[str]:
        """Get all media keys."""
        with self._lock:
            return list(self._data.keys())

    def get_data_size(self) -> int:
        """Get the total number of media entries."""
        with self._lock:
            return len(self._data)

    def cleanup_invalid_paths(self) -> int:
        """Remove data for non-existent files. Returns count of removed entries."""
        with self._lock:
            paths_to_remove = [
                key for key in self._data.keys()
                if not Path(key).exists()
            ]

            for key in paths_to_remove:
                del self._data[key]
                logger.debug(f"Removed data for non-existent file: {key}")

            if paths_to_remove:
                self._dirty = True
                self._save_data()
                logger.info(f"Cleaned up {len(paths_to_remove)} invalid file paths")

            return len(paths_to_remove)

    def force_save(self) -> None:
        """Force save data to disk (useful for shutdown)."""
        with self._lock:
            if self._dirty:
                self._save_data()


class PathValidator:
    """Validates file paths with caching for performance."""

    # Cache for path validation results
    _path_cache: Dict[str, bool] = {}
    _cache_max_size = 1000

    @classmethod
    def _clear_cache_if_needed(cls) -> None:
        """Clear cache if it gets too large."""
        if len(cls._path_cache) > cls._cache_max_size:
            cls._path_cache.clear()

    @classmethod
    def validate_image_path(cls, path_str: str) -> bool:
        """Validate that an image path exists and is a file."""
        cls._clear_cache_if_needed()

        if path_str in cls._path_cache:
            return cls._path_cache[path_str]

        try:
            path = Path(path_str)
            result = path.exists() and path.is_file()
            cls._path_cache[path_str] = result
            return result
        except Exception:
            cls._path_cache[path_str] = False
            return False

    @staticmethod
    def validate_string(value: Any) -> bool:
        """Validate that a value is a non-empty string."""
        return isinstance(value, str) and bool(value.strip())


class MediaPersistenceService:
    """Service for persisting user changes to media items with performance optimizations."""

    # Define data fields with validation and transformation
    DATA_FIELDS = {
        DataType.IMAGE_THUMBNAIL: DataField(
            key="image_thumbnail",
            validator=PathValidator.validate_image_path,
            transformer=lambda x: str(Path(x).absolute()) if x else None
        ),
        DataType.TITLE: DataField(
            key="title",
            validator=PathValidator.validate_string
        ),
        DataType.DESCRIPTION: DataField(
            key="description",
            validator=PathValidator.validate_string
        )
    }

    def __init__(self):
        self.data_manager = DataManager(get_data_dir() / "media_persistence.json")
        self._batch_updates: List[tuple] = []
        self._batch_mode = False

    @lru_cache(maxsize=1000)
    def _get_media_key(self, file_path: Path) -> str:
        """Generate a unique key for a media file with caching."""
        return str(file_path.absolute())

    def _get_field_config(self, data_type: DataType) -> DataField:
        """Get the field configuration for a data type."""
        return self.DATA_FIELDS[data_type]

    def _save_data(self, file_path: Path, data_type: DataType, value: Any) -> None:
        """Generic method to save data."""
        try:
            field_config = self._get_field_config(data_type)

            # Transform value if transformer exists
            transformed_value = field_config.transform(value)
            if transformed_value is None:
                return

            # Validate value if validator exists
            if not field_config.validate(transformed_value):
                logger.warning(f"Invalid value for {data_type.value}: {value}")
                return

            media_key = self._get_media_key(file_path)

            if self._batch_mode:
                self._batch_updates.append((media_key, field_config.key, transformed_value))
            else:
                self.data_manager.update_media_data(media_key, field_config.key, transformed_value)
                logger.debug(f"Saved {data_type.value} for {file_path}: {transformed_value}")
        except Exception as e:
            logger.warning(f"Error saving {data_type.value} for {file_path}: {e}")

    def _get_data(self, file_path: Path, data_type: DataType) -> Optional[Any]:
        """Generic method to get data."""
        try:
            field_config = self._get_field_config(data_type)
            media_key = self._get_media_key(file_path)
            media_data = self.data_manager.get_media_data(media_key)

            value = media_data.get(field_config.key)
            if value is None:
                return None

            # For image paths, return Path object
            if data_type == DataType.IMAGE_THUMBNAIL:
                return Path(value)

            return value
        except Exception as e:
            logger.warning(f"Error getting {data_type.value} for {file_path}: {e}")
            return None

    def _clear_data(self, file_path: Path, data_type: DataType) -> None:
        """Generic method to clear data."""
        try:
            field_config = self._get_field_config(data_type)
            media_key = self._get_media_key(file_path)
            self.data_manager.remove_media_data(media_key, field_config.key)
            logger.debug(f"Cleared {data_type.value} for {file_path}")
        except Exception as e:
            logger.warning(f"Error clearing {data_type.value} for {file_path}: {e}")

    # Batch operations for performance
    def start_batch_mode(self) -> None:
        """Start batch mode for multiple operations."""
        self._batch_mode = True
        self._batch_updates.clear()

    def commit_batch(self) -> None:
        """Commit all batched operations."""
        if self._batch_updates:
            self.data_manager.batch_update_media_data(self._batch_updates)
            logger.debug(f"Committed {len(self._batch_updates)} batch updates")
            self._batch_updates.clear()
        self._batch_mode = False

    def cancel_batch(self) -> None:
        """Cancel batch mode without committing."""
        self._batch_updates.clear()
        self._batch_mode = False

    # Public API methods - Image Thumbnail
    def save_image_thumbnail(self, file_path: Path, image_path: Path) -> None:
        """Save the image thumbnail path for a media file."""
        self._save_data(file_path, DataType.IMAGE_THUMBNAIL, image_path)

    def get_image_thumbnail(self, file_path: Path) -> Optional[Path]:
        """Get the saved image thumbnail path for a media file."""
        return self._get_data(file_path, DataType.IMAGE_THUMBNAIL)

    def clear_image_thumbnail(self, file_path: Path) -> None:
        """Clear the saved image thumbnail for a media file."""
        self._clear_data(file_path, DataType.IMAGE_THUMBNAIL)

    # Public API methods - Title
    def save_title(self, file_path: Path, title: str) -> None:
        """Save the custom title for a media file."""
        self._save_data(file_path, DataType.TITLE, title)

    def get_title(self, file_path: Path) -> Optional[str]:
        """Get the saved custom title for a media file."""
        return self._get_data(file_path, DataType.TITLE)

    def clear_title(self, file_path: Path) -> None:
        """Clear the saved title for a media file."""
        self._clear_data(file_path, DataType.TITLE)

    # Public API methods - Description
    def save_description(self, file_path: Path, description: str) -> None:
        """Save the custom description for a media file."""
        self._save_data(file_path, DataType.DESCRIPTION, description)

    def get_description(self, file_path: Path) -> Optional[str]:
        """Get the saved custom description for a media file."""
        return self._get_data(file_path, DataType.DESCRIPTION)

    def clear_description(self, file_path: Path) -> None:
        """Clear the saved description for a media file."""
        self._clear_data(file_path, DataType.DESCRIPTION)

    # Utility methods
    def get_all_persisted_data(self, file_path: Path) -> Dict[str, Any]:
        """Get all persisted data for a media file."""
        try:
            media_key = self._get_media_key(file_path)
            data = self.data_manager.get_media_data(media_key).copy()

            # Validate image thumbnail path
            if 'image_thumbnail' in data:
                if not PathValidator.validate_image_path(data['image_thumbnail']):
                    del data['image_thumbnail']
                    logger.debug(f"Removed invalid image thumbnail path: {data['image_thumbnail']}")

            return data
        except Exception as e:
            logger.warning(f"Error getting all persisted data for {file_path}: {e}")
            return {}

    def load_media_row_data(self, file_path: Path) -> Dict[str, Any]:
        """Load all persisted data for a media row."""
        try:
            media_key = self._get_media_key(file_path)
            data = self.data_manager.get_media_data(media_key).copy()
            result = {}

            # Load image thumbnail path
            if 'image_thumbnail' in data:
                image_path = Path(data['image_thumbnail'])
                if PathValidator.validate_image_path(str(image_path)):
                    result['image_path'] = str(image_path)

            # Load title and description
            for field in ['title', 'description']:
                if field in data and PathValidator.validate_string(data[field]):
                    result[field] = data[field]

            logger.debug(f"Loaded media row data for {file_path}: {result}")
            return result
        except Exception as e:
            logger.warning(f"Error loading media row data for {file_path}: {e}")
            return {}

    def clear_all_data(self, file_path: Path) -> None:
        """Clear all persisted data for a media file."""
        try:
            media_key = self._get_media_key(file_path)
            self.data_manager.remove_media_data(media_key)
            logger.debug(f"Cleared all persisted data for {file_path}")
        except Exception as e:
            logger.warning(f"Error clearing all data for {file_path}: {e}")

    def cleanup_invalid_paths(self) -> int:
        """Remove persisted data for files that no longer exist."""
        return self.data_manager.cleanup_invalid_paths()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the persistence data."""
        try:
            total_entries = self.data_manager.get_data_size()
            all_keys = self.data_manager.get_all_keys()

            # Count data types
            title_count = sum(
                1 for key in all_keys
                if 'title' in self.data_manager.get_media_data(key)
            )
            description_count = sum(
                1 for key in all_keys
                if 'description' in self.data_manager.get_media_data(key)
            )
            image_count = sum(
                1 for key in all_keys
                if 'image_thumbnail' in self.data_manager.get_media_data(key)
            )

            return {
                'total_entries': total_entries,
                'titles_saved': title_count,
                'descriptions_saved': description_count,
                'images_saved': image_count,
                'file_size_mb': self.data_manager.persistence_file.stat().st_size / (
                    1024 * 1024) if self.data_manager.persistence_file.exists() else 0}
        except Exception as e:
            logger.warning(f"Error getting statistics: {e}")
            return {}

    def shutdown(self) -> None:
        """Clean shutdown - commit any pending batch operations and force save."""
        if self._batch_mode:
            self.commit_batch()
        self.data_manager.force_save()
        # Clear caches
        self._get_media_key.cache_clear()
        PathValidator._path_cache.clear()
