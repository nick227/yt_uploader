"""
Centralized upload manager that integrates authentication and YouTube uploads.

Simplifies the upload process and provides a clean interface for the UI.
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QMutex, QObject, QThread, Signal

from .auth_manager import GoogleAuthManager
from .file_organizer import FileOrganizer
from services.youtube_service import YouTubeService
from infra.uploader import UploadWorker

# Note: UploadWorker is imported from infra.uploader when needed

logger = logging.getLogger(__name__)


@dataclass
class UploadRequest:
    """Represents an upload request with all necessary data."""

    path: Path
    title: str
    description: str
    request_id: str
    scheduled_time: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class UploadResult:
    """Represents the result of an upload operation."""

    request_id: str
    success: bool
    video_id: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: datetime = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now()


class UploadManager(QObject):
    """Centralized manager for YouTube uploads with authentication integration."""

    # Signals
    upload_started = Signal(str)  # request_id
    upload_progress = Signal(str, int, str, str)  # request_id, percent, status, message
    upload_completed = Signal(str, bool, str)  # request_id, success, video_id_or_error
    batch_progress = Signal(int, int, int)  # total, completed, failed
    batch_completed = Signal(int, int)  # total_completed, total_failed

    def __init__(self, auth_manager: GoogleAuthManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.file_organizer = None  # Defer initialization
        self._active_uploads: Dict[str, UploadRequest] = {}
        self._upload_threads: Dict[str, QThread] = {}
        self._upload_workers: Dict[str, UploadWorker] = {}
        self._mutex = QMutex()

        # Batch tracking
        self._batch_requests: List[str] = []
        self._batch_completed = 0
        self._batch_failed = 0

    def is_ready(self) -> bool:
        """Check if the upload manager is ready to handle uploads."""
        return self.auth_manager.is_authenticated()

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        return self.auth_manager.get_auth_info()

    def validate_upload_request(
        self, path: Path, title: str, description: str
    ) -> tuple[bool, str]:
        """Validate an upload request before starting."""
        # Check authentication
        if not self.is_ready():
            return False, "Not authenticated with Google"

        # Check file
        if not path.exists():
            return False, "File does not exist"

        if not path.is_file():
            return False, "Path is not a file"

        # Check metadata
        if not title or not title.strip():
            return False, "Title is required"

        if len(title) > 100:
            return False, "Title too long (max 100 characters)"

        if not description or not description.strip():
            return False, "Description is required"

        if len(description) > 5000:
            return False, "Description too long (max 5000 characters)"

        return True, ""

    def start_upload(
        self,
        path: Path,
        title: str,
        description: str,
        scheduled_time: Optional[str] = None,
    ) -> str:
        """Start a single upload and return the request ID."""
        # Validate request
        is_valid, error_msg = self.validate_upload_request(path, title, description)
        if not is_valid:
            raise ValueError(error_msg)

        # Create request
        request_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        request = UploadRequest(
            path=path,
            title=title.strip(),
            description=description.strip(),
            request_id=request_id,
            scheduled_time=scheduled_time,
        )

        # Store request
        self._mutex.lock()
        try:
            self._active_uploads[request_id] = request
        finally:
            self._mutex.unlock()

        # Start upload in background thread
        self._start_upload_thread(request)

        logger.info(f"Started upload {request_id} for {path.name}")
        return request_id

    def start_batch_upload(self, uploads: List[tuple[Path, str, str]]) -> List[str]:
        """Start multiple uploads and return request IDs."""
        request_ids = []

        # Validate all requests first
        for path, title, description in uploads:
            is_valid, error_msg = self.validate_upload_request(path, title, description)
            if not is_valid:
                raise ValueError(f"Invalid upload request for {path.name}: {error_msg}")

        # Reset batch tracking
        self._batch_requests = []
        self._batch_completed = 0
        self._batch_failed = 0

        # Start all uploads
        for path, title, description in uploads:
            request_id = self.start_upload(path, title, description)
            request_ids.append(request_id)
            self._batch_requests.append(request_id)

        logger.info(f"Started batch upload with {len(request_ids)} files")
        return request_ids

    def cancel_upload(self, request_id: str) -> bool:
        """Cancel a specific upload."""
        self._mutex.lock()
        try:
            if request_id in self._upload_workers:
                worker = self._upload_workers[request_id]
                worker.cancel()
                logger.info(f"Cancelled upload {request_id}")
                return True
            return False
        finally:
            self._mutex.unlock()

    def cancel_all_uploads(self):
        """Cancel all active uploads."""
        self._mutex.lock()
        try:
            for worker in self._upload_workers.values():
                worker.cancel()
            logger.info("Cancelled all active uploads")
        finally:
            self._mutex.unlock()

    def get_upload_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific upload."""
        self._mutex.lock()
        try:
            if request_id in self._active_uploads:
                request = self._active_uploads[request_id]
                return {
                    "request_id": request_id,
                    "path": str(request.path),
                    "title": request.title,
                    "created_at": request.created_at.isoformat(),
                    "is_active": request_id in self._upload_workers,
                }
            return None
        finally:
            self._mutex.unlock()

    def get_active_uploads(self) -> List[str]:
        """Get list of active upload request IDs."""
        self._mutex.lock()
        try:
            return list(self._active_uploads.keys())
        finally:
            self._mutex.unlock()

    def _start_upload_thread(self, request: UploadRequest):
        """Start upload in a background thread."""

        # Create service factory
        def service_factory():
            return YouTubeService(auth_manager=self.auth_manager)

        # Create worker and thread
        worker = UploadWorker(
            request.path,
            request.title,
            request.description,
            service_factory,
            request.scheduled_time,
        )

        thread = QThread()
        worker.moveToThread(thread)

        # Connect signals
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Ensure proper cleanup to prevent "QThread: Destroyed while thread is still running"
        thread.finished.connect(lambda: self._cleanup_thread(request.request_id))

        # Connect progress signals
        worker.started.connect(lambda: self._on_upload_started(request.request_id))
        worker.progress.connect(
            lambda progress: self._on_upload_progress(request.request_id, progress)
        )
        worker.finished.connect(
            lambda success, info: self._on_upload_finished(
                request.request_id, success, info
            )
        )

        # Store references
        self._mutex.lock()
        try:
            self._upload_threads[request.request_id] = thread
            self._upload_workers[request.request_id] = worker
        finally:
            self._mutex.unlock()

        # Start thread
        thread.start()

    def _on_upload_started(self, request_id: str):
        """Handle upload started event."""
        self.upload_started.emit(request_id)
        logger.debug(f"Upload {request_id} started")

    def _on_upload_progress(self, request_id: str, progress):
        """Handle upload progress event."""
        self.upload_progress.emit(
            request_id, progress.percent, progress.status, progress.message
        )

    def _on_upload_finished(self, request_id: str, success: bool, info: str):
        """Handle upload finished event."""
        # Create result
        result = UploadResult(
            request_id=request_id,
            success=success,
            video_id=info if success else None,
            error_message=info if not success else None,
        )

        # Clean up references (thread cleanup is handled separately)
        self._mutex.lock()
        try:
            self._active_uploads.pop(request_id, None)
            self._upload_workers.pop(request_id, None)
        finally:
            self._mutex.unlock()

        # Update batch tracking
        if request_id in self._batch_requests:
            if success:
                self._batch_completed += 1
            else:
                self._batch_failed += 1

            # Emit batch progress
            total_batch = len(self._batch_requests)
            self.batch_progress.emit(
                total_batch, self._batch_completed, self._batch_failed
            )

            # Check if batch is complete
            if self._batch_completed + self._batch_failed == total_batch:
                self.batch_completed.emit(self._batch_completed, self._batch_failed)
                self._batch_requests.clear()
                self._batch_completed = 0
                self._batch_failed = 0

        # Emit completion signal
        self.upload_completed.emit(request_id, success, info)

        logger.info(
            f"Upload {request_id} {'completed' if success else 'failed'}: {info}"
        )

    def _cleanup_thread(self, request_id: str):
        """Clean up thread references after thread finishes."""
        self._mutex.lock()
        try:
            self._upload_threads.pop(request_id, None)
        finally:
            self._mutex.unlock()

    def cleanup(self):
        """Clean up all resources."""
        self.cancel_all_uploads()

        # Wait for threads to finish
        self._mutex.lock()
        try:
            threads_to_wait = list(self._upload_threads.values())
        finally:
            self._mutex.unlock()

        for thread in threads_to_wait:
            if thread.isRunning():
                thread.wait(5000)  # Wait up to 5 seconds

        # Clear all references
        self._mutex.lock()
        try:
            self._active_uploads.clear()
            self._upload_threads.clear()
            self._upload_workers.clear()
            self._batch_requests.clear()
            self._batch_completed = 0
            self._batch_failed = 0
        finally:
            self._mutex.unlock()

        logger.info("Upload manager cleanup completed")

    def organize_uploaded_file(
        self, file_path: Path, upload_date: Optional[datetime] = None
    ) -> tuple[bool, str]:
        """
        Organize an uploaded file by moving it to the uploaded folder structure.

        Args:
            file_path: Path to the uploaded file
            upload_date: Date of upload (defaults to current date)

        Returns:
            (success: bool, message: str)
        """
        try:
            return self._get_file_organizer().organize_uploaded_file(
                file_path, upload_date
            )
        except Exception as e:
            logger.error(f"Error organizing uploaded file {file_path}: {e}")
            return False, f"Error organizing file: {str(e)}"

    def get_organization_stats(self) -> dict:
        """Get statistics about organized files."""
        return self._get_file_organizer().get_organization_stats()
