# core/history_manager.py
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.config import get_data_dir


class HistoryManager:
    """Lightweight persistence for tracking uploads and conversions."""

    def __init__(self):
        self.history_file = get_data_dir() / "history.json"
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """Load history from JSON file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            pass

        # Return default structure
        return {
            "uploads": [],
            "conversions": [],
            "last_updated": datetime.now().isoformat(),
        }

    def _save_history(self):
        """Save history to JSON file."""
        try:
            # Ensure data directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            # Update timestamp
            self.history["last_updated"] = datetime.now().isoformat()

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def add_upload(self, original_file: str, title: str, video_url: str, video_id: str):
        """Record a successful YouTube upload."""
        upload_record = {
            "type": "upload",
            "original_file": original_file,
            "title": title,
            "video_url": video_url,
            "video_id": video_id,
            "date": datetime.now().isoformat(),
            "status": "completed",
        }

        self.history["uploads"].append(upload_record)
        self._save_history()

    def add_conversion(
        self, mp3_file: str, mp4_file: str, image_file: Optional[str] = None
    ):
        """Record a successful MP3 to MP4 conversion."""
        conversion_record = {
            "type": "conversion",
            "mp3_file": mp3_file,
            "mp4_file": mp4_file,
            "image_file": image_file,
            "date": datetime.now().isoformat(),
            "status": "completed",
        }

        self.history["conversions"].append(conversion_record)
        self._save_history()

    def get_recent_uploads(self, limit: int = 10) -> List[Dict]:
        """Get recent uploads, sorted by date (newest first)."""
        uploads = self.history.get("uploads", [])
        # Sort by date (newest first) and limit results
        sorted_uploads = sorted(uploads, key=lambda x: x.get("date", ""), reverse=True)
        return sorted_uploads[:limit]

    def get_recent_conversions(self, limit: int = 10) -> List[Dict]:
        """Get recent conversions, sorted by date (newest first)."""
        conversions = self.history.get("conversions", [])
        # Sort by date (newest first) and limit results
        sorted_conversions = sorted(
            conversions, key=lambda x: x.get("date", ""), reverse=True
        )
        return sorted_conversions[:limit]

    def get_all_history(self, limit: int = 20) -> List[Dict]:
        """Get all history items (uploads + conversions) sorted by date."""
        all_items = []

        # Add uploads with type identifier
        for upload in self.history.get("uploads", []):
            upload["item_type"] = "upload"
            all_items.append(upload)

        # Add conversions with type identifier
        for conversion in self.history.get("conversions", []):
            conversion["item_type"] = "conversion"
            all_items.append(conversion)

        # Sort by date (newest first) and limit results
        sorted_items = sorted(all_items, key=lambda x: x.get("date", ""), reverse=True)
        return sorted_items[:limit]

    def clear_history(self):
        """Clear all history (useful for testing or cleanup)."""
        self.history = {
            "uploads": [],
            "conversions": [],
            "last_updated": datetime.now().isoformat(),
        }
        self._save_history()

    def get_stats(self) -> Dict:
        """Get basic statistics about the history."""
        uploads = self.history.get("uploads", [])
        conversions = self.history.get("conversions", [])

        return {
            "total_uploads": len(uploads),
            "total_conversions": len(conversions),
            "last_upload": uploads[-1]["date"] if uploads else None,
            "last_conversion": conversions[-1]["date"] if conversions else None,
            "last_updated": self.history.get("last_updated"),
        }
