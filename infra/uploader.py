# infra/uploader.py
import logging
from pathlib import Path
from typing import Callable, Optional, Tuple

from PySide6.QtCore import QMutex, QObject, QThread, Signal, Slot

from services.youtube_service import YouTubeService

from .events import UploadProgress

# Configure logging
logger = logging.getLogger(__name__)


class UploadWorker(QObject):
    progress = Signal(object)  # UploadProgress
    finished = Signal(bool, str)  # success, video_id_or_error
    started = Signal()

    def __init__(
        self,
        path: Path,
        title: str,
        description: str,
        service_factory: Callable[[], YouTubeService],
        scheduled_time: Optional[str] = None,
    ):
        super().__init__()
        self._path = path
        self._title = title
        self._description = description
        self._service_factory = service_factory
        self._scheduled_time = scheduled_time
        self._mutex = QMutex()
        self._cancelled = False

    @Slot()
    def run(self):
        """Main upload execution method."""
        self._mutex.lock()
        try:
            self.started.emit()
            logger.info(f"Starting upload for: {self._path.name}")

            svc = self._service_factory()

            def on_progress(pct: int, status: str, message: str = ""):
                """Progress callback that emits signals safely."""
                if self._cancelled:
                    return

                # Create detailed progress object
                progress_obj = UploadProgress(
                    percent=pct, status=status, message=message
                )
                self.progress.emit(progress_obj)
                logger.debug(f"Upload progress: {pct}% - {status} - {message}")

            try:
                video_id = svc.upload_media(
                    self._path,
                    self._title,
                    self._description,
                    on_progress,
                    self._scheduled_time,
                )

                if self._cancelled:
                    self.progress.emit(
                        UploadProgress(
                            percent=0,
                            status="Cancelled",
                            message="Upload was cancelled",
                        )
                    )
                    self.finished.emit(False, "Upload cancelled")
                    return

                if video_id is None:
                    error_msg = "Upload failed: No video ID returned"
                    logger.error(f"Upload failed for {self._path.name}: {error_msg}")
                    self.progress.emit(
                        UploadProgress(percent=0, status="Failed", message=error_msg)
                    )
                    self.finished.emit(False, error_msg)
                    return

                self.progress.emit(
                    UploadProgress(
                        percent=100,
                        status="Completed",
                        message="Upload completed successfully",
                    )
                )
                logger.info(f"Upload completed successfully: {video_id}")
                self.finished.emit(True, video_id)

            except Exception as e:
                error_msg = f"Upload failed: {str(e)}"
                logger.error(f"Upload error for {self._path.name}: {e}")
                self.progress.emit(
                    UploadProgress(percent=0, status="Failed", message=error_msg)
                )
                self.finished.emit(False, error_msg)

        finally:
            self._mutex.unlock()

    def cancel(self):
        """Cancel the upload."""
        self._cancelled = True


def start_upload(
    path: Path,
    title: str,
    description: str,
    service_factory: Callable[[], YouTubeService],
) -> Tuple[QThread, UploadWorker]:
    """
    Start an upload in a new QThread and return (thread, worker).

    Args:
        path: Path to the media file
        title: Video title
        description: Video description
        service_factory: Factory function to create YouTube service instance

    Returns:
        Tuple of (QThread, UploadWorker) - caller must keep thread alive until finished

    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if not path or not path.exists():
        raise ValueError(f"Invalid file path: {path}")

    if not title or not title.strip():
        raise ValueError("Title is required")

    if not description or not description.strip():
        raise ValueError("Description is required")

    if not service_factory:
        raise ValueError("Service factory is required")

    # Create thread and worker
    thread = QThread()
    worker = UploadWorker(path, title, description, service_factory)
    worker.moveToThread(thread)

    # Connect signals
    thread.started.connect(worker.run)

    # Clean shutdown & deletion
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # Start the thread
    thread.start()
    logger.info(f"Started upload thread for: {path.name}")

    return thread, worker


def cancel_upload(thread: QThread, worker: UploadWorker) -> bool:
    """
    Attempt to cancel an ongoing upload.

    Args:
        thread: The upload thread
        worker: The upload worker

    Returns:
        True if cancellation was initiated, False otherwise
    """
    try:
        if thread.isRunning():
            logger.info("Cancelling upload...")
            worker.cancel()
            thread.quit()
            thread.wait(5000)  # Wait up to 5 seconds
            return True
        return False
    except Exception as e:
        logger.error(f"Error cancelling upload: {e}")
        return False
