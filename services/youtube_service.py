import logging
import math
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from core.auth_manager import AuthError, GoogleAuthManager

logger = logging.getLogger(__name__)

ProgressCb = Callable[[int, str, str], None]


class YouTubeService:
    """Enhanced YouTube service with real API integration and authentication."""

    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth_manager = auth_manager or GoogleAuthManager()
        self.file_size_mb = 0
        self.start_time = 0
        self.youtube = None
        self._auth_checked = False  # Cache authentication status

    def _ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication."""
        # Only check authentication once per service instance to prevent spam
        if self._auth_checked and self.youtube:
            return True

        if not self.auth_manager.is_authenticated():
            logger.error("Not authenticated with Google")
            return False

        if not self.youtube:
            try:
                credentials = self.auth_manager.get_credentials()
                if not credentials:
                    logger.error("No valid credentials available")
                    return False

                from googleapiclient.discovery import build

                self.youtube = build("youtube", "v3", credentials=credentials)
                logger.info("YouTube API client initialized")
                self._auth_checked = True  # Mark as checked
            except AuthError as e:
                logger.error(f"Authentication error: {e}")
                return False
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API client: {e}")
                return False

        return True

    def _calculate_speed_and_eta(
        self, uploaded_mb: float, elapsed_seconds: float
    ) -> tuple[float, int]:
        """Calculate upload speed and ETA."""
        if elapsed_seconds <= 0:
            return 0.0, 0

        speed_mbps = uploaded_mb / elapsed_seconds
        remaining_mb = self.file_size_mb - uploaded_mb
        eta_seconds = int(remaining_mb / speed_mbps) if speed_mbps > 0 else 0

        return speed_mbps, eta_seconds

    def _format_time(self, seconds: int) -> str:
        """Format seconds into human-readable time."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def _format_speed(self, speed_mbps: float) -> str:
        """Format speed into human-readable format."""
        if speed_mbps < 1:
            return f"{speed_mbps * 1024:.1f} KB/s"
        else:
            return f"{speed_mbps:.1f} MB/s"

    def _validate_file(self, path: Path) -> bool:
        """Validate the file before upload."""
        try:
            if not path.exists():
                logger.error(f"File does not exist: {path}")
                return False

            if not path.is_file():
                logger.error(f"Path is not a file: {path}")
                return False

            # Check file size (YouTube has limits)
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 128 * 1024:  # 128GB limit
                logger.error(f"File too large: {file_size_mb:.1f}MB (max 128GB)")
                return False

            # Check file extension
            valid_extensions = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"}
            if path.suffix.lower() not in valid_extensions:
                logger.warning(f"Unsupported file format: {path.suffix}")
                return False

            return True

        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False

    def _validate_metadata(self, title: str, description: str) -> tuple[bool, str]:
        """Validate upload metadata."""
        if not title or not title.strip():
            return False, "Title is required"

        if len(title) > 100:
            return False, "Title too long (max 100 characters)"

        if not description or not description.strip():
            return False, "Description is required"

        if len(description) > 5000:
            return False, "Description too long (max 5000 characters)"

        return True, ""

    def upload_media(
        self,
        path: Path,
        title: str,
        description: str,
        on_progress: ProgressCb,
        scheduled_time: Optional[str] = None,
    ) -> Optional[str]:
        """Upload media with enhanced progress feedback and real API integration."""
        # Validate file and metadata first
        if not self._validate_file(path):
            on_progress(0, "Failed", "Invalid file")
            return None

        is_valid, error_msg = self._validate_metadata(title, description)
        if not is_valid:
            on_progress(0, "Failed", error_msg)
            return None

        # Ensure authentication
        if not self._ensure_authenticated():
            on_progress(0, "Failed", "Authentication required")
            return None

        # Calculate file size
        self.file_size_mb = path.stat().st_size / (1024 * 1024)
        self.start_time = time.time()

        try:
            # Step 1: Queued
            on_progress(0, "Queued", "Preparing upload...")

            # Step 2: Authenticating (already done, but show for consistency)
            on_progress(5, "Authenticating", "Verifying credentials...")
            time.sleep(0.5)

            # Step 3: Uploading with real API
            on_progress(10, "Uploading", "Starting upload...")

            # Create media upload object with optimized settings
            media = MediaFileUpload(
                str(path),
                resumable=True,
                chunksize=1024 * 1024,  # 1MB chunks
                mimetype="video/mp4",  # Default mimetype
            )

            # Prepare request body
            request_body = {
                "snippet": {
                    "title": title.strip(),
                    "description": description.strip(),
                    "tags": [],
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "private",  # Start as private for safety
                    "selfDeclaredMadeForKids": False,
                },
            }

            # Add scheduling if provided
            if scheduled_time:
                # Validate scheduled_time format (should be ISO format with Z suffix)
                if not scheduled_time.endswith("Z") or "T" not in scheduled_time:
                    logger.warning(f"Invalid scheduled_time format: {scheduled_time}")
                    on_progress(0, "Failed", "Invalid scheduled time format")
                    return None

                request_body["status"]["publishAt"] = scheduled_time
                logger.info(f"Scheduling video for publication at: {scheduled_time}")

            # Create upload request
            request = self.youtube.videos().insert(
                part="snippet,status", body=request_body, media_body=media
            )

            # Execute upload with progress tracking
            response = None
            upload_start_time = time.time()
            last_progress_update = 0

            while response is None:
                try:
                    status, response = request.next_chunk()

                    if status:
                        # Calculate progress
                        progress_percent = min(90, int(status.progress() * 100))
                        elapsed = time.time() - upload_start_time

                        # Calculate upload metrics
                        uploaded_bytes = status.resumable_progress
                        uploaded_mb = uploaded_bytes / (1024 * 1024)
                        speed_mbps, eta_seconds = self._calculate_speed_and_eta(
                            uploaded_mb, elapsed
                        )

                        # Only update progress if it changed significantly or every 2 seconds
                        current_time = time.time()
                        if (
                            progress_percent != last_progress_update
                            or current_time - last_progress_update > 2
                        ):

                            speed_str = self._format_speed(speed_mbps)
                            eta_str = self._format_time(eta_seconds)

                            progress_message = (
                                f"{uploaded_mb:.1f}MB / {self.file_size_mb:.1f}MB • "
                                f"{speed_str} • {eta_str} remaining"
                            )

                            on_progress(
                                progress_percent,
                                "Uploading",
                                progress_message,
                            )
                            last_progress_update = progress_percent

                        # Small delay for UI responsiveness
                        time.sleep(0.1)

                except HttpError as e:
                    error_details = (
                        e.error_details if hasattr(e, "error_details") else str(e)
                    )
                    logger.error(f"YouTube API error: {error_details}")

                    # Handle specific error cases
                    if e.resp.status == 403:
                        on_progress(
                            0,
                            "Failed",
                            "Access denied - check YouTube API quota and permissions",
                        )
                    elif e.resp.status == 400:
                        on_progress(
                            0,
                            "Failed",
                            "Invalid request - check file format and metadata",
                        )
                    elif e.resp.status == 413:
                        on_progress(0, "Failed", "File too large for upload")
                    else:
                        on_progress(0, "Failed", f"YouTube API error: {error_details}")
                    return None

                except Exception as e:
                    logger.error(f"Upload error: {e}")
                    on_progress(0, "Failed", f"Upload failed: {str(e)}")
                    return None

            # Step 4: Processing
            on_progress(95, "Processing", "YouTube is processing your video...")
            time.sleep(1.0)

            # Step 5: Finalizing
            on_progress(98, "Finalizing", "Finalizing upload...")
            time.sleep(0.5)

            # Step 6: Completed
            on_progress(100, "Completed", "Upload successful!")

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Success logging
            if scheduled_time:
                print("✅ Upload scheduled successfully!")
                print(f"📺 Video ID: {video_id}")
                print(f"🔗 URL: {video_url}")
                print(f"📅 Scheduled for: {scheduled_time}")

                logger.info(f"Video uploaded and scheduled: {video_id}")
            else:
                print("✅ Upload successful!")
                print(f"📺 Video ID: {video_id}")
                print(f"🔗 URL: {video_url}")

                logger.info(f"Video uploaded: {video_id}")

            return video_id

        except HttpError as e:
            error_details = e.error_details if hasattr(e, "error_details") else str(e)
            logger.error(f"YouTube API error: {error_details}")
            on_progress(0, "Failed", f"YouTube API error: {error_details}")
            return None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            on_progress(0, "Failed", f"Upload failed: {str(e)}")
            return None

    def get_upload_quota(self) -> Optional[Dict[str, Any]]:
        """Get YouTube API quota information."""
        try:
            if not self._ensure_authenticated():
                return None

            # Get quota information from YouTube API
            with self.auth_manager.get_authenticated_service(
                "youtube", "v3"
            ) as service:
                # Note: YouTube API doesn't provide direct quota info
                # This is a placeholder for future implementation
                return {
                    "quota_used": "Unknown",
                    "quota_limit": "Unknown",
                    "quota_remaining": "Unknown",
                }

        except Exception as e:
            logger.error(f"Failed to get quota info: {e}")
            return None
