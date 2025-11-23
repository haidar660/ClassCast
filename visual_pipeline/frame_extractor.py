"""
Frame extraction module using OpenCV.
Extracts frames from video at regular intervals.
"""
from pathlib import Path
from typing import List, Dict
import cv2

import config
from utils.logging_utils import setup_logger
from utils.paths import get_frame_path

logger = setup_logger(__name__)


def extract_frames(video_path: Path, prefix: str) -> List[Dict]:
    """
    Extract frames from video at specified intervals.

    Args:
        video_path: Path to input video file
        prefix: Prefix for naming frames and organizing output

    Returns:
        List of frame metadata:
        [
            {
                "frame_id": str,
                "timestamp": float (seconds),
                "path": str
            },
            ...
        ]

    Raises:
        Exception: If frame extraction fails
    """
    logger.info(f"Extracting frames from video: {video_path}")
    logger.info(f"Frame interval: {config.FRAME_INTERVAL_SECONDS} seconds")

    try:
        # Open video file
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise Exception(f"Could not open video file: {video_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        logger.info(f"Video FPS: {fps}")
        logger.info(f"Total frames: {total_frames}")
        logger.info(f"Duration: {duration:.2f} seconds")

        # Calculate frame interval in frame numbers
        frame_interval = int(fps * config.FRAME_INTERVAL_SECONDS)

        if frame_interval < 1:
            frame_interval = 1

        frames_metadata = []
        frame_count = 0
        extracted_count = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            # Extract frame at intervals
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frame_id = f"frame_{extracted_count:04d}"

                # Get output path
                frame_path = get_frame_path(prefix, frame_id)

                # Save frame with high quality for better OCR
                # JPEG quality parameter: 0-100 (higher is better)
                quality = getattr(config, 'FRAME_QUALITY', 95)
                cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

                # Store metadata
                frames_metadata.append({
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "path": str(frame_path)
                })

                extracted_count += 1

                if extracted_count % 10 == 0:
                    logger.debug(f"Extracted {extracted_count} frames...")

            frame_count += 1

        cap.release()

        logger.info(f"Frame extraction complete. Total frames extracted: {len(frames_metadata)}")
        return frames_metadata

    except Exception as e:
        logger.error(f"Error during frame extraction: {str(e)}")
        raise
