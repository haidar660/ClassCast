"""
Debug script to test OCR + fusion pipeline on the 20 test frames.

Runs the complete pipeline:
1. OCR extraction
2. OCR postprocessing + structure detection
3. Math-to-speech conversion
4. Fusion with transcript

Outputs results to JSON and generates an HTML report.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Set Tesseract path for Windows
if os.name == 'nt':  # Windows
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from vision.ocr_engine import extract_ocr_from_image
from vision.ocr_postprocess import postprocess_ocr_result
from fusion.fuse_enhanced import process_single_frame_with_transcript
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)

# Paths
TEST_IMAGES_DIR = Path("data/pics_to_test_OCR")
TEST_CASES_JSON = Path("data/ocr_test_cases.json")
OUTPUT_JSON = Path("data/fusion_results/ocr_fusion_debug_results.json")
OUTPUT_HTML = Path("data/fusion_results/ocr_fusion_debug_results.html")


def load_test_cases() -> List[Dict[str, str]]:
    """Load test cases from JSON file."""
    with open(TEST_CASES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['frames']


def run_pipeline_on_frame(frame_info: Dict[str, str], engine: str = "google_vision") -> Dict[str, Any]:
    """
    Run the complete pipeline on a single frame.

    Args:
        frame_info: Dictionary with 'filename' and 'transcript'
        engine: OCR engine to use

    Returns:
        Dictionary with all results
    """
    filename = frame_info['filename']
    transcript = frame_info['transcript']
    image_path = TEST_IMAGES_DIR / filename

    logger.info(f"Processing: {filename}")

    if not image_path.exists():
        logger.error(f"Image not found: {image_path}")
        return {
            'filename': filename,
            'transcript': transcript,
            'error': 'Image file not found',
            'ocr_raw': '',
            'ocr_clean': '',
            'structure': 'error',
            'fused_ui_text': '',
            'fused_tts_text': ''
        }

    try:
        # Step 1: Extract OCR
        ocr_result = extract_ocr_from_image(image_path, engine=engine)

        if 'error' in ocr_result:
            logger.error(f"OCR failed for {filename}: {ocr_result['error']}")
            return {
                'filename': filename,
                'transcript': transcript,
                'error': ocr_result['error'],
                'ocr_raw': '',
                'ocr_clean': '',
                'structure': 'error',
                'fused_ui_text': '',
                'fused_tts_text': ''
            }

        # Step 2: Process with fusion
        result = process_single_frame_with_transcript(
            image_path=image_path,
            ocr_result=ocr_result,
            transcript_text=transcript,
            timestamp=0.0
        )

        logger.info(f"OK {filename}: structure={result['structure']}, confidence={result['confidence']:.1f}%")

        return result

    except Exception as e:
        logger.error(f"Pipeline failed for {filename}: {str(e)}", exc_info=True)
        return {
            'filename': filename,
            'transcript': transcript,
            'error': str(e),
            'ocr_raw': '',
            'ocr_clean': '',
            'structure': 'error',
            'fused_ui_text': '',
            'fused_tts_text': ''
        }


def generate_html_report(results: List[Dict[str, Any]], output_path: Path):
    """
    Generate an HTML report showing all test results.

    Args:
        results: List of result dictionaries
        output_path: Path to save HTML file
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR + Fusion Debug Results</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .summary {
            background: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .test-case {
            background: white;
            margin-bottom: 30px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #4CAF50;
        }
        .test-case.error {
            border-left-color: #f44336;
        }
        .test-case h2 {
            margin-top: 0;
            color: #333;
            font-size: 1.3em;
        }
        .image-container {
            text-align: center;
            margin: 20px 0;
            background: #fafafa;
            padding: 15px;
            border-radius: 5px;
        }
        .image-container img {
            max-width: 100%;
            max-height: 400px;
            border: 2px solid #ddd;
            border-radius: 4px;
        }
        .section {
            margin: 15px 0;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }
        .section-title {
            font-weight: bold;
            color: #555;
            margin-bottom: 8px;
            font-size: 0.95em;
            text-transform: uppercase;
        }
        .section-content {
            color: #333;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .metadata {
            display: flex;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .metadata-item {
            background: #e3f2fd;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .metadata-item strong {
            color: #1976d2;
        }
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #f44336;
        }
        .tts-text {
            background: #e8f5e9;
            border-left: 4px solid #4CAF50;
        }
        .ui-text {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }
    </style>
</head>
<body>
    <h1>OCR + Fusion Debug Results</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Test Cases:</strong> {total_cases}</p>
        <p><strong>Successful:</strong> {successful}</p>
        <p><strong>Failed:</strong> {failed}</p>
        <p><strong>Success Rate:</strong> {success_rate:.1f}%</p>
    </div>
"""

    # Calculate summary stats
    total_cases = len(results)
    successful = sum(1 for r in results if 'error' not in r or not r.get('error'))
    failed = total_cases - successful
    success_rate = (successful / total_cases * 100) if total_cases > 0 else 0

    # Replace placeholders in summary section
    html_content = html_content.replace('{total_cases}', str(total_cases))
    html_content = html_content.replace('{successful}', str(successful))
    html_content = html_content.replace('{failed}', str(failed))
    html_content = html_content.replace('{success_rate:.1f}', f'{success_rate:.1f}')

    # Add each test case
    for i, result in enumerate(results, 1):
        has_error = 'error' in result and result.get('error')
        error_class = ' error' if has_error else ''

        html_content += f"""
    <div class="test-case{error_class}">
        <h2>Test Case {i}: {result['filename']}</h2>

        <div class="image-container">
            <img src="../../pics_to_test_OCR/{result['filename']}" alt="{result['filename']}">
        </div>

        <div class="metadata">
            <div class="metadata-item">
                <strong>Structure:</strong> {result.get('structure', 'unknown')}
            </div>
            <div class="metadata-item">
                <strong>Confidence:</strong> {result.get('confidence', 0):.1f}%
            </div>
            <div class="metadata-item">
                <strong>Math Elements:</strong> {', '.join(result.get('math_elements', [])) or 'None'}
            </div>
        </div>
"""

        if has_error:
            html_content += f"""
        <div class="error-message">
            <strong>Error:</strong> {result['error']}
        </div>
"""

        html_content += f"""
        <div class="section">
            <div class="section-title">Transcript</div>
            <div class="section-content">{result['transcript']}</div>
        </div>

        <div class="section">
            <div class="section-title">OCR Extracted (Raw)</div>
            <div class="section-content">{result.get('ocr_raw', 'N/A')}</div>
        </div>

        <div class="section">
            <div class="section-title">OCR Extracted (Clean)</div>
            <div class="section-content">{result.get('ocr_clean', 'N/A')}</div>
        </div>

        <div class="section ui-text">
            <div class="section-title">Fused UI Text</div>
            <div class="section-content">{result.get('fused_ui_text', 'N/A')}</div>
        </div>

        <div class="section tts-text">
            <div class="section-title">Fused TTS Text (Podcast-Ready)</div>
            <div class="section-content">{result.get('fused_tts_text', 'N/A')}</div>
        </div>
    </div>
"""

    html_content += """
</body>
</html>
"""

    # Save HTML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"HTML report saved to: {output_path}")


def main():
    """Main function to run the debug pipeline."""
    logger.info("=" * 80)
    logger.info("OCR + FUSION DEBUG PIPELINE")
    logger.info("=" * 80)

    # Load test cases
    logger.info(f"Loading test cases from: {TEST_CASES_JSON}")
    test_cases = load_test_cases()
    logger.info(f"Loaded {len(test_cases)} test cases")

    # Process each frame
    results = []
    for i, frame_info in enumerate(test_cases, 1):
        logger.info(f"\n[{i}/{len(test_cases)}] {frame_info['filename']}")
        # Use Google Cloud Vision API (best quality OCR)
        result = run_pipeline_on_frame(frame_info, engine="google_vision")
        results.append(result)

    # Save results to JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"\nResults saved to: {OUTPUT_JSON}")

    # Generate HTML report
    generate_html_report(results, OUTPUT_HTML)

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    successful = sum(1 for r in results if 'error' not in r or not r.get('error'))
    failed = len(results) - successful
    logger.info(f"Total test cases: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {successful / len(results) * 100:.1f}%")
    logger.info("\n✓ Open the HTML report to view detailed results:")
    logger.info(f"  {OUTPUT_HTML.absolute()}")


if __name__ == "__main__":
    main()
