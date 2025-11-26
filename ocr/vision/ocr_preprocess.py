"""
Image preprocessing for improved OCR accuracy.

Applies enhancement techniques before OCR to improve recognition quality.
"""
from pathlib import Path
from typing import Tuple, Optional
import cv2
import numpy as np
from PIL import Image

from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def preprocess_for_ocr(
    image_path: Path,
    target_height: int = 800,
    enhance_contrast: bool = True,
    denoise: bool = True,
    binarize: bool = False,
    sharpen: bool = False
) -> Path:
    """
    Preprocess image for better OCR results.

    Args:
        image_path: Path to original image
        target_height: Target height for resizing (maintains aspect ratio)
        enhance_contrast: Apply adaptive histogram equalization
        denoise: Apply denoising filter
        binarize: Convert to black & white (good for printed text)
        sharpen: Apply sharpening filter

    Returns:
        Path to preprocessed image (saved in temp directory)
    """
    logger.info(f"Preprocessing image: {image_path}")

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return image_path

    original_shape = image.shape
    logger.debug(f"Original size: {original_shape[1]}x{original_shape[0]}")

    # 1. Upscale if too small
    if image.shape[0] < target_height:
        scale_factor = target_height / image.shape[0]
        new_width = int(image.shape[1] * scale_factor)
        new_height = int(image.shape[0] * scale_factor)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        logger.debug(f"Upscaled to: {new_width}x{new_height}")

    # 2. Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 3. Denoise
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        logger.debug("Applied denoising")

    # 4. Enhance contrast
    if enhance_contrast:
        # Adaptive histogram equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        logger.debug("Enhanced contrast with CLAHE")

    # 5. Sharpen
    if sharpen:
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        gray = cv2.filter2D(gray, -1, kernel)
        logger.debug("Applied sharpening")

    # 6. Binarize (optional, good for clean printed text)
    if binarize:
        # Otsu's thresholding
        _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        logger.debug("Applied binarization")

    # Save preprocessed image
    output_dir = Path("data/preprocessed_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"preprocessed_{image_path.name}"

    cv2.imwrite(str(output_path), gray)
    logger.info(f"Saved preprocessed image: {output_path}")

    return output_path


def preprocess_for_math_ocr(image_path: Path) -> Path:
    """
    Preprocessing optimized for handwritten mathematical expressions.

    Uses aggressive enhancement for better recognition of:
    - Math symbols (∫, Σ, ≤, ≥, etc.)
    - Subscripts and superscripts
    - Fractions and complex layouts
    """
    return preprocess_for_ocr(
        image_path,
        target_height=1000,  # Higher resolution for small symbols
        enhance_contrast=True,
        denoise=True,
        binarize=False,  # Keep grayscale for handwriting
        sharpen=True  # Sharpen to clarify symbols
    )


def preprocess_for_text_ocr(image_path: Path) -> Path:
    """
    Preprocessing optimized for printed text (definitions, lists, etc.).

    Uses binarization for crisp text recognition.
    """
    return preprocess_for_ocr(
        image_path,
        target_height=800,
        enhance_contrast=True,
        denoise=True,
        binarize=True,  # Binary for printed text
        sharpen=False
    )


def auto_preprocess(image_path: Path, structure: Optional[str] = None) -> Path:
    """
    Automatically choose preprocessing based on content structure.

    Args:
        image_path: Path to image
        structure: Content structure hint ("equation", "definition", etc.)

    Returns:
        Path to preprocessed image
    """
    if structure in ['equation', 'fraction', 'integral', 'summation', 'limit']:
        logger.info(f"Using math preprocessing for {structure}")
        return preprocess_for_math_ocr(image_path)

    elif structure in ['definition', 'bullets', 'steps', 'abbreviation']:
        logger.info(f"Using text preprocessing for {structure}")
        return preprocess_for_text_ocr(image_path)

    else:
        # Default: moderate preprocessing
        logger.info("Using default preprocessing")
        return preprocess_for_ocr(
            image_path,
            enhance_contrast=True,
            denoise=True,
            binarize=False
        )


def compare_preprocessing(image_path: Path) -> dict:
    """
    Compare different preprocessing strategies on the same image.

    Useful for testing which approach works best.

    Returns:
        Dictionary with paths to different preprocessed versions
    """
    results = {}

    # Original
    results['original'] = image_path

    # Different strategies
    results['math_optimized'] = preprocess_for_math_ocr(image_path)
    results['text_optimized'] = preprocess_for_text_ocr(image_path)

    # Minimal preprocessing
    results['minimal'] = preprocess_for_ocr(
        image_path,
        enhance_contrast=True,
        denoise=False,
        binarize=False
    )

    # Aggressive preprocessing
    results['aggressive'] = preprocess_for_ocr(
        image_path,
        target_height=1200,
        enhance_contrast=True,
        denoise=True,
        binarize=False,
        sharpen=True
    )

    return results
