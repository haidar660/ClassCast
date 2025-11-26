"""
Test script to verify frame extraction package installation.

Run this script to check if all dependencies are installed correctly.
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def test_python_version():
    """Check Python version."""
    print("Testing Python version...")
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ Python {version.major}.{version.minor} detected")
        print(f"  ✗ Python 3.8 or higher required")
        return False

    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def test_opencv():
    """Check OpenCV installation."""
    print("\nTesting OpenCV (cv2)...")

    try:
        import cv2
        version = cv2.__version__
        print(f"  ✓ OpenCV {version} installed")

        # Test basic functionality
        print("  Testing video capture capability...")
        cap = cv2.VideoCapture()
        print("  ✓ VideoCapture available")

        return True

    except ImportError:
        print("  ✗ OpenCV not installed")
        print("  ✗ Run: pip install opencv-python")
        return False
    except Exception as e:
        print(f"  ⚠ OpenCV installed but error occurred: {e}")
        return False


def test_json():
    """Check JSON module (built-in)."""
    print("\nTesting JSON module...")

    try:
        import json
        print("  ✓ JSON module available")
        return True
    except ImportError:
        print("  ✗ JSON module not available (this shouldn't happen)")
        return False


def test_pathlib():
    """Check pathlib module (built-in)."""
    print("\nTesting pathlib module...")

    try:
        from pathlib import Path
        print("  ✓ pathlib module available")
        return True
    except ImportError:
        print("  ✗ pathlib module not available (this shouldn't happen)")
        return False


def test_extract_frames_script():
    """Check if extract_frames.py exists."""
    print("\nTesting extract_frames.py script...")

    script_path = Path("extract_frames.py")

    if not script_path.exists():
        print(f"  ✗ extract_frames.py not found in current directory")
        print(f"  ✗ Make sure you're running this from the frame_extraction_package directory")
        return False

    print(f"  ✓ extract_frames.py found")

    # Try to import it
    try:
        import extract_frames
        print(f"  ✓ extract_frames.py can be imported")
        return True
    except Exception as e:
        print(f"  ⚠ extract_frames.py found but import failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("ClassCast Frame Extraction - Installation Test")
    print("=" * 70)

    tests = [
        ("Python Version", test_python_version),
        ("OpenCV", test_opencv),
        ("JSON", test_json),
        ("pathlib", test_pathlib),
        ("Extract Script", test_extract_frames_script),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  ✗ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print("=" * 70)

    if passed_count == total_count:
        print(f"\n✓ All tests passed! ({passed_count}/{total_count})")
        print("\nYou're ready to extract frames!")
        print("\nTry: python extract_frames.py --help")
        return True
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
        print("\nPlease fix the issues above before using the tool.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
