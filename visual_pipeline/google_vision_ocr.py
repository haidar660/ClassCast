"""
Low-level OCR engine for extracting text from images.
Supports Tesseract, EasyOCR, Google Cloud Vision, and Pix2Text.
"""
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image
import pytesseract

from utils.logging_utils import setup_logger

logger = setup_logger(__name__)

# Google Cloud Vision service key path
GOOGLE_VISION_KEY_PATH = "keys/google_vision.json"


def extract_ocr_from_image(
    image_path: Path,
    engine: str = "google_vision",
    preprocess: bool = False,
    structure: str = None
) -> Dict[str, Any]:
    """
    Extract raw OCR text from image with bounding boxes and confidences.

    Args:
        image_path: Path to image file
        engine: OCR engine to use ("tesseract", "easyocr", "google_vision", or "pix2text")
        preprocess: Whether to apply preprocessing before OCR
        structure: Content structure hint for preprocessing ("equation", "definition", etc.)

    Returns:
        Dictionary with:
            - text: Full extracted text
            - lines: List of text lines with bounding boxes and confidences
            - raw_data: Raw OCR output
            - latex: LaTeX representation (for pix2text only)
            - preprocessed: Whether preprocessing was applied
    """
    # Apply preprocessing if requested
    if preprocess:
        from .ocr_preprocess import auto_preprocess
        logger.info(f"Preprocessing image before OCR (structure={structure})")
        image_path = auto_preprocess(image_path, structure)

    logger.info(f"Running OCR with {engine} on: {image_path}")

    try:
        if engine == "google_vision":
            return _extract_google_vision(image_path)
        elif engine == "pix2text":
            return _extract_pix2text(image_path)
        else:
            # For other engines, load image
            image = Image.open(image_path)

            if engine == "tesseract":
                return _extract_tesseract(image)
            elif engine == "easyocr":
                return _extract_easyocr(image, image_path)
            else:
                raise ValueError(f"Unknown OCR engine: {engine}")

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': str(e),
            'preprocessed': preprocess
        }


def _extract_tesseract(image: Image.Image) -> Dict[str, Any]:
    """Extract using Tesseract OCR."""
    try:
        # Get full text
        text = pytesseract.image_to_string(image)

        # Get detailed data with bounding boxes
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Extract lines with confidences
        lines = []
        current_line = []
        current_line_num = -1

        for i in range(len(data['text'])):
            if data['text'][i].strip():
                line_num = data['line_num'][i]
                conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0.0

                if line_num != current_line_num:
                    if current_line:
                        lines.append({
                            'text': ' '.join([w['text'] for w in current_line]),
                            'confidence': sum(w['conf'] for w in current_line) / len(current_line),
                            'bbox': _merge_bboxes([w['bbox'] for w in current_line])
                        })
                    current_line = []
                    current_line_num = line_num

                current_line.append({
                    'text': data['text'][i],
                    'conf': conf,
                    'bbox': (data['left'][i], data['top'][i],
                             data['left'][i] + data['width'][i],
                             data['top'][i] + data['height'][i])
                })

        # Add last line
        if current_line:
            lines.append({
                'text': ' '.join([w['text'] for w in current_line]),
                'confidence': sum(w['conf'] for w in current_line) / len(current_line),
                'bbox': _merge_bboxes([w['bbox'] for w in current_line])
            })

        return {
            'text': text.strip(),
            'lines': lines,
            'raw_data': data
        }

    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': str(e)
        }


def _extract_easyocr(image: Image.Image, image_path: Path) -> Dict[str, Any]:
    """Extract using EasyOCR."""
    try:
        import easyocr
        reader = easyocr.Reader(['en'])

        # EasyOCR works with file paths
        results = reader.readtext(str(image_path))

        # Convert to standard format
        lines = []
        text_parts = []

        for bbox, text, conf in results:
            lines.append({
                'text': text,
                'confidence': float(conf) * 100,  # Convert to percentage
                'bbox': _bbox_from_points(bbox)
            })
            text_parts.append(text)

        return {
            'text': ' '.join(text_parts),
            'lines': lines,
            'raw_data': results
        }

    except Exception as e:
        logger.error(f"EasyOCR failed: {e}")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': str(e)
        }


def _merge_bboxes(bboxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    """Merge multiple bounding boxes into one."""
    if not bboxes:
        return (0, 0, 0, 0)

    x1 = min(bbox[0] for bbox in bboxes)
    y1 = min(bbox[1] for bbox in bboxes)
    x2 = max(bbox[2] for bbox in bboxes)
    y2 = max(bbox[3] for bbox in bboxes)

    return (x1, y1, x2, y2)


def _bbox_from_points(points: List[List[int]]) -> Tuple[int, int, int, int]:
    """Convert EasyOCR point format to bbox format."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _extract_google_vision(image_path: Path) -> Dict[str, Any]:
    """
    Extract using Google Cloud Vision API.

    Uses document_text_detection for best results on dense boards and slides.
    """
    try:
        from google.cloud import vision

        # Create client using service account key
        client = vision.ImageAnnotatorClient.from_service_account_json(
            GOOGLE_VISION_KEY_PATH
        )

        # Load image
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Use document_text_detection for better results on dense text
        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(response.error.message)

        # Extract full text
        full_text = response.full_text_annotation.text if response.full_text_annotation else ''

        # Extract lines with bounding boxes and confidences
        lines = []

        if response.full_text_annotation and response.full_text_annotation.pages:
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    # Block confidence
                    block_confidence = block.confidence * 100 if hasattr(block, 'confidence') else 90.0

                    for paragraph in block.paragraphs:
                        # Combine words in paragraph into line
                        line_text = ''
                        word_confidences = []
                        all_vertices = []

                        for word in paragraph.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            line_text += word_text + ' '

                            # Get word confidence
                            word_conf = word.confidence * 100 if hasattr(word, 'confidence') else block_confidence
                            word_confidences.append(word_conf)

                            # Collect vertices
                            if word.bounding_box and word.bounding_box.vertices:
                                all_vertices.extend([(v.x, v.y) for v in word.bounding_box.vertices])

                        if line_text.strip():
                            # Calculate bounding box for the line
                            if all_vertices:
                                xs = [v[0] for v in all_vertices]
                                ys = [v[1] for v in all_vertices]
                                bbox = (min(xs), min(ys), max(xs), max(ys))
                            else:
                                bbox = (0, 0, 0, 0)

                            # Calculate average confidence
                            avg_confidence = sum(word_confidences) / len(word_confidences) if word_confidences else block_confidence

                            lines.append({
                                'text': line_text.strip(),
                                'confidence': avg_confidence,
                                'bbox': bbox
                            })

        logger.info(f"Google Vision extracted {len(lines)} lines")

        return {
            'text': full_text.strip(),
            'lines': lines,
            'raw_data': response
        }

    except ImportError:
        logger.error("google-cloud-vision not installed. Install with: pip install google-cloud-vision")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': 'google-cloud-vision not installed'
        }

    except Exception as e:
        logger.error(f"Google Vision API failed: {e}")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': str(e)
        }


def _extract_pix2text(image_path: Path) -> Dict[str, Any]:
    """
    Extract using Pix2Text (specialized for mathematical expressions).

    Returns LaTeX representation which is converted to natural text.
    Best for handwritten math, equations, formulas.
    """
    try:
        from pix2text import Pix2Text
        import re

        # Initialize Pix2Text (will download models on first run)
        p2t = Pix2Text()

        # Run OCR - returns dict with 'text' (LaTeX) and other metadata
        result = p2t.recognize(str(image_path), resized_shape=768)

        # Extract LaTeX
        latex = result if isinstance(result, str) else result.get('text', '')

        # Convert LaTeX to plain text for compatibility
        plain_text = _latex_to_text(latex)

        # Pix2Text doesn't provide line-by-line data, so create single line
        # Estimate confidence based on LaTeX quality
        confidence = _estimate_latex_confidence(latex)

        lines = [{
            'text': plain_text,
            'confidence': confidence,
            'bbox': (0, 0, 100, 100)  # Placeholder bbox
        }]

        logger.info(f"Pix2Text extracted LaTeX: {latex[:50]}...")
        logger.info(f"Converted to text: {plain_text[:50]}...")

        return {
            'text': plain_text,
            'lines': lines,
            'raw_data': result,
            'latex': latex,  # Keep LaTeX for reference
            'engine': 'pix2text'
        }

    except ImportError:
        logger.error("pix2text not installed. Install with: pip install pix2text")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': 'pix2text not installed'
        }

    except Exception as e:
        logger.error(f"Pix2Text failed: {e}")
        return {
            'text': '',
            'lines': [],
            'raw_data': None,
            'error': str(e)
        }


def _latex_to_text(latex: str) -> str:
    """
    Convert LaTeX mathematical notation to plain text.

    Examples:
        x^{2} -> x²
        \\frac{a}{b} -> (a)/(b)
        \\sum_{i=1}^{n} -> Σ(i=1 to n)
    """
    if not latex:
        return ''

    text = latex

    # Remove LaTeX math delimiters
    text = text.replace('$', '')
    text = text.replace('\\[', '').replace('\\]', '')
    text = text.replace('\\(', '').replace('\\)', '')

    # Convert common LaTeX commands to Unicode/text
    replacements = {
        '\\times': '×',
        '\\div': '÷',
        '\\pm': '±',
        '\\leq': '≤',
        '\\geq': '≥',
        '\\neq': '≠',
        '\\approx': '≈',
        '\\sum': 'Σ',
        '\\prod': 'Π',
        '\\int': '∫',
        '\\infty': '∞',
        '\\alpha': 'α',
        '\\beta': 'β',
        '\\gamma': 'γ',
        '\\delta': 'δ',
        '\\theta': 'θ',
        '\\pi': 'π',
        '\\sigma': 'σ',
        '\\lim': 'lim',
        '\\sin': 'sin',
        '\\cos': 'cos',
        '\\tan': 'tan',
        '\\log': 'log',
        '\\ln': 'ln',
        '\\partial': '∂',
        '\\nabla': '∇',
        '\\in': '∈',
        '\\subset': '⊂',
        '\\cup': '∪',
        '\\cap': '∩',
        '\\rightarrow': '→',
        '\\leftarrow': '←',
        '\\Rightarrow': '⇒',
        '\\Leftarrow': '⇐',
    }

    for latex_cmd, unicode_char in replacements.items():
        text = text.replace(latex_cmd, unicode_char)

    # Handle fractions: \frac{a}{b} -> (a)/(b)
    import re
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)

    # Handle superscripts: x^{2} -> x²
    superscript_map = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                       '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    text = re.sub(r'\^(\d)', lambda m: superscript_map.get(m.group(1), '^' + m.group(1)), text)
    text = re.sub(r'\^\{(\d+)\}', lambda m: ''.join(superscript_map.get(c, c) for c in m.group(1)), text)

    # Handle subscripts: x_{i} -> x_i (keep underscore for now)
    text = re.sub(r'_\{([^}]+)\}', r'_\1', text)

    # Remove remaining braces
    text = text.replace('{', '').replace('}', '')

    # Remove backslashes from remaining commands
    text = re.sub(r'\\(\w+)', r'\1', text)

    # Clean up spacing
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def _estimate_latex_confidence(latex: str) -> float:
    """
    Estimate confidence based on LaTeX quality.

    Good LaTeX (valid commands, proper structure) -> high confidence
    Malformed LaTeX or gibberish -> low confidence
    """
    if not latex:
        return 0.0

    # Check for valid LaTeX structure
    score = 50.0  # Base score

    # Bonus for valid LaTeX commands
    valid_commands = ['frac', 'sum', 'int', 'lim', 'sqrt', 'sin', 'cos', 'log']
    for cmd in valid_commands:
        if f'\\{cmd}' in latex:
            score += 5.0

    # Bonus for mathematical symbols
    if any(c in latex for c in ['=', '+', '-', '*', '/', '^', '_']):
        score += 10.0

    # Bonus for balanced braces
    if latex.count('{') == latex.count('}'):
        score += 10.0

    # Penalty for gibberish indicators
    if any(c in latex for c in ['?', '!', '…']):
        score -= 20.0

    # Cap at 95 (never claim 100% confidence)
    return min(score, 95.0)
