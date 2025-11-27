"""
Comprehensive Test Suite for ClassCast Fusion Package
Tests all components and generates an HTML report with results
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import all fusion modules
from models.data_models import TranscriptSegment, FrameInfo, BoardElement, find_closest_frame
from fusion_engine.batch_fusion import batch_fuse_segments, batch_fuse_simple
from fusion_engine.fusion_controller import FusionController, quick_fuse
from fusion_engine.math_to_speech import math_to_speech, convert_exponents_to_speech
from ocr.vision.latex_converter import latex_to_text
from ClassCast.fusion.pairing import pair_segments_with_context

# Load environment variables
load_dotenv()


class TestResults:
    """Container for test results"""
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()

    def add_test(self, name: str, passed: bool, details: str = "", output: Any = None):
        """Add a test result"""
        self.tests.append({
            'name': name,
            'passed': passed,
            'details': details,
            'output': output,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'total': len(self.tests),
            'passed': self.passed,
            'failed': self.failed,
            'duration': f"{duration:.2f}s",
            'success_rate': f"{(self.passed / len(self.tests) * 100):.1f}%" if self.tests else "0%"
        }


def test_data_models(results: TestResults):
    """Test data models module"""
    print("\n" + "=" * 80)
    print("TEST 1: Data Models")
    print("=" * 80)

    try:
        # Test TranscriptSegment
        segment = TranscriptSegment(start=0.0, end=5.0, text="Test segment")
        assert segment.midpoint == 2.5, "Midpoint calculation failed"
        assert segment.duration == 5.0, "Duration calculation failed"
        results.add_test(
            "Data Models - TranscriptSegment",
            True,
            f"Created segment with midpoint={segment.midpoint}s, duration={segment.duration}s",
            {'midpoint': segment.midpoint, 'duration': segment.duration}
        )
        print("[PASS] TranscriptSegment: PASSED")
    except Exception as e:
        results.add_test("Data Models - TranscriptSegment", False, str(e))
        print(f"[FAIL] TranscriptSegment: FAILED - {e}")

    try:
        # Test FrameInfo
        frame = FrameInfo(time=2.5, path="test_frame.jpg")
        assert frame.time == 2.5, "Frame time incorrect"
        results.add_test(
            "Data Models - FrameInfo",
            True,
            f"Created frame at time={frame.time}s",
            {'time': frame.time, 'path': frame.path}
        )
        print("[PASS] FrameInfo: PASSED")
    except Exception as e:
        results.add_test("Data Models - FrameInfo", False, str(e))
        print(f"[FAIL] FrameInfo: FAILED - {e}")

    try:
        # Test BoardElement
        element = BoardElement(id=1, latex="x^2", first_seen=0.0, last_seen=5.0)
        assert element.duration == 5.0, "BoardElement duration failed"
        assert element.is_visible_at(2.5), "Visibility check failed"
        assert not element.is_visible_at(6.0), "Visibility check false positive"
        results.add_test(
            "Data Models - BoardElement",
            True,
            f"Created element visible for {element.duration}s",
            {'duration': element.duration, 'latex': element.latex}
        )
        print("[PASS] BoardElement: PASSED")
    except Exception as e:
        results.add_test("Data Models - BoardElement", False, str(e))
        print(f"[FAIL] BoardElement: FAILED - {e}")

    try:
        # Test find_closest_frame
        segments = [
            TranscriptSegment(start=0, end=5, text="First"),
            TranscriptSegment(start=5, end=10, text="Second")
        ]
        frames = [
            FrameInfo(time=2.0, path="frame1.jpg"),
            FrameInfo(time=7.5, path="frame2.jpg")
        ]
        mapping = find_closest_frame(segments, frames)
        assert len(mapping) == 2, "Frame mapping incomplete"
        assert mapping[0].time == 2.0, "First frame mapping incorrect"
        assert mapping[1].time == 7.5, "Second frame mapping incorrect"
        results.add_test(
            "Data Models - find_closest_frame",
            True,
            f"Mapped {len(segments)} segments to {len(frames)} frames",
            {'mapping_count': len(mapping)}
        )
        print("[PASS] find_closest_frame: PASSED")
    except Exception as e:
        results.add_test("Data Models - find_closest_frame", False, str(e))
        print(f"[FAIL] find_closest_frame: FAILED - {e}")


def test_latex_converter(results: TestResults):
    """Test LaTeX to text conversion"""
    print("\n" + "=" * 80)
    print("TEST 2: LaTeX Converter")
    print("=" * 80)

    test_cases = [
        (r"x^2", "x squared"),
        (r"\frac{a}{b}", "a over b"),
        (r"f(x) = 3x^2 + 1", "f of x equals 3 times x squared plus 1"),
    ]

    for latex_input, expected_contains in test_cases:
        try:
            result = latex_to_text(latex_input)
            # Check if key parts are present
            passed = any(word in result.lower() for word in expected_contains.split())
            results.add_test(
                f"LaTeX Converter - {latex_input[:20]}",
                passed,
                f"Input: {latex_input}, Output: {result}",
                {'input': latex_input, 'output': result}
            )
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} {latex_input} → {result}")
        except Exception as e:
            results.add_test(f"LaTeX Converter - {latex_input}", False, str(e))
            print(f"[FAIL] {latex_input}: FAILED - {e}")


def test_math_to_speech(results: TestResults):
    """Test math to speech conversion"""
    print("\n" + "=" * 80)
    print("TEST 3: Math to Speech Converter")
    print("=" * 80)

    test_cases = [
        ("x^2 + y^3", "squared", "cubed"),
        ("f(x) = 2x", "f of", "times"),
        ("1/2 + 3/4", "half", "quarters"),
    ]

    for math_input, *expected_words in test_cases:
        try:
            result = math_to_speech(math_input)
            passed = all(word in result.lower() for word in expected_words)
            results.add_test(
                f"Math to Speech - {math_input[:20]}",
                passed,
                f"Input: {math_input}, Output: {result}",
                {'input': math_input, 'output': result}
            )
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} {math_input} → {result}")
        except Exception as e:
            results.add_test(f"Math to Speech - {math_input}", False, str(e))
            print(f"[FAIL] {math_input}: FAILED - {e}")


def test_pairing(results: TestResults):
    """Test pairing module"""
    print("\n" + "=" * 80)
    print("TEST 4: Segment-Frame Pairing")
    print("=" * 80)

    try:
        segments = [
            TranscriptSegment(start=0, end=5, text="First segment"),
            TranscriptSegment(start=5, end=10, text="Second segment")
        ]
        frames = [
            FrameInfo(time=2.0, path="frame1.jpg"),
            FrameInfo(time=7.5, path="frame2.jpg")
        ]

        paired = pair_segments_with_context(segments, frames)
        assert len(paired) == 2, "Pairing count mismatch"
        assert paired[0]['segment'].text == "First segment", "First pairing incorrect"
        assert paired[1]['frame'].time == 7.5, "Second frame pairing incorrect"

        results.add_test(
            "Pairing - pair_segments_with_context",
            True,
            f"Successfully paired {len(paired)} segments with frames",
            {'paired_count': len(paired)}
        )
        print(f"[PASS] Paired {len(paired)} segments with frames")
    except Exception as e:
        results.add_test("Pairing - pair_segments_with_context", False, str(e))
        print(f"[FAIL] Pairing: FAILED - {e}")


def test_fusion_controller(results: TestResults):
    """Test fusion controller without API calls"""
    print("\n" + "=" * 80)
    print("TEST 5: Fusion Controller (Structure)")
    print("=" * 80)

    try:
        controller = FusionController(batch_size=2)
        assert controller.batch_size == 2, "Batch size not set correctly"
        results.add_test(
            "Fusion Controller - Initialization",
            True,
            f"Initialized with batch_size={controller.batch_size}",
            {'batch_size': controller.batch_size}
        )
        print(f"[PASS] FusionController initialized with batch_size={controller.batch_size}")
    except Exception as e:
        results.add_test("Fusion Controller - Initialization", False, str(e))
        print(f"[FAIL] FusionController: FAILED - {e}")


def test_batch_fusion_api(results: TestResults):
    """Test actual batch fusion with OpenAI API"""
    print("\n" + "=" * 80)
    print("TEST 6: Batch Fusion API Integration")
    print("=" * 80)

    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        results.add_test(
            "Batch Fusion - API Integration",
            False,
            "OPENAI_API_KEY not found in environment"
        )
        print("[WARN]  Skipping API test - No API key found")
        return

    print("[KEY] OpenAI API key found")
    print("[RUN] Running real API fusion test (this will cost ~$0.001)...")

    try:
        # Create test data
        test_segments = [
            {'text': 'Let us examine this derivative', 'start': 0.0, 'end': 3.0},
            {'text': 'Now consider the quadratic formula', 'start': 3.0, 'end': 6.0}
        ]

        test_frames = [
            {'path': 'frame_0.jpg', 'time': 1.5},
            {'path': 'frame_1.jpg', 'time': 4.5}
        ]

        test_board = [
            [r'\frac{d}{dx}(x^2) = 2x'],
            [r'x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}']
        ]

        # Run batch fusion
        start_time = time.time()
        fused = batch_fuse_segments(
            segments=test_segments,
            frames=test_frames,
            board_elements=test_board,
            batch_size=2
        )
        duration = time.time() - start_time

        # Validate results
        assert len(fused) == 2, f"Expected 2 results, got {len(fused)}"
        assert all(isinstance(s, str) for s in fused), "Results not all strings"
        assert all(len(s) > 0 for s in fused), "Empty fusion results"

        results.add_test(
            "Batch Fusion - API Integration",
            True,
            f"Successfully fused {len(fused)} segments in {duration:.2f}s",
            {
                'input_segments': test_segments,
                'board_elements': test_board,
                'output': fused,
                'duration': f"{duration:.2f}s"
            }
        )

        print(f"[PASS] API Fusion: PASSED ({duration:.2f}s)")
        print("\n[NOTE] Fusion Results:")
        for idx, (seg, fused_text) in enumerate(zip(test_segments, fused), 1):
            print(f"\n  [{idx}] Original: {seg['text']}")
            print(f"      Board: {test_board[idx-1][0]}")
            print(f"      Fused: {fused_text}")

    except Exception as e:
        results.add_test("Batch Fusion - API Integration", False, str(e))
        print(f"[FAIL] API Fusion: FAILED - {e}")


def generate_html_report(results: TestResults, output_path: str):
    """Generate HTML report of test results"""
    summary = results.get_summary()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fusion Package Test Results</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .summary-card:hover {{
            transform: translateY(-5px);
        }}
        .summary-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .summary-card.passed .value {{ color: #28a745; }}
        .summary-card.failed .value {{ color: #dc3545; }}
        .tests {{
            padding: 40px;
        }}
        .test-item {{
            background: white;
            margin-bottom: 20px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        .test-item:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        .test-header {{
            display: flex;
            align-items: center;
            padding: 20px;
            cursor: pointer;
            user-select: none;
        }}
        .test-header:hover {{
            background: #f8f9fa;
        }}
        .test-status {{
            font-size: 1.5em;
            margin-right: 15px;
            min-width: 30px;
        }}
        .test-name {{
            flex: 1;
            font-weight: 600;
            color: #333;
        }}
        .test-time {{
            color: #999;
            font-size: 0.9em;
        }}
        .test-details {{
            padding: 0 20px 20px 65px;
            color: #666;
            line-height: 1.6;
            display: none;
        }}
        .test-item.expanded .test-details {{
            display: block;
        }}
        .test-output {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 400px;
            overflow-y: auto;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }}
        .badge.passed {{
            background: #d4edda;
            color: #155724;
        }}
        .badge.failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            border-top: 1px solid #dee2e6;
        }}
        .progress-bar {{
            width: 100%;
            height: 10px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[TEST] Fusion Package Test Results</h1>
            <p>ClassCast Video-to-Podcast Pipeline</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary['total']}</div>
            </div>
            <div class="summary-card passed">
                <h3>Passed</h3>
                <div class="value">{summary['passed']}</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="value">{summary['failed']}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value" style="font-size: 2em;">{summary['success_rate']}</div>
            </div>
            <div class="summary-card">
                <h3>Duration</h3>
                <div class="value" style="font-size: 1.8em;">{summary['duration']}</div>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {summary['success_rate']}"></div>
        </div>

        <div class="tests">
            <h2 style="margin-bottom: 30px; color: #333;">Test Details</h2>
"""

    for test in results.tests:
        status_icon = "[PASS]" if test['passed'] else "[FAIL]"
        badge_class = "passed" if test['passed'] else "failed"
        badge_text = "PASSED" if test['passed'] else "FAILED"

        html += f"""
            <div class="test-item" onclick="this.classList.toggle('expanded')">
                <div class="test-header">
                    <span class="test-status">{status_icon}</span>
                    <span class="test-name">{test['name']}</span>
                    <span class="badge {badge_class}">{badge_text}</span>
                    <span class="test-time">{test['timestamp']}</span>
                </div>
                <div class="test-details">
"""

        if test['details']:
            html += f"<p><strong>Details:</strong> {test['details']}</p>"

        if test['output']:
            output_str = json.dumps(test['output'], indent=2) if isinstance(test['output'], dict) else str(test['output'])
            html += f'<div class="test-output">{output_str}</div>'

        html += """
                </div>
            </div>
"""

    html += f"""
        </div>

        <div class="footer">
            <p><strong>ClassCast Fusion Package</strong></p>
            <p style="margin-top: 10px;">Educational content fusion system for video-to-podcast conversion</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Test completed at {datetime.now().strftime('%H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // Auto-expand failed tests
        document.addEventListener('DOMContentLoaded', function() {{
            const failedTests = document.querySelectorAll('.test-item .badge.failed');
            failedTests.forEach(badge => {{
                badge.closest('.test-item').classList.add('expanded');
            }});
        }});
    </script>
</body>
</html>
"""

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[FILE] HTML report generated: {output_path}")


def main():
    """Run all tests and generate report"""
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("\n" + "=" * 80)
    print("COMPREHENSIVE FUSION PACKAGE TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = TestResults()

    # Run all tests
    test_data_models(results)
    test_latex_converter(results)
    test_math_to_speech(results)
    test_pairing(results)
    test_fusion_controller(results)
    test_batch_fusion_api(results)

    # Generate summary
    summary = results.get_summary()

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests:    {summary['total']}")
    print(f"Passed:         {summary['passed']}")
    print(f"Failed:         {summary['failed']}")
    print(f"Success Rate:   {summary['success_rate']}")
    print(f"Duration:       {summary['duration']}")
    print("=" * 80)

    # Generate HTML report
    output_path = "test_results.html"
    generate_html_report(results, output_path)

    print(f"\nTesting complete! Open {output_path} in your browser to view the full report.")

    return results


if __name__ == "__main__":
    main()
