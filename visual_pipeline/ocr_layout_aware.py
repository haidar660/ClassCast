"""
Layout-aware Tesseract OCR with proper spatial ordering.

This module fixes the text scrambling issue by:
1. Using layout analysis to get bounding boxes
2. Sorting text by reading order (top-to-bottom, left-to-right)
3. Filtering out diagram noise
4. Grouping text into meaningful blocks
"""
from pathlib import Path
from typing import List, Dict, Tuple
import pytesseract
from PIL import Image, ImageDraw
import cv2
import numpy as np

import config
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_for_layout(image_path: Path) -> np.ndarray:
    """Preprocess image for layout-aware OCR."""
    img = cv2.imread(str(image_path))
    if img is None:
        return None

    # Upscale
    upscale = 3.0
    img = cv2.resize(img, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    return gray


def get_text_blocks(image: np.ndarray) -> List[Dict]:
    """
    Get text blocks with bounding boxes and confidence from Tesseract.

    Returns list of blocks sorted by reading order (top-to-bottom, left-to-right).
    """
    # Convert to PIL Image
    pil_image = Image.fromarray(image)

    # Use PSM 3 (fully automatic page segmentation with OSD)
    # This gives us proper layout analysis
    custom_config = r'--oem 3 --psm 3'

    # Get detailed data with bounding boxes
    data = pytesseract.image_to_data(
        pil_image,
        config=custom_config,
        output_type=pytesseract.Output.DICT
    )

    # Extract blocks
    blocks = []
    n_boxes = len(data['text'])

    for i in range(n_boxes):
        text = data['text'][i].strip()
        conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0

        # Filter out empty text and low confidence
        if not text or conf < 30:
            continue

        # Filter out single characters that are likely noise
        if len(text) == 1 and text not in ['X', 'Y', 'x', 'y', 'a', 'b', 'I']:
            continue

        # Filter out obvious diagram noise (symbols, special chars)
        if len(text) <= 3 and all(not c.isalnum() for c in text):
            continue

        # Get bounding box
        x = data['left'][i]
        y = data['top'][i]
        w = data['width'][i]
        h = data['height'][i]

        blocks.append({
            'text': text,
            'conf': conf,
            'bbox': (x, y, w, h),
            'block_num': data['block_num'][i],
            'par_num': data['par_num'][i],
            'line_num': data['line_num'][i],
            'word_num': data['word_num'][i]
        })

    return blocks


def sort_blocks_reading_order(blocks: List[Dict]) -> List[Dict]:
    """
    Sort blocks in natural reading order (top-to-bottom, left-to-right).

    Uses hierarchical sorting:
    1. Block number (Tesseract's layout analysis)
    2. Y-coordinate (top to bottom)
    3. X-coordinate (left to right)
    """
    def sort_key(block):
        x, y, w, h = block['bbox']
        block_num = block['block_num']
        par_num = block['par_num']
        line_num = block['line_num']

        # Primary: block number from Tesseract layout analysis
        # Secondary: Y coordinate (row)
        # Tertiary: X coordinate (column)
        return (block_num, y // 50, x)  # Group by 50px rows

    return sorted(blocks, key=sort_key)


def group_blocks_into_lines(blocks: List[Dict]) -> List[List[Dict]]:
    """
    Group blocks into lines based on Y-coordinate proximity.

    Blocks on the same horizontal line are grouped together.
    """
    if not blocks:
        return []

    lines = []
    current_line = [blocks[0]]
    _, prev_y, _, prev_h = blocks[0]['bbox']

    for block in blocks[1:]:
        _, y, _, h = block['bbox']

        # Check if block is on same line (within vertical threshold)
        y_threshold = max(prev_h, h) * 0.5  # 50% of text height
        if abs(y - prev_y) <= y_threshold:
            current_line.append(block)
        else:
            lines.append(current_line)
            current_line = [block]

        prev_y = y
        prev_h = h

    if current_line:
        lines.append(current_line)

    return lines


def reconstruct_text_from_blocks(blocks: List[Dict]) -> str:
    """
    Reconstruct readable text from sorted blocks.

    Maintains proper spacing and line breaks.
    """
    if not blocks:
        return ""

    # Sort blocks
    sorted_blocks = sort_blocks_reading_order(blocks)

    # Group into lines
    lines = group_blocks_into_lines(sorted_blocks)

    # Reconstruct text
    text_lines = []
    for line in lines:
        # Sort words in line by X coordinate (left to right)
        line_sorted = sorted(line, key=lambda b: b['bbox'][0])
        line_text = ' '.join(b['text'] for b in line_sorted)
        text_lines.append(line_text)

    return '\n'.join(text_lines)


def perform_layout_aware_ocr(frame_path: Path) -> Dict:
    """
    Perform layout-aware OCR that preserves reading order.

    Returns:
        {
            'text': str (properly ordered text),
            'blocks': list (text blocks with positions),
            'confidence': float,
            'method': str
        }
    """
    try:
        # Preprocess
        preprocessed = preprocess_for_layout(frame_path)
        if preprocessed is None:
            return {
                'text': '',
                'blocks': [],
                'confidence': 0.0,
                'method': 'layout_aware_tesseract'
            }

        # Get text blocks with layout
        blocks = get_text_blocks(preprocessed)

        if not blocks:
            return {
                'text': '',
                'blocks': [],
                'confidence': 0.0,
                'method': 'layout_aware_tesseract'
            }

        # Reconstruct text in proper reading order
        ordered_text = reconstruct_text_from_blocks(blocks)

        # Calculate average confidence
        avg_conf = sum(b['conf'] for b in blocks) / len(blocks) if blocks else 0.0

        logger.debug(f"Detected {len(blocks)} text blocks, avg confidence: {avg_conf:.1f}%")

        return {
            'text': ordered_text,
            'blocks': blocks,
            'confidence': avg_conf / 100.0,  # Normalize to 0-1
            'method': 'layout_aware_tesseract'
        }

    except Exception as e:
        logger.error(f"Layout-aware OCR failed for {frame_path}: {e}")
        return {
            'text': '',
            'blocks': [],
            'confidence': 0.0,
            'method': 'layout_aware_tesseract',
            'error': str(e)
        }


def perform_ocr_on_frames(frames_metadata: List[Dict]) -> List[Dict]:
    """
    Perform layout-aware OCR on all frames.

    Args:
        frames_metadata: List of frame metadata

    Returns:
        List of OCR results with properly ordered text
    """
    logger.info(f"Performing layout-aware OCR on {len(frames_metadata)} frames...")
    logger.info("Using Tesseract with layout analysis and spatial ordering")

    ocr_results = []

    for idx, frame_meta in enumerate(frames_metadata):
        frame_id = frame_meta["frame_id"]
        timestamp = frame_meta["timestamp"]
        path = frame_meta["path"]

        logger.debug(f"Processing frame {idx + 1}/{len(frames_metadata)}: {frame_id}")

        # Perform layout-aware OCR
        ocr_result = perform_layout_aware_ocr(Path(path))

        # Store result
        ocr_results.append({
            "frame_id": frame_id,
            "timestamp": timestamp,
            "path": path,
            "text": ocr_result['text'],
            "blocks": ocr_result.get('blocks', []),
            "confidence": ocr_result['confidence'],
            "method": ocr_result['method']
        })

        if (idx + 1) % 5 == 0:
            logger.info(f"OCR progress: {idx + 1}/{len(frames_metadata)} frames processed")

    logger.info(f"Layout-aware OCR complete. Processed {len(ocr_results)} frames")

    # Log statistics
    non_empty = sum(1 for r in ocr_results if r["text"])
    logger.info(f"Frames with detected text: {non_empty}/{len(ocr_results)} ({non_empty/len(ocr_results)*100:.1f}%)")

    if non_empty > 0:
        avg_len = sum(len(r["text"]) for r in ocr_results if r["text"]) / non_empty
        avg_conf = sum(r["confidence"] for r in ocr_results if r["text"]) / non_empty
        logger.info(f"Average text length: {avg_len:.1f} characters")
        logger.info(f"Average confidence: {avg_conf*100:.1f}%")

    return ocr_results
