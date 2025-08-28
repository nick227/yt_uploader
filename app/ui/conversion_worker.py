"""
Conversion worker for handling MP3 to MP4 conversions in background threads.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal

from .media_converter import MediaConverter, ConversionError

logger = logging.getLogger(__name__)


class ConversionWorker(QObject):
    """Worker for handling MP3 to MP4 conversions in background threads."""
    
    # Signals
    progress_updated = Signal(int, str)  # percent, message
    conversion_finished = Signal(Path)  # output_path
    conversion_failed = Signal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        self.media_converter = MediaConverter(progress_callback=self._update_progress)
        self._is_running = False
        
    def _update_progress(self, percent: int, message: str):
        """Update progress and emit signal."""
        if self._is_running:
            self.progress_updated.emit(percent, message)
    
    def convert_single_mp3(
        self, 
        mp3_path: Path, 
        image_path: Optional[Path] = None,
        overlay_type: str = "none",
        overlay_config: Optional[Dict[str, Any]] = None
    ):
        """Convert a single MP3 to MP4."""
        self._is_running = True
        
        try:
            logger.info(f"Starting conversion: {mp3_path}")
            
            if overlay_type != "none":
                output_path = self.media_converter.convert_mp3_to_mp4_with_overlay(
                    mp3_path, image_path, overlay_type, overlay_config
                )
            else:
                if image_path:
                    output_path = self.media_converter.convert_mp3_to_mp4(mp3_path, image_path)
                else:
                    output_path = self.media_converter.convert_mp3_to_mp4_with_overlay(
                        mp3_path, None, "none"
                    )
            
            if output_path and output_path.exists():
                logger.info(f"Conversion successful: {output_path}")
                self.conversion_finished.emit(output_path)
            else:
                error_msg = "Conversion failed - output file not created"
                logger.error(error_msg)
                self.conversion_failed.emit(error_msg)
                
        except ConversionError as e:
            error_msg = f"Conversion failed: {e}"
            logger.error(error_msg)
            self.conversion_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected conversion error: {e}"
            logger.error(error_msg)
            self.conversion_failed.emit(error_msg)
        finally:
            self._is_running = False
    
    def merge_mp3s(
        self, 
        mp3_paths: list[Path], 
        image_path: Optional[Path] = None
    ):
        """Merge multiple MP3 files into a single MP4."""
        self._is_running = True
        
        try:
            logger.info(f"Starting merge of {len(mp3_paths)} MP3 files")
            
            if image_path:
                output_path = self.media_converter.merge_mp3s_to_mp4(mp3_paths, image_path)
            else:
                output_path = self.media_converter.merge_mp3s_to_mp4_black(mp3_paths)
            
            if output_path and output_path.exists():
                logger.info(f"Merge successful: {output_path}")
                self.conversion_finished.emit(output_path)
            else:
                error_msg = "Merge failed - output file not created"
                logger.error(error_msg)
                self.conversion_failed.emit(error_msg)
                
        except ConversionError as e:
            error_msg = f"Merge failed: {e}"
            logger.error(error_msg)
            self.conversion_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected merge error: {e}"
            logger.error(error_msg)
            self.conversion_failed.emit(error_msg)
        finally:
            self._is_running = False
    
    def cancel(self):
        """Cancel the current conversion."""
        self._is_running = False
        logger.info("Conversion cancelled by user")
