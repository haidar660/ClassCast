"""
Minimal OCR-only test (no audio, no fusion, just frame extraction + OCR).
"""
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_utils import setup_logger
from utils.paths import ensure_data_directories, get_file_prefix, INPUT_VIDEO_DIR
from visual_pipeline.frame_extractor import extract_frames
from visual_pipeline.ocr_layout_aware import perform_ocr_on_frames  # Or use ocr_tesseract

logger = setup_logger(__name__)

def test_ocr_only(video_path: Path, max_frames: int = 10):
    """Test OCR on video frames."""
    logger.info("=" * 60)
    logger.info("OCR-ONLY TEST")
    logger.info("=" * 60)
    
    prefix = get_file_prefix(video_path.name)
    
    # Step 1: Extract frames
    logger.info(f"Extracting frames from: {video_path}")
    frames_metadata = extract_frames(video_path, prefix)
    frames_metadata = frames_metadata[:max_frames]  # Limit frames
    logger.info(f"Extracted {len(frames_metadata)} frames")
    
    # Step 2: Run OCR
    logger.info("Running OCR on frames...")
    ocr_results = perform_ocr_on_frames(frames_metadata)
    
    # Step 3: Save results
    output_path = Path(f"data/ocr/{prefix}_ocr_test.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")
    
    # Print sample results
    logger.info("\n" + "=" * 60)
    logger.info("SAMPLE RESULTS (First 3 frames):")
    logger.info("=" * 60)
    for i, result in enumerate(ocr_results[:3], 1):
        logger.info(f"\nFrame {i}: {result['frame_id']}")
        logger.info(f"Timestamp: {result['timestamp']:.1f}s")
        if 'confidence' in result:
            logger.info(f"Confidence: {result['confidence']*100:.1f}%")
        logger.info(f"Text: {result['text'][:200] if result['text'] else '(no text)'}")
        logger.info("-" * 60)

if __name__ == "__main__":
    ensure_data_directories()
    
    # Get video from command line or use default
    video_filename = sys.argv[1] if len(sys.argv) > 1 else "lecture_video_math.mp4"
    video_path = INPUT_VIDEO_DIR / video_filename
    
    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        logger.info(f"Place your video in: {INPUT_VIDEO_DIR}")
        sys.exit(1)
    
    try:
        test_ocr_only(video_path, max_frames=10)
        print("\n✅ SUCCESS! Check data/ocr/ for results.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)