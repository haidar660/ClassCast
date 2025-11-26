"""
Run OCR on all 20 frames in data/pics_to_test_OCR folder.
"""
from pathlib import Path
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Import the OCR function directly without config
from typing import List, Dict

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
    """
    pil_image = Image.fromarray(image)
    custom_config = r'--oem 3 --psm 3'

    data = pytesseract.image_to_data(
        pil_image,
        config=custom_config,
        output_type=pytesseract.Output.DICT
    )

    blocks = []
    n_boxes = len(data['text'])

    for i in range(n_boxes):
        text = data['text'][i].strip()
        conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0

        if not text or conf < 30:
            continue

        if len(text) == 1 and text not in ['X', 'Y', 'x', 'y', 'a', 'b', 'I']:
            continue

        if len(text) <= 3 and all(not c.isalnum() for c in text):
            continue

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
    """Sort blocks in natural reading order."""
    def sort_key(block):
        x, y, w, h = block['bbox']
        block_num = block['block_num']
        return (block_num, y // 50, x)

    return sorted(blocks, key=sort_key)


def group_blocks_into_lines(blocks: List[Dict]) -> List[List[Dict]]:
    """Group blocks into lines based on Y-coordinate proximity."""
    if not blocks:
        return []

    lines = []
    current_line = [blocks[0]]
    _, prev_y, _, prev_h = blocks[0]['bbox']

    for block in blocks[1:]:
        _, y, _, h = block['bbox']

        y_threshold = max(prev_h, h) * 0.5
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
    """Reconstruct readable text from sorted blocks."""
    if not blocks:
        return ""

    sorted_blocks = sort_blocks_reading_order(blocks)
    lines = group_blocks_into_lines(sorted_blocks)

    text_lines = []
    for line in lines:
        line_sorted = sorted(line, key=lambda b: b['bbox'][0])
        line_text = ' '.join(b['text'] for b in line_sorted)
        text_lines.append(line_text)

    return '\n'.join(text_lines)


def perform_layout_aware_ocr(frame_path: Path) -> Dict:
    """Perform layout-aware OCR that preserves reading order."""
    try:
        preprocessed = preprocess_for_layout(frame_path)
        if preprocessed is None:
            return {
                'text': '',
                'blocks': [],
                'confidence': 0.0,
                'method': 'layout_aware_tesseract'
            }

        blocks = get_text_blocks(preprocessed)

        if not blocks:
            return {
                'text': '',
                'blocks': [],
                'confidence': 0.0,
                'method': 'layout_aware_tesseract'
            }

        ordered_text = reconstruct_text_from_blocks(blocks)
        avg_conf = sum(b['conf'] for b in blocks) / len(blocks) if blocks else 0.0

        return {
            'text': ordered_text,
            'blocks': blocks,
            'confidence': avg_conf / 100.0,
            'method': 'layout_aware_tesseract'
        }

    except Exception as e:
        return {
            'text': '',
            'blocks': [],
            'confidence': 0.0,
            'method': 'layout_aware_tesseract',
            'error': str(e)
        }

def run_ocr_on_all_frames():
    """Run OCR on all frames and report results."""
    frames_dir = Path("data/pics_to_test_OCR")

    # Get all PNG frames
    frame_files = sorted(frames_dir.glob("*.png"))

    print(f"Found {len(frame_files)} frames to process\n")
    print("=" * 80)

    results = []

    for idx, frame_path in enumerate(frame_files, 1):
        print(f"\nProcessing [{idx}/{len(frame_files)}]: {frame_path.name}")
        print("-" * 80)

        # Perform OCR
        ocr_result = perform_layout_aware_ocr(frame_path)

        # Display results
        confidence = ocr_result['confidence'] * 100
        text = ocr_result['text']
        num_blocks = len(ocr_result.get('blocks', []))

        print(f"Confidence: {confidence:.1f}%")
        print(f"Text blocks detected: {num_blocks}")
        print(f"Text length: {len(text)} characters")

        if text:
            # Show first 200 characters
            preview = text[:200] + ("..." if len(text) > 200 else "")
            print(f"\nText preview:\n{preview}")
        else:
            print("\nNo text detected")

        results.append({
            'frame': frame_path.name,
            'confidence': confidence,
            'text_length': len(text),
            'num_blocks': num_blocks,
            'has_text': bool(text),
            'full_text': text
        })

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    frames_with_text = sum(1 for r in results if r['has_text'])
    avg_confidence_all = sum(r['confidence'] for r in results) / len(results)

    # Average confidence for frames with text
    if frames_with_text > 0:
        avg_confidence_with_text = sum(r['confidence'] for r in results if r['has_text']) / frames_with_text
        avg_text_length = sum(r['text_length'] for r in results if r['has_text']) / frames_with_text
        avg_blocks = sum(r['num_blocks'] for r in results if r['has_text']) / frames_with_text
    else:
        avg_confidence_with_text = 0
        avg_text_length = 0
        avg_blocks = 0

    print(f"\nTotal frames processed: {len(results)}")
    print(f"Frames with text: {frames_with_text} ({frames_with_text/len(results)*100:.1f}%)")
    print(f"\nAverage confidence (all frames): {avg_confidence_all:.2f}%")
    print(f"Average confidence (frames with text): {avg_confidence_with_text:.2f}%")
    print(f"Average text length: {avg_text_length:.1f} characters")
    print(f"Average text blocks: {avg_blocks:.1f}")

    # Confidence distribution
    print("\nConfidence distribution:")
    high_conf = sum(1 for r in results if r['confidence'] >= 80)
    med_conf = sum(1 for r in results if 60 <= r['confidence'] < 80)
    low_conf = sum(1 for r in results if 30 <= r['confidence'] < 60)
    very_low_conf = sum(1 for r in results if r['confidence'] < 30)

    print(f"  High (>=80%): {high_conf} frames")
    print(f"  Medium (60-79%): {med_conf} frames")
    print(f"  Low (30-59%): {low_conf} frames")
    print(f"  Very low (<30%): {very_low_conf} frames")

    return results

if __name__ == "__main__":
    results = run_ocr_on_all_frames()
