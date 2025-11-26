"""
Test OCR on the first 5 frames from data/pics_to_test_OCR

This script:
1. Runs OpenAI OCR on the first 5 test frames
2. Generates an interactive HTML viewer showing the results
3. Opens the viewer in your browser
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import time

from ocr.visual_pipeline.ocr_openai import perform_ocr_on_frame
from ocr.vision.ocr_preprocess import preprocess_for_ocr
from utils.logging_utils import setup_logger
from ocr.vision.latex_converter import latex_to_text

logger = setup_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

TEST_FRAMES_DIR = Path("data/pics_to_test_OCR")
OUTPUT_JSON = Path("data/ocr_test_results.json")
OUTPUT_HTML = Path("data/ocr_test_viewer.html")
NUM_FRAMES = 5  # Test first 5 frames

# Preprocessing options (set to True to enable)
USE_PREPROCESSING = True
PREPROCESS_OPTIONS = {
    "target_height": 800,       # Upscale to this height if smaller
    "enhance_contrast": True,   # CLAHE contrast enhancement
    "denoise": True,           # Noise reduction
    "binarize": False,         # Convert to black/white (good for printed text)
    "sharpen": False           # Edge sharpening
}


# ============================================================================
# MAIN TEST
# ============================================================================

def run_ocr_test():
    """Run OCR test on first 5 frames."""
    logger.info("=" * 80)
    logger.info("OCR TEST ON FIRST 5 FRAMES")
    logger.info("=" * 80)

    # Get first 5 frames
    all_frames = sorted(TEST_FRAMES_DIR.glob("*.png"))[:NUM_FRAMES]

    if not all_frames:
        logger.error(f"No frames found in {TEST_FRAMES_DIR}")
        return

    logger.info(f"Testing OCR on {len(all_frames)} frames:")
    for f in all_frames:
        logger.info(f"  - {f.name}")

    # Run OCR on each frame
    results = []

    for idx, frame_path in enumerate(all_frames, 1):
        logger.info(f"\n[{idx}/{len(all_frames)}] Processing {frame_path.name}...")

        # Preprocess image if enabled
        preprocessed_path = frame_path
        if USE_PREPROCESSING:
            logger.info("  Preprocessing image...")
            try:
                preprocessed_path = preprocess_for_ocr(frame_path, **PREPROCESS_OPTIONS)
                logger.info(f"  Preprocessed: {preprocessed_path}")
            except Exception as e:
                logger.warning(f"  Preprocessing failed: {e}, using original image")
                preprocessed_path = frame_path

        # Run OCR
        start_time = time.time()
        ocr_result = perform_ocr_on_frame(preprocessed_path)
        elapsed = time.time() - start_time

        # Convert LaTeX to plain text (postprocessing)
        latex_text = ocr_result.get("text", "")
        plain_text = latex_to_text(latex_text) if latex_text else ""

        result = {
            "frame_id": idx,
            "filename": frame_path.name,
            "path": str(frame_path),
            "preprocessed_path": str(preprocessed_path) if USE_PREPROCESSING else None,
            "text": latex_text,
            "plain_text": plain_text,
            "confidence": ocr_result.get("confidence", 0.0),
            "method": ocr_result.get("method", "openai"),
            "preprocessing_enabled": USE_PREPROCESSING,
            "processing_time": round(elapsed, 2),
            "error": ocr_result.get("error", None)
        }

        results.append(result)

        # Log result
        if result["text"]:
            logger.info(f"  + Extracted {len(result['text'])} characters in {elapsed:.2f}s")
            logger.info(f"  LaTeX: {result['text'][:100]}...")
            logger.info(f"  Plain: {result['plain_text'][:100]}...")
        else:
            logger.warning(f"  - No text extracted")
            if result["error"]:
                logger.error(f"  Error: {result['error']}")

    # Save results to JSON
    logger.info(f"\nSaving results to {OUTPUT_JSON}...")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Generate HTML viewer
    logger.info(f"Generating HTML viewer at {OUTPUT_HTML}...")
    generate_html_viewer(results)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("OCR TEST COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Frames tested: {len(results)}")

    successful = sum(1 for r in results if r['text'])
    failed = len(results) - successful

    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")

    total_chars = sum(len(r['text']) for r in results)
    avg_time = sum(r['processing_time'] for r in results) / len(results)

    logger.info(f"Total characters extracted: {total_chars}")
    logger.info(f"Average processing time: {avg_time:.2f}s")

    logger.info(f"\nResults saved to: {OUTPUT_JSON}")
    logger.info(f"HTML viewer: {OUTPUT_HTML}")
    logger.info("=" * 80)

    return str(OUTPUT_HTML)


# ============================================================================
# HTML VIEWER GENERATOR
# ============================================================================

def generate_html_viewer(results: List[Dict[str, Any]]):
    """Generate interactive HTML viewer for OCR results."""

    html = []

    # HTML header
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Test Results - First 5 Frames</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            font-size: 32px;
            color: #2d3748;
            margin-bottom: 10px;
        }

        .header p {
            color: #718096;
            font-size: 16px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .stat-card h3 {
            font-size: 14px;
            color: #718096;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }

        .results-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
        }

        .result-card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }

        .result-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        .result-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }

        .result-header h2 {
            font-size: 20px;
            color: #2d3748;
        }

        .status-badge {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }

        .status-badge.success {
            background: #c6f6d5;
            color: #22543d;
        }

        .status-badge.error {
            background: #fed7d7;
            color: #742a2a;
        }

        .result-content {
            display: grid;
            grid-template-columns: 400px 1fr;
            gap: 30px;
        }

        .image-section {
            position: sticky;
            top: 20px;
            height: fit-content;
        }

        .image-container {
            width: 100%;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            background: #f7fafc;
        }

        .image-container img {
            width: 100%;
            height: auto;
            display: block;
        }

        .image-info {
            padding: 12px;
            background: #f7fafc;
            border-top: 1px solid #e2e8f0;
            font-size: 13px;
            color: #718096;
        }

        .text-section {
            min-height: 300px;
        }

        .text-label {
            font-size: 14px;
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
        }

        .text-label svg {
            margin-right: 8px;
        }

        .extracted-text {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            color: #2d3748;
            white-space: pre-wrap;
            word-wrap: break-word;
            min-height: 200px;
            max-height: 500px;
            overflow-y: auto;
        }

        .extracted-text::-webkit-scrollbar {
            width: 8px;
        }

        .extracted-text::-webkit-scrollbar-track {
            background: #edf2f7;
            border-radius: 4px;
        }

        .extracted-text::-webkit-scrollbar-thumb {
            background: #cbd5e0;
            border-radius: 4px;
        }

        .extracted-text::-webkit-scrollbar-thumb:hover {
            background: #a0aec0;
        }

        .metadata {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
        }

        .metadata-item {
            text-align: center;
        }

        .metadata-item .label {
            font-size: 12px;
            color: #718096;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metadata-item .value {
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
        }

        .error-message {
            background: #fff5f5;
            border: 1px solid #fc8181;
            border-radius: 8px;
            padding: 15px;
            color: #742a2a;
            margin-top: 15px;
        }

        .copy-button {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 10px;
        }

        .copy-button:hover {
            background: #5a67d8;
        }

        .copy-button:active {
            background: #4c51bf;
        }

        @media (max-width: 1024px) {
            .result-content {
                grid-template-columns: 1fr;
            }

            .image-section {
                position: static;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OCR Test Results</h1>
            <p>Testing OpenAI GPT-4o Vision OCR with preprocessing on the first 5 frames from pics_to_test_OCR</p>
        </div>
""")

    # Calculate statistics
    total_frames = len(results)
    successful = sum(1 for r in results if r['text'])
    failed = total_frames - successful
    total_chars = sum(len(r['text']) for r in results)
    avg_time = sum(r['processing_time'] for r in results) / total_frames if results else 0

    # Stats cards
    html.append(f"""
        <div class="stats">
            <div class="stat-card">
                <h3>Total Frames</h3>
                <div class="value">{total_frames}</div>
            </div>
            <div class="stat-card">
                <h3>Successful</h3>
                <div class="value" style="color: #48bb78;">{successful}</div>
            </div>
            <div class="stat-card">
                <h3>Failed</h3>
                <div class="value" style="color: #f56565;">{failed}</div>
            </div>
            <div class="stat-card">
                <h3>Characters Extracted</h3>
                <div class="value">{total_chars:,}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Processing Time</h3>
                <div class="value">{avg_time:.2f}s</div>
            </div>
        </div>
""")

    # Results grid
    html.append('<div class="results-grid">')

    for result in results:
        has_text = bool(result['text'])
        status_class = "success" if has_text else "error"
        status_text = "✓ Success" if has_text else "✗ Failed"

        # Convert path to relative for browser
        img_path = result['path'].replace('\\', '/').replace('data/', '')

        html.append(f"""
            <div class="result-card">
                <div class="result-header">
                    <h2>Frame {result['frame_id']}: {result['filename']}</h2>
                    <span class="status-badge {status_class}">{status_text}</span>
                </div>

                <div class="result-content">
                    <div class="image-section">
                        <div class="image-container">
                            <img src="{img_path}" alt="{result['filename']}">
                            <div class="image-info">
                                {result['filename']}
                            </div>
                        </div>
                    </div>

                    <div class="text-section">
                        <div class="text-label">
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm1 2v10h14V7H5zm2 2h10v2H7V9zm0 4h6v2H7v-2z"/>
                            </svg>
                            LaTeX Output
                        </div>
                        <div class="extracted-text" id="text-{result['frame_id']}">{result['text'] if has_text else '(No text extracted)'}</div>
                        {f'<button class="copy-button" onclick="copyText({result["frame_id"]})">Copy LaTeX</button>' if has_text else ''}

                        <div class="text-label" style="margin-top: 20px;">
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
                                <path d="M11 7h2v6h-2zm0 8h2v2h-2z"/>
                            </svg>
                            Plain Text (TTS-Ready)
                        </div>
                        <div class="extracted-text" id="plain-{result['frame_id']}" style="background: #f0fdf4; border-color: #86efac;">{result.get('plain_text', '') if has_text else '(No plain text)'}</div>
                        {f'<button class="copy-button" onclick="copyPlainText({result["frame_id"]})">Copy Plain Text</button>' if has_text and result.get('plain_text') else ''}

                        <div class="metadata">
                            <div class="metadata-item">
                                <div class="label">Characters</div>
                                <div class="value">{len(result['text'])}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="label">Processing Time</div>
                                <div class="value">{result['processing_time']}s</div>
                            </div>
                            <div class="metadata-item">
                                <div class="label">Method</div>
                                <div class="value">{result['method']}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="label">Preprocessing</div>
                                <div class="value">{'Yes' if result.get('preprocessing_enabled') else 'No'}</div>
                            </div>
                        </div>

                        {f'<div class="error-message"><strong>Error:</strong> {result["error"]}</div>' if result.get('error') else ''}
                    </div>
                </div>
            </div>
        """)

    html.append('</div>')  # Close results-grid

    # JavaScript
    html.append("""
        <script>
            function copyText(frameId) {
                const textElement = document.getElementById(`text-${frameId}`);
                const text = textElement.textContent;

                navigator.clipboard.writeText(text).then(() => {
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '✓ Copied!';
                    button.style.background = '#48bb78';

                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.background = '#667eea';
                    }, 2000);
                });
            }

            function copyPlainText(frameId) {
                const textElement = document.getElementById(`plain-${frameId}`);
                const text = textElement.textContent;

                navigator.clipboard.writeText(text).then(() => {
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '✓ Copied!';
                    button.style.background = '#48bb78';

                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.background = '#667eea';
                    }, 2000);
                });
            }
        </script>
    </div>
</body>
</html>
""")

    # Write HTML file
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(''.join(html))

    logger.info(f"HTML viewer generated: {OUTPUT_HTML}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    html_path = run_ocr_test()

    # Open in browser
    if html_path:
        import subprocess
        logger.info(f"\nOpening viewer in browser...")
        subprocess.run(["start", "", html_path], shell=True)
