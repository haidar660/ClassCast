"""
Test OCR Comparison: With vs Without Preprocessing

This script:
1. Runs OpenAI OCR on the first 5 test frames WITH preprocessing
2. Runs OpenAI OCR on the same frames WITHOUT preprocessing
3. Generates a comparison showing both results side-by-side
4. Converts LaTeX to speech-ready plain text
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import time

from visual_pipeline.ocr_openai import perform_ocr_on_frame
from vision.ocr_preprocess import preprocess_for_ocr
from utils.logging_utils import setup_logger
from vision.latex_converter import latex_to_text

logger = setup_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

TEST_FRAMES_DIR = Path("data/pics_to_test_OCR")
OUTPUT_JSON = Path("data/ocr_comparison_results.json")
OUTPUT_HTML = Path("data/ocr_comparison_viewer.html")
NUM_FRAMES = 5  # Test first 5 frames

# Preprocessing options
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

def run_comparison_test():
    """Run OCR test comparing with and without preprocessing."""
    logger.info("=" * 80)
    logger.info("OCR COMPARISON TEST: WITH vs WITHOUT PREPROCESSING")
    logger.info("=" * 80)

    # Get first 5 frames
    all_frames = sorted(TEST_FRAMES_DIR.glob("*.png"))[:NUM_FRAMES]

    if not all_frames:
        logger.error(f"No frames found in {TEST_FRAMES_DIR}")
        return

    logger.info(f"Testing OCR on {len(all_frames)} frames:")
    for f in all_frames:
        logger.info(f"  - {f.name}")

    # Run OCR on each frame - both with and without preprocessing
    results = []

    for idx, frame_path in enumerate(all_frames, 1):
        logger.info(f"\n[{idx}/{len(all_frames)}] Processing {frame_path.name}...")

        # ===== WITHOUT PREPROCESSING =====
        logger.info("  [1/2] Running OCR WITHOUT preprocessing...")
        start_time = time.time()
        ocr_without = perform_ocr_on_frame(frame_path)
        time_without = time.time() - start_time

        latex_without = ocr_without.get("text", "")
        plain_without = latex_to_text(latex_without) if latex_without else ""

        logger.info(f"    → Extracted {len(latex_without)} characters in {time_without:.2f}s")

        # ===== WITH PREPROCESSING =====
        logger.info("  [2/2] Running OCR WITH preprocessing...")

        # Preprocess image
        preprocessed_path = frame_path
        try:
            preprocessed_path = preprocess_for_ocr(frame_path, **PREPROCESS_OPTIONS)
            logger.info(f"    → Preprocessed: {preprocessed_path}")
        except Exception as e:
            logger.warning(f"    → Preprocessing failed: {e}, using original image")
            preprocessed_path = frame_path

        # Run OCR on preprocessed image
        start_time = time.time()
        ocr_with = perform_ocr_on_frame(preprocessed_path)
        time_with = time.time() - start_time

        latex_with = ocr_with.get("text", "")
        plain_with = latex_to_text(latex_with) if latex_with else ""

        logger.info(f"    → Extracted {len(latex_with)} characters in {time_with:.2f}s")

        # Compile result
        result = {
            "frame_id": idx,
            "filename": frame_path.name,
            "path": str(frame_path),
            "preprocessed_path": str(preprocessed_path),

            # Without preprocessing
            "without_preprocessing": {
                "text": latex_without,
                "plain_text": plain_without,
                "confidence": ocr_without.get("confidence", 0.0),
                "method": ocr_without.get("method", "openai"),
                "processing_time": round(time_without, 2),
                "error": ocr_without.get("error", None),
                "char_count": len(latex_without)
            },

            # With preprocessing
            "with_preprocessing": {
                "text": latex_with,
                "plain_text": plain_with,
                "confidence": ocr_with.get("confidence", 0.0),
                "method": ocr_with.get("method", "openai"),
                "processing_time": round(time_with, 2),
                "error": ocr_with.get("error", None),
                "char_count": len(latex_with)
            }
        }

        results.append(result)

        # Log comparison
        diff = len(latex_with) - len(latex_without)
        logger.info(f"  ✓ Comparison: {diff:+d} chars difference")

    # Save results to JSON
    logger.info(f"\nSaving results to {OUTPUT_JSON}...")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Generate HTML viewer
    logger.info(f"Generating comparison HTML viewer at {OUTPUT_HTML}...")
    generate_comparison_html(results)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("OCR COMPARISON TEST COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Frames tested: {len(results)}")

    total_without = sum(r['without_preprocessing']['char_count'] for r in results)
    total_with = sum(r['with_preprocessing']['char_count'] for r in results)
    avg_time_without = sum(r['without_preprocessing']['processing_time'] for r in results) / len(results)
    avg_time_with = sum(r['with_preprocessing']['processing_time'] for r in results) / len(results)

    logger.info(f"\nWithout preprocessing:")
    logger.info(f"  - Total characters: {total_without}")
    logger.info(f"  - Avg processing time: {avg_time_without:.2f}s")

    logger.info(f"\nWith preprocessing:")
    logger.info(f"  - Total characters: {total_with}")
    logger.info(f"  - Avg processing time: {avg_time_with:.2f}s")

    logger.info(f"\nDifference: {total_with - total_without:+d} characters")

    logger.info(f"\nResults saved to: {OUTPUT_JSON}")
    logger.info(f"HTML viewer: {OUTPUT_HTML}")
    logger.info("=" * 80)

    return str(OUTPUT_HTML)


# ============================================================================
# HTML COMPARISON VIEWER GENERATOR
# ============================================================================

def generate_comparison_html(results: List[Dict[str, Any]]):
    """Generate interactive HTML comparison viewer."""

    html = []

    # HTML header
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Comparison: With vs Without Preprocessing</title>
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
            max-width: 1600px;
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
            margin-bottom: 8px;
        }

        .preprocessing-info {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 15px;
            border-radius: 4px;
        }

        .preprocessing-info h3 {
            font-size: 14px;
            color: #4a5568;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .preprocessing-info ul {
            list-style: none;
            padding-left: 0;
        }

        .preprocessing-info li {
            color: #718096;
            font-size: 14px;
            padding: 4px 0;
        }

        .preprocessing-info li::before {
            content: "✓ ";
            color: #48bb78;
            font-weight: bold;
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
        }

        .result-header {
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }

        .result-header h2 {
            font-size: 20px;
            color: #2d3748;
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: 400px 1fr 1fr;
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

        .ocr-section {
            min-height: 300px;
        }

        .section-header {
            font-size: 16px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .without-preprocessing .section-header {
            background: #fff5f5;
            border-left: 4px solid #f56565;
        }

        .with-preprocessing .section-header {
            background: #f0fdf4;
            border-left: 4px solid #48bb78;
        }

        .text-label {
            font-size: 13px;
            font-weight: 600;
            color: #4a5568;
            margin: 15px 0 8px 0;
        }

        .extracted-text {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #2d3748;
            white-space: pre-wrap;
            word-wrap: break-word;
            min-height: 150px;
            max-height: 400px;
            overflow-y: auto;
        }

        .plain-text {
            background: #fffbeb;
            border-color: #fbbf24;
        }

        .metadata {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
        }

        .metadata-item {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
        }

        .metadata-item .label {
            color: #718096;
        }

        .metadata-item .value {
            font-weight: 600;
            color: #2d3748;
        }

        .copy-button {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 8px;
        }

        .copy-button:hover {
            background: #5a67d8;
        }

        @media (max-width: 1400px) {
            .comparison-grid {
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
            <h1>🔬 OCR Comparison Test Results</h1>
            <p>Comparing OpenAI GPT-4o Vision OCR performance with and without preprocessing</p>
            <p>Testing on 5 frames from data/pics_to_test_OCR</p>

            <div class="preprocessing-info">
                <h3>Preprocessing Methods Applied:</h3>
                <ul>
                    <li><strong>Upscaling:</strong> Target height of 800px (maintains aspect ratio)</li>
                    <li><strong>Contrast Enhancement:</strong> CLAHE (Contrast Limited Adaptive Histogram Equalization)</li>
                    <li><strong>Denoising:</strong> Fast Non-Local Means Denoising (h=10)</li>
                </ul>
                <h3 style="margin-top: 10px;">Post-Processing:</h3>
                <ul>
                    <li><strong>LaTeX to Plain Text:</strong> Conversion for speech synthesis (TTS-ready)</li>
                </ul>
            </div>
        </div>
""")

    # Calculate statistics
    total_frames = len(results)
    total_without = sum(r['without_preprocessing']['char_count'] for r in results)
    total_with = sum(r['with_preprocessing']['char_count'] for r in results)
    avg_time_without = sum(r['without_preprocessing']['processing_time'] for r in results) / total_frames if results else 0
    avg_time_with = sum(r['with_preprocessing']['processing_time'] for r in results) / total_frames if results else 0

    # Stats cards
    diff_color = '#48bb78' if total_with > total_without else '#f56565'
    html.append(f"""
        <div class="stats">
            <div class="stat-card">
                <h3>Total Frames</h3>
                <div class="value">{total_frames}</div>
            </div>
            <div class="stat-card">
                <h3>Chars Without Prep</h3>
                <div class="value" style="color: #f56565;">{total_without:,}</div>
            </div>
            <div class="stat-card">
                <h3>Chars With Prep</h3>
                <div class="value" style="color: #48bb78;">{total_with:,}</div>
            </div>
            <div class="stat-card">
                <h3>Difference</h3>
                <div class="value" style="color: {diff_color};">{total_with - total_without:+,}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Time (No Prep)</h3>
                <div class="value">{avg_time_without:.2f}s</div>
            </div>
            <div class="stat-card">
                <h3>Avg Time (With Prep)</h3>
                <div class="value">{avg_time_with:.2f}s</div>
            </div>
        </div>
""")

    # Results grid
    html.append('<div class="results-grid">')

    for result in results:
        # Convert path to relative for browser
        img_path = result['path'].replace('\\', '/').replace('data/', '')

        without = result['without_preprocessing']
        with_prep = result['with_preprocessing']

        html.append(f"""
            <div class="result-card">
                <div class="result-header">
                    <h2>Frame {result['frame_id']}: {result['filename']}</h2>
                </div>

                <div class="comparison-grid">
                    <!-- Image Section -->
                    <div class="image-section">
                        <div class="image-container">
                            <img src="{img_path}" alt="{result['filename']}">
                            <div class="image-info">
                                {result['filename']}
                            </div>
                        </div>
                    </div>

                    <!-- Without Preprocessing -->
                    <div class="ocr-section without-preprocessing">
                        <div class="section-header">
                            <span>❌ Without Preprocessing</span>
                            <span>{without['char_count']} chars</span>
                        </div>

                        <div class="text-label">LaTeX Output:</div>
                        <div class="extracted-text" id="latex-without-{result['frame_id']}">{without['text'] if without['text'] else '(No text extracted)'}</div>
                        {'<button class="copy-button" onclick="copyText(' + f"'latex-without-{result['frame_id']}'" + ')">Copy LaTeX</button>' if without['text'] else ''}

                        <div class="text-label">Plain Text (Speech-Ready):</div>
                        <div class="extracted-text plain-text" id="plain-without-{result['frame_id']}">{without['plain_text'] if without['plain_text'] else '(No plain text)'}</div>
                        {'<button class="copy-button" onclick="copyText(' + f"'plain-without-{result['frame_id']}'" + ')">Copy Plain Text</button>' if without['plain_text'] else ''}

                        <div class="metadata">
                            <div class="metadata-item">
                                <span class="label">Processing Time:</span>
                                <span class="value">{without['processing_time']}s</span>
                            </div>
                            <div class="metadata-item">
                                <span class="label">Method:</span>
                                <span class="value">{without['method']}</span>
                            </div>
                        </div>
                    </div>

                    <!-- With Preprocessing -->
                    <div class="ocr-section with-preprocessing">
                        <div class="section-header">
                            <span>✅ With Preprocessing</span>
                            <span>{with_prep['char_count']} chars</span>
                        </div>

                        <div class="text-label">LaTeX Output:</div>
                        <div class="extracted-text" id="latex-with-{result['frame_id']}">{with_prep['text'] if with_prep['text'] else '(No text extracted)'}</div>
                        {'<button class="copy-button" onclick="copyText(' + f"'latex-with-{result['frame_id']}'" + ')">Copy LaTeX</button>' if with_prep['text'] else ''}

                        <div class="text-label">Plain Text (Speech-Ready):</div>
                        <div class="extracted-text plain-text" id="plain-with-{result['frame_id']}">{with_prep['plain_text'] if with_prep['plain_text'] else '(No plain text)'}</div>
                        {'<button class="copy-button" onclick="copyText(' + f"'plain-with-{result['frame_id']}'" + ')">Copy Plain Text</button>' if with_prep['plain_text'] else ''}

                        <div class="metadata">
                            <div class="metadata-item">
                                <span class="label">Processing Time:</span>
                                <span class="value">{with_prep['processing_time']}s</span>
                            </div>
                            <div class="metadata-item">
                                <span class="label">Method:</span>
                                <span class="value">{with_prep['method']}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """)

    html.append('</div>')  # Close results-grid

    # JavaScript
    html.append("""
        <script>
            function copyText(elementId) {
                const textElement = document.getElementById(elementId);
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

    logger.info(f"Comparison HTML viewer generated: {OUTPUT_HTML}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    html_path = run_comparison_test()

    # Open in browser
    if html_path:
        import subprocess
        logger.info(f"\nOpening comparison viewer in browser...")
        subprocess.run(["start", "", html_path], shell=True)
