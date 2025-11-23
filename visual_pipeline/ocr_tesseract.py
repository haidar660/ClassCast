"""
OCR module using Tesseract OCR.
Performs optical character recognition on extracted frames.
Tesseract is optimized for document/screen text.
"""
from pathlib import Path
from typing import List, Dict
import pytesseract
from PIL import Image
import cv2
import numpy as np

import config
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)

# Set Tesseract path (Windows default installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_for_tesseract(image_path: Path) -> np.ndarray:
    """
    Preprocess image for Tesseract OCR.

    For screen recordings, minimal preprocessing with upscaling works best.

    Args:
        image_path: Path to image file

    Returns:
        Preprocessed image as numpy array
    """
    # Read image
    img = cv2.imread(str(image_path))

    if img is None:
        logger.warning(f"Could not read image: {image_path}")
        return None

    # Get upscaling factor
    upscale_factor = getattr(config, 'OCR_UPSCALE_FACTOR', 2.0)

    # Upscale image for better OCR (larger text = better recognition)
    if upscale_factor > 1.0:
        new_width = int(img.shape[1] * upscale_factor)
        new_height = int(img.shape[0] * upscale_factor)
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Check configuration
    use_preprocessing = getattr(config, 'OCR_USE_PREPROCESSING', False)
    use_threshold = getattr(config, 'OCR_USE_THRESHOLD', False)

    if not use_preprocessing and not use_threshold:
        # No preprocessing - just grayscale (RECOMMENDED for screen recordings)
        return gray

    if use_preprocessing:
        # Apply slight denoising
        gray = cv2.fastNlMeansDenoising(gray, h=10)

    if use_threshold:
        # Apply binary threshold
        # WARNING: This can turn UI icons into gibberish!
        _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return gray


def perform_ocr_on_frame(frame_path: Path) -> str:
    """
    Perform OCR on a single frame image using Tesseract.

    Args:
        frame_path: Path to frame image

    Returns:
        Detected text as a single string
    """
    try:
        # Always preprocess (at minimum for upscaling)
        preprocessed = preprocess_for_tesseract(frame_path)
        if preprocessed is None:
            logger.warning(f"Preprocessing failed for {frame_path}, using original")
            image = Image.open(frame_path)
        else:
            # Convert numpy array to PIL Image
            image = Image.fromarray(preprocessed)

        # Tesseract configuration
        # --psm 11: Sparse text. Find as much text as possible in no particular order (BEST for UI)
        # --psm 3: Fully automatic page segmentation (default)
        # --psm 6: Assume a single uniform block of text
        # --oem 3: Use LSTM OCR engine (best accuracy)
        custom_config = r'--oem 3 --psm 11'

        # Perform OCR
        text = pytesseract.image_to_string(image, config=custom_config)

        # Clean up text
        text = text.strip()

        # Replace multiple spaces/newlines with single space
        text = ' '.join(text.split())

        if text:
            logger.debug(f"OCR detected {len(text)} characters")

        return text

    except Exception as e:
        logger.warning(f"OCR failed for {frame_path}: {str(e)}")
        return ""


def perform_ocr_on_frames(frames_metadata: List[Dict]) -> List[Dict]:
    """
    Perform OCR on all extracted frames using Tesseract.

    Args:
        frames_metadata: List of frame metadata from frame_extractor

    Returns:
        List of OCR results:
        [
            {
                "frame_id": str,
                "timestamp": float (seconds),
                "path": str,
                "text": str
            },
            ...
        ]
    """
    logger.info(f"Performing OCR on {len(frames_metadata)} frames...")
    logger.info("Using Tesseract OCR engine")

    ocr_results = []

    for idx, frame_meta in enumerate(frames_metadata):
        frame_id = frame_meta["frame_id"]
        timestamp = frame_meta["timestamp"]
        path = frame_meta["path"]

        logger.debug(f"Processing frame {idx + 1}/{len(frames_metadata)}: {frame_id}")

        # Perform OCR
        text = perform_ocr_on_frame(Path(path))

        # Store result
        ocr_results.append({
            "frame_id": frame_id,
            "timestamp": timestamp,
            "path": path,
            "text": text
        })

        if (idx + 1) % 5 == 0:
            logger.info(f"OCR progress: {idx + 1}/{len(frames_metadata)} frames processed")

    logger.info(f"OCR complete. Processed {len(ocr_results)} frames")

    # Log some statistics
    non_empty = sum(1 for r in ocr_results if r["text"])
    logger.info(f"Frames with detected text: {non_empty}/{len(ocr_results)}")

    return ocr_results
