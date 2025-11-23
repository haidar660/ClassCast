"""
Audio extraction module using ffmpeg-python.
Extracts mono WAV audio from video files.
"""
from pathlib import Path
import ffmpeg

import config
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def extract_audio_from_video(video_path: Path, output_audio_path: Path) -> Path:
    """
    Extract audio from video file and save as WAV.

    Args:
        video_path: Path to input video file
        output_audio_path: Path to save extracted audio

    Returns:
        Path to extracted audio file

    Raises:
        Exception: If audio extraction fails
    """
    logger.info(f"Extracting audio from: {video_path}")
    logger.info(f"Output audio will be saved to: {output_audio_path}")

    try:
        # Use ffmpeg to extract audio
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.output(
            stream,
            str(output_audio_path),
            acodec='pcm_s16le',  # 16-bit PCM
            ac=config.AUDIO_CHANNELS,  # mono
            ar=config.AUDIO_SAMPLE_RATE  # 16kHz
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        logger.info(f"Audio extraction successful: {output_audio_path}")
        return output_audio_path

    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error during audio extraction: {e.stderr.decode() if e.stderr else str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during audio extraction: {str(e)}")
        raise
