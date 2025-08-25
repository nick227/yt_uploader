from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UploadStatus(Enum):
    """Enum for upload status types."""

    QUEUED = "queued"
    AUTHENTICATING = "authenticating"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def is_final(cls, status: str) -> bool:
        """Check if status is final (completed, failed, cancelled)."""
        return status in [cls.COMPLETED.value, cls.FAILED.value, cls.CANCELLED.value]

    @classmethod
    def is_success(cls, status: str) -> bool:
        """Check if status indicates success."""
        return status == cls.COMPLETED.value

    @classmethod
    def is_error(cls, status: str) -> bool:
        """Check if status indicates error."""
        return status in [cls.FAILED.value, cls.CANCELLED.value]

    @classmethod
    def icon(cls, status: str) -> str:
        """Get icon for status."""
        icons = {
            cls.QUEUED.value: "⏳",
            cls.AUTHENTICATING.value: "🔐",
            cls.UPLOADING.value: "📤",
            cls.PROCESSING.value: "⚙️",
            cls.FINALIZING.value: "🎯",
            cls.COMPLETED.value: "✅",
            cls.FAILED.value: "❌",
            cls.CANCELLED.value: "🚫",
        }
        return icons.get(status, "❓")

    @classmethod
    def color(cls, status: str) -> str:
        """Get color for status."""
        colors = {
            cls.QUEUED.value: "orange",
            cls.AUTHENTICATING.value: "blue",
            cls.UPLOADING.value: "blue",  # Changed from green to blue to match test
            cls.PROCESSING.value: "purple",
            cls.FINALIZING.value: "yellow",
            cls.COMPLETED.value: "green",
            cls.FAILED.value: "red",
            cls.CANCELLED.value: "gray",
        }
        return colors.get(status, "gray")


@dataclass(frozen=True)
class UploadProgress:
    percent: int  # 0-100
    status: str  # Status message
    message: str = ""
    details: Optional[str] = ""  # Additional details for complex operations
    eta_seconds: Optional[int] = 0  # Estimated time remaining
    speed_mbps: Optional[float] = 0.0  # Upload speed in MB/s

    @property
    def is_complete(self) -> bool:
        """Check if upload is complete."""
        return self.percent == 100 and self.status in ["completed", "finalized"]

    @property
    def is_failed(self) -> bool:
        """Check if upload failed."""
        return self.status in ["failed", "cancelled"]

    @property
    def eta_formatted(self) -> str:
        """Get formatted ETA string."""
        if not self.eta_seconds:
            return "Unknown"

        if self.eta_seconds < 60:
            return f"{self.eta_seconds}s"
        elif self.eta_seconds < 3600:
            minutes = self.eta_seconds // 60
            seconds = self.eta_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = self.eta_seconds // 3600
            minutes = (self.eta_seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    @property
    def speed_formatted(self) -> str:
        """Get formatted speed string."""
        if not self.speed_mbps:
            return "Unknown"

        if self.speed_mbps < 1:
            return f"{self.speed_mbps * 1024:.1f} KB/s"
        else:
            return f"{self.speed_mbps:.1f} MB/s"

    def __str__(self) -> str:
        """String representation with percentage and message."""
        if self.message:
            return f"{self.percent}% - {self.status} - {self.message}"
        return f"{self.percent}% - {self.status}"
