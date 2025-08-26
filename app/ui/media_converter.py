# app/ui/media_converter.py
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtWidgets import QMessageBox

# Import constants from core config
from core.config import SUPPORTED_EXTENSIONS

# Default overlay configurations
DEFAULT_WAVEFORM_CONFIG = {
    "color": "#00ff00",  # Green color
    "mode": "line",  # line, bar, point
    "scale": "sqrt",  # linear, sqrt, log
    "opacity": 0.7,  # 0.0 to 1.0
    "size": "1280x720",  # Waveform size
    "position": "center",  # top, bottom, center
}

DEFAULT_RAIN_CONFIG = {
    "density": 0.3,  # 0.0 to 1.0
    "speed": 1.0,  # Animation speed
    "color": "#ffffff",  # Rain color
    "opacity": 0.2,  # 0.0 to 1.0
    "direction": "vertical",  # vertical, diagonal
}


class ConversionError(Exception):
    """Raised when MP3 to MP4 conversion fails."""

    pass


class MediaConverter:
    """Handles MP3 to MP4 conversion with progress tracking and overlay effects."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback

    def convert_mp3_to_mp4_with_overlay(
        self,
        mp3_path: Path,
        image_path: Path = None,
        overlay_type: str = "none",
        overlay_config: Dict[str, Any] = None,
    ) -> Path:
        """Convert MP3 + image to MP4 with optional overlay effects."""

        if overlay_type == "waveform":
            if image_path:
                return self._convert_with_waveform(mp3_path, image_path, overlay_config)
            else:
                return self._convert_waveform_only(mp3_path, overlay_config)
        elif overlay_type == "rain":
            return self._convert_with_rain(mp3_path, image_path, overlay_config)
        elif overlay_type == "waveform_rain":
            return self._convert_with_waveform_and_rain(
                mp3_path, image_path, overlay_config
            )
        else:
            if image_path:
                return self.convert_mp3_to_mp4(mp3_path, image_path)  # Original method
            else:
                return self._convert_audio_only(mp3_path)  # Audio-only conversion

    def _convert_with_waveform(
        self, mp3_path: Path, image_path: Path, config: Dict[str, Any] = None
    ) -> Path:
        """Convert MP3 + image to MP4 with animated waveform overlay."""
        try:
            # Use default config if none provided
            if config is None:
                config = DEFAULT_WAVEFORM_CONFIG.copy()

            # Verify input files exist
            if not mp3_path.exists():
                raise ConversionError(f"MP3 file not found: {mp3_path}")
            if not image_path.exists():
                raise ConversionError(f"Image file not found: {image_path}")

            # Create output path
            output_path = mp3_path.with_suffix(".mp4")

            # Update progress - preparing waveform conversion
            self._update_progress(10, "Preparing waveform overlay...")

            # Build FFmpeg command with waveform filter
            waveform_cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(image_path),  # Background image
                "-i",
                str(mp3_path),  # Audio input
                "-filter_complex",
                f"[0:v]scale=trunc(iw/2)*2:trunc(ih/2)*2[scaled];[1:a]showwaves=s={
                    config['size']}:mode={
                    config['mode']}:colors={
                    config['color']}:scale={
                    config['scale']}:draw=full,format=yuv420p[waveform];[scaled][waveform]overlay=(W-w)/2:(H-h)/2:shortest=1",
                "-c:a",
                "aac",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

            # Update progress - starting waveform conversion
            self._update_progress(30, "Generating waveform visualization...")

            result = subprocess.run(waveform_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(
                    f"FFmpeg waveform conversion failed: {result.stderr}"
                )

            # Update progress - finalizing
            self._update_progress(90, "Finalizing waveform video...")

            # Verify the output file was created
            if not output_path.exists():
                raise ConversionError(f"Output file was not created: {output_path}")

            # Update progress - complete
            self._update_progress(100, "Waveform conversion complete!")

            return output_path

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to convert MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected waveform conversion error: {e}")

    def _convert_waveform_only(
        self, mp3_path: Path, config: Dict[str, Any] = None
    ) -> Path:
        """Convert MP3 to MP4 with waveform on black background."""
        try:
            # Use default config if none provided
            if config is None:
                config = DEFAULT_WAVEFORM_CONFIG.copy()

            # Verify input file exists
            if not mp3_path.exists():
                raise ConversionError(f"MP3 file not found: {mp3_path}")

            # Create output path
            output_path = mp3_path.with_suffix(".mp4")

            # Update progress - preparing waveform-only conversion
            self._update_progress(10, "Preparing waveform-only conversion...")

            # Build FFmpeg command with waveform on black background
            waveform_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(mp3_path),  # Audio input
                "-filter_complex",
                f"[0:a]showwaves=s={
                    config['size']}:mode={
                    config['mode']}:colors={
                    config['color']}:scale={
                    config['scale']}:draw=full,format=yuv420p",
                "-c:a",
                "aac",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

            # Update progress - starting waveform conversion
            self._update_progress(30, "Generating waveform visualization...")

            result = subprocess.run(waveform_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(
                    f"FFmpeg waveform conversion failed: {result.stderr}"
                )

            # Update progress - finalizing
            self._update_progress(90, "Finalizing waveform video...")

            # Verify the output file was created
            if not output_path.exists():
                raise ConversionError(f"Output file was not created: {output_path}")

            # Update progress - complete
            self._update_progress(100, "Waveform-only conversion complete!")

            return output_path

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to convert MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected waveform-only conversion error: {e}")

    def _convert_audio_only(self, mp3_path: Path) -> Path:
        """Convert MP3 to MP4 with black background (no image, no overlay)."""
        try:
            # Verify input file exists
            if not mp3_path.exists():
                raise ConversionError(f"MP3 file not found: {mp3_path}")

            # Create output path
            output_path = mp3_path.with_suffix(".mp4")

            # Update progress - preparing audio-only conversion
            self._update_progress(10, "Preparing audio-only conversion...")

            # Build FFmpeg command with black background
            audio_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(mp3_path),  # Audio input
                "-f",
                "lavfi",  # Use lavfi for generating video
                "-i",
                "color=black:size=1280x720",  # Black background
                "-c:a",
                "aac",
                "-c:v",
                "libx264",
                "-shortest",  # End when audio ends
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

            # Update progress - starting conversion
            self._update_progress(30, "Converting audio to video...")

            result = subprocess.run(audio_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(
                    f"FFmpeg audio-only conversion failed: {result.stderr}"
                )

            # Update progress - finalizing
            self._update_progress(90, "Finalizing video...")

            # Verify the output file was created
            if not output_path.exists():
                raise ConversionError(f"Output file was not created: {output_path}")

            # Update progress - complete
            self._update_progress(100, "Audio-only conversion complete!")

            return output_path

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to convert MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected audio-only conversion error: {e}")

    def _convert_with_rain(
        self, mp3_path: Path, image_path: Path, config: Dict[str, Any] = None
    ) -> Path:
        """Convert MP3 + image to MP4 with animated rain overlay."""
        try:
            # Use default config if none provided
            if config is None:
                config = DEFAULT_RAIN_CONFIG.copy()

            # Verify input files exist
            if not mp3_path.exists():
                raise ConversionError(f"MP3 file not found: {mp3_path}")
            if not image_path.exists():
                raise ConversionError(f"Image file not found: {image_path}")

            # Create output path
            output_path = mp3_path.with_suffix(".mp4")

            # Update progress - preparing rain effect
            self._update_progress(10, "Preparing rain effect overlay...")

            # Build FFmpeg command with rain effect filter
            rain_cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(image_path),  # Background image
                "-i",
                str(mp3_path),  # Audio input
                "-filter_complex",
                f"[0:v]scale=trunc(iw/2)*2:trunc(ih/2)*2,geq=r='if(gt(mod(Y,{int(20 /
                                                                                 config['density'])}),10),if(gt(mod(X,{int(10 /
                                                                                                                           config['density'])}),5),255,0),0)':g='if(gt(mod(Y,{int(20 /
                                                                                                                                                                                  config['density'])}),10),if(gt(mod(X,{int(10 /
                                                                                                                                                                                                                            config['density'])}),5),255,0),0)':b='if(gt(mod(Y,{int(20 /
                                                                                                                                                                                                                                                                                   config['density'])}),10),if(gt(mod(X,{int(10 /
                                                                                                                                                                                                                                                                                                                             config['density'])}),5),255,0),0)':a='if(gt(mod(Y,{int(20 /
                                                                                                                                                                                                                                                                                                                                                                                    config['density'])}),10),if(gt(mod(X,{int(10 /
                                                                                                                                                                                                                                                                                                                                                                                                                              config['density'])}),5),{config['opacity']},0),0)',format=yuva420p",
                "-c:a",
                "aac",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

            # Update progress - generating rain effect
            self._update_progress(30, "Generating rain effect...")

            result = subprocess.run(rain_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(
                    f"FFmpeg rain effect conversion failed: {result.stderr}"
                )

            # Update progress - finalizing
            self._update_progress(90, "Finalizing rain effect video...")

            # Verify the output file was created
            if not output_path.exists():
                raise ConversionError(f"Output file was not created: {output_path}")

            # Update progress - complete
            self._update_progress(100, "Rain effect conversion complete!")

            return output_path

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to convert MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected rain effect conversion error: {e}")

    def _convert_with_waveform_and_rain(
        self, mp3_path: Path, image_path: Path, config: Dict[str, Any] = None
    ) -> Path:
        """Convert MP3 + image to MP4 with both waveform and rain overlays."""
        try:
            # Use default configs if none provided
            if config is None:
                config = {
                    "waveform": DEFAULT_WAVEFORM_CONFIG.copy(),
                    "rain": DEFAULT_RAIN_CONFIG.copy(),
                }

            # Verify input files exist
            if not mp3_path.exists():
                raise ConversionError(f"MP3 file not found: {mp3_path}")
            if not image_path.exists():
                raise ConversionError(f"Image file not found: {image_path}")

            # Create output path
            output_path = mp3_path.with_suffix(".mp4")

            # Update progress - preparing combined effects
            self._update_progress(10, "Preparing waveform and rain effects...")

            # Build FFmpeg command with both effects
            combined_cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(image_path),  # Background image
                "-i",
                str(mp3_path),  # Audio input
                "-filter_complex",
                f"[0:v]scale=trunc(iw/2)*2:trunc(ih/2)*2[scaled];[1:a]showwaves=s={
                    config['waveform']['size']}:mode={
                    config['waveform']['mode']}:colors={
                    config['waveform']['color']}:scale={
                    config['waveform']['scale']}:draw=full,format=yuv420p[waveform];[scaled][waveform]overlay=shortest=1",
                "-c:a",
                "aac",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

            # Update progress - generating combined effects
            self._update_progress(30, "Generating waveform and rain effects...")

            result = subprocess.run(combined_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(
                    f"FFmpeg combined effects conversion failed: {result.stderr}"
                )

            # Update progress - finalizing
            self._update_progress(90, "Finalizing combined effects video...")

            # Verify the output file was created
            if not output_path.exists():
                raise ConversionError(f"Output file was not created: {output_path}")

            # Update progress - complete
            self._update_progress(100, "Combined effects conversion complete!")

            return output_path

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to convert MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected combined effects conversion error: {e}")

    def convert_mp3_to_mp4(self, mp3_path: Path, image_path: Path) -> Path:
        """Convert MP3 + image to MP4 using ffmpeg."""
        try:
            # Verify input files exist
            if not mp3_path.exists():
                raise ConversionError(f"MP3 file not found: {mp3_path}")
            if not image_path.exists():
                raise ConversionError(f"Image file not found: {image_path}")

            # Create output path (same name as MP3 but .mp4 extension)
            output_path = mp3_path.with_suffix(".mp4")

            # Update progress - getting duration
            self._update_progress(10, "Getting audio duration...")

            # Get MP3 duration
            duration_cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(mp3_path),
            ]

            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(f"Failed to get MP3 duration: {result.stderr}")

            duration = float(result.stdout.strip())

            # Update progress - starting conversion
            self._update_progress(20, "Starting video conversion...")

            # Convert MP3 + image to MP4
            convert_cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-loop",
                "1",  # Loop the image
                "-i",
                str(image_path),  # Input image
                "-i",
                str(mp3_path),  # Input audio
                "-c:v",
                "libx264",  # Video codec
                "-c:a",
                "aac",  # Audio codec
                "-shortest",  # End when shortest input ends
                "-pix_fmt",
                "yuv420p",  # Pixel format for compatibility
                str(output_path),  # Output file
            ]

            # Update progress - conversion in progress
            self._update_progress(50, "Converting audio to video...")

            result = subprocess.run(convert_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(f"FFmpeg conversion failed: {result.stderr}")

            # Update progress - finalizing
            self._update_progress(90, "Finalizing video...")

            # Verify the output file was created
            if not output_path.exists():
                raise ConversionError(f"Output file was not created: {output_path}")

            # Update progress - complete
            self._update_progress(100, "Conversion complete!")

            return output_path

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to convert MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except ValueError as e:
            raise ConversionError(f"Invalid duration value: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected conversion error: {e}")

    def merge_mp3s_to_mp4(self, mp3_paths: list[Path], image_path: Path) -> Path:
        """Merge multiple MP3 files into a single MP4 with the given image."""
        try:
            # Verify input files exist
            for mp3_path in mp3_paths:
                if not mp3_path.exists():
                    raise ConversionError(f"MP3 file not found: {mp3_path}")
            if not image_path.exists():
                raise ConversionError(f"Image file not found: {image_path}")

            # Create output path (use name of first MP3 but with _merged suffix)
            first_mp3 = mp3_paths[0]
            output_path = first_mp3.with_suffix("").with_name(
                f"{first_mp3.stem}_merged{".mp4"}"
            )

            # Update progress - preparing merge
            self._update_progress(
                10, f"Preparing to merge {len(mp3_paths)} MP3 files..."
            )

            # Create a temporary file list for ffmpeg
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                temp_file_list = Path(f.name)
                for mp3_path in mp3_paths:
                    f.write(f"file '{mp3_path.absolute()}'\n")

            try:
                # Update progress - merging audio
                self._update_progress(20, "Merging audio files...")

                # First, merge all MP3 files into a single audio file
                merged_audio_path = first_mp3.with_suffix("").with_name(
                    f"{first_mp3.stem}_merged_audio.mp3"
                )

                merge_audio_cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output file
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(temp_file_list),
                    "-c",
                    "copy",
                    str(merged_audio_path),
                ]

                result = subprocess.run(merge_audio_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ConversionError(
                        f"Failed to merge audio files: {result.stderr}"
                    )

                # Update progress - converting to video
                self._update_progress(50, "Converting merged audio to video...")

                # Convert merged audio + image to MP4
                convert_cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output file
                    "-loop",
                    "1",  # Loop the image
                    "-i",
                    str(image_path),  # Input image
                    "-i",
                    str(merged_audio_path),  # Input merged audio
                    "-c:v",
                    "libx264",  # Video codec
                    "-c:a",
                    "aac",  # Audio codec
                    "-shortest",  # End when shortest input ends
                    "-pix_fmt",
                    "yuv420p",  # Pixel format for compatibility
                    str(output_path),  # Output file
                ]

                result = subprocess.run(convert_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ConversionError(f"FFmpeg conversion failed: {result.stderr}")

                # Update progress - finalizing
                self._update_progress(90, "Finalizing merged video...")

                # Clean up temporary files
                if merged_audio_path.exists():
                    merged_audio_path.unlink()

                # Verify the output file was created
                if not output_path.exists():
                    raise ConversionError(f"Output file was not created: {output_path}")

                # Update progress - complete
                self._update_progress(100, "Merge and conversion complete!")

                return output_path

            finally:
                # Clean up temporary file list
                if temp_file_list.exists():
                    temp_file_list.unlink()

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to merge MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected merge error: {e}")

    def merge_mp3s_to_mp4_black(self, mp3_paths: list[Path]) -> Path:
        """Merge multiple MP3 files into a single MP4 with black background."""
        try:
            # Verify input files exist
            for mp3_path in mp3_paths:
                if not mp3_path.exists():
                    raise ConversionError(f"MP3 file not found: {mp3_path}")

            # Create output path (use name of first MP3 but with _merged suffix)
            first_mp3 = mp3_paths[0]
            output_path = first_mp3.with_suffix("").with_name(
                f"{first_mp3.stem}_merged{".mp4"}"
            )

            # Update progress - preparing merge
            self._update_progress(
                10,
                f"Preparing to merge {len(mp3_paths)} MP3 files with black background...",
            )

            # Create a temporary file list for ffmpeg
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                temp_file_list = Path(f.name)
                for mp3_path in mp3_paths:
                    f.write(f"file '{mp3_path.absolute()}'\n")

            try:
                # Update progress - merging audio
                self._update_progress(20, "Merging audio files...")

                # First, merge all MP3 files into a single audio file
                merged_audio_path = first_mp3.with_suffix("").with_name(
                    f"{first_mp3.stem}_merged_audio.mp3"
                )

                merge_audio_cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output file
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(temp_file_list),
                    "-c",
                    "copy",
                    str(merged_audio_path),
                ]

                result = subprocess.run(merge_audio_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ConversionError(
                        f"Failed to merge audio files: {result.stderr}"
                    )

                # Update progress - converting to video
                self._update_progress(
                    50, "Converting merged audio to video with black background..."
                )

                # Convert merged audio + black background to MP4
                convert_cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output file
                    "-i",
                    str(merged_audio_path),  # Input merged audio
                    "-f",
                    "lavfi",  # Use lavfi for generating video
                    "-i",
                    "color=black:size=1280x720",  # Black background
                    "-c:a",
                    "aac",  # Audio codec
                    "-c:v",
                    "libx264",  # Video codec
                    "-shortest",  # End when shortest input ends
                    "-pix_fmt",
                    "yuv420p",  # Pixel format for compatibility
                    str(output_path),  # Output file
                ]

                result = subprocess.run(convert_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ConversionError(f"FFmpeg conversion failed: {result.stderr}")

                # Update progress - finalizing
                self._update_progress(90, "Finalizing merged video...")

                # Clean up temporary files
                if merged_audio_path.exists():
                    merged_audio_path.unlink()

                # Verify the output file was created
                if not output_path.exists():
                    raise ConversionError(f"Output file was not created: {output_path}")

                # Update progress - complete
                self._update_progress(100, "Merge and conversion complete!")

                return output_path

            finally:
                # Clean up temporary file list
                if temp_file_list.exists():
                    temp_file_list.unlink()

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please install FFmpeg to merge MP3s."
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"FFmpeg process error: {e}")
        except OSError as e:
            raise ConversionError(f"File system error: {e}")
        except Exception as e:
            raise ConversionError(f"Unexpected merge error: {e}")

    def _update_progress(self, percent: int, message: str):
        """Update progress if callback is provided."""
        if self.progress_callback:
            self.progress_callback(percent, message)
