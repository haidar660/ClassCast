"""
Run OCR on 20 frames and calculate average confidence.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_utils import setup_logger
from visual_pipeline.ocr_layout_aware import perform_ocr_on_frames

logger = setup_logger(__name__)

def run_ocr_test(num_frames=20):
    """Run OCR on first N frames from lecture_video_math."""

    # Build frame metadata for first 20 frames
    frames_dir = Path("data/frames/lecture_video_math")

    if not frames_dir.exists():
        logger.error(f"Frames directory not found: {frames_dir}")
        return

    frames_metadata = []
    for i in range(num_frames):
        frame_id = f"frame_{i:04d}"
        frame_path = frames_dir / f"{frame_id}.jpg"

        if not frame_path.exists():
            logger.warning(f"Frame not found: {frame_path}")
            continue

        # Approximate timestamp (2 seconds per frame based on config)
        timestamp = i * 2.0

        frames_metadata.append({
            "frame_id": frame_id,
            "timestamp": timestamp,
            "path": str(frame_path)
        })

    logger.info(f"Processing {len(frames_metadata)} frames with layout-aware OCR...")

    # Run OCR
    ocr_results = perform_ocr_on_frames(frames_metadata)

    # Calculate statistics
    total_frames = len(ocr_results)
    frames_with_text = sum(1 for r in ocr_results if r.get('text', '').strip())

    # Calculate average confidence
    confidences = [r.get('confidence', 0.0) for r in ocr_results]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # Calculate average confidence for frames with text only
    text_confidences = [r.get('confidence', 0.0) for r in ocr_results if r.get('text', '').strip()]
    avg_text_confidence = sum(text_confidences) / len(text_confidences) if text_confidences else 0.0

    # Save results
    output_path = Path("data/ocr/lecture_video_math_20frames_test.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2)

    # Print results
    print("\n" + "=" * 70)
    print("OCR RESULTS - 20 FRAMES")
    print("=" * 70)
    print(f"Total frames processed: {total_frames}")
    print(f"Frames with text detected: {frames_with_text}/{total_frames} ({frames_with_text/total_frames*100:.1f}%)")
    print(f"\nAverage confidence (all frames): {avg_confidence*100:.2f}%")
    print(f"Average confidence (text frames only): {avg_text_confidence*100:.2f}%")
    print(f"Min confidence: {min(confidences)*100:.2f}%")
    print(f"Max confidence: {max(confidences)*100:.2f}%")
    print(f"\nResults saved to: {output_path}")
    print("=" * 70)

    # Show sample results
    print("\n📝 SAMPLE RESULTS (First 5 frames):\n")
    for i, result in enumerate(ocr_results[:5], 1):
        print(f"Frame {i}: {result['frame_id']} @ {result['timestamp']:.1f}s")
        print(f"  Confidence: {result.get('confidence', 0)*100:.1f}%")
        text = result.get('text', '').strip()
        if text:
            preview = text[:100] + "..." if len(text) > 100 else text
            print(f"  Text: {preview}")
        else:
            print(f"  Text: (no text detected)")
        print()

    return ocr_results

if __name__ == "__main__":
    run_ocr_test(20)
