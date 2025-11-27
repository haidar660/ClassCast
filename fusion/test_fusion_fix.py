"""
Test the fixed fusion prompt - reuse existing video/frames/transcript
"""
import os
import sys
import io
import json
from pathlib import Path
from dotenv import load_dotenv

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from fusion.fusion_engine.fusion_controller import FusionController
from fusion.models.data_models import TranscriptSegment, FrameInfo, find_closest_frame

load_dotenv()

def test_fusion_fix():
    """Test the fusion with fixed prompt using existing data."""

    print(f"\n{'='*80}")
    print(f"TESTING FIXED FUSION PROMPT")
    print(f"{'='*80}")

    test_dir = Path("test_output")

    # Load existing transcript
    print("\n📄 Loading existing transcript...")
    with open(test_dir / "transcript.json", 'r') as f:
        transcript_data = json.load(f)

    segments = [
        TranscriptSegment(
            start=seg['start'],
            end=seg['end'],
            text=seg['text']
        )
        for seg in transcript_data['segments']
    ]

    print(f"   Loaded {len(segments)} segments")

    # Load existing OCR results
    print("\n🔍 Loading existing OCR results...")
    with open(test_dir / "ocr_results.json", 'r') as f:
        ocr_results = json.load(f)

    print(f"   Loaded {len(ocr_results)} OCR results")

    # Create frame infos
    frame_infos = [
        FrameInfo(
            time=ocr['timestamp'],
            path=ocr['path']
        )
        for ocr in ocr_results
    ]

    # Match segments with frames
    print("\n🔗 Matching segments with frames...")
    segment_to_frame = find_closest_frame(segments, frame_infos)
    aligned_frames = [segment_to_frame[i] for i in range(len(segments))]

    # Extract board elements
    board_elements = []
    for seg in segments:
        seg_mid = seg.midpoint
        closest_ocr = min(ocr_results, key=lambda x: abs(x['timestamp'] - seg_mid))
        board_text = closest_ocr.get('text', '').strip()
        board_elements.append([board_text] if board_text else [])

    print(f"   Paired {len(segments)} segments with frames")

    # Run fusion with FIXED prompt
    print(f"\n{'='*80}")
    print(f"RUNNING FUSION WITH FIXED PROMPT")
    print(f"{'='*80}")

    controller = FusionController(batch_size=4)
    fused_sentences = controller.fuse_pipeline(
        segments=segments,
        frames=aligned_frames,
        board_elements=board_elements
    )

    # Display results
    print(f"\n{'='*80}")
    print(f"COMPARISON: ORIGINAL vs FUSED")
    print(f"{'='*80}")

    for idx, (seg, fused, board) in enumerate(zip(segments, fused_sentences, board_elements), 1):
        print(f"\n[Segment {idx}] {seg.start:.1f}s - {seg.end:.1f}s")
        print(f"  📝 Original:  {seg.text}")
        print(f"  🎯 Fused:     {fused}")
        if board:
            print(f"  📐 Board:     {board[0][:100]}")
        print()

    # Save new results
    output_path = test_dir / "fusion_results_FIXED.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, (seg, fused) in enumerate(zip(segments, fused_sentences), 1):
            f.write(f"[Segment {idx}] {seg.start:.1f}s - {seg.end:.1f}s\n")
            f.write(f"Original: {seg.text}\n")
            f.write(f"Fused: {fused}\n\n")

    print(f"{'='*80}")
    print(f"✅ Results saved to: {output_path}")
    print(f"{'='*80}")

    # Analysis
    print(f"\n{'='*80}")
    print(f"ANALYSIS")
    print(f"{'='*80}")

    for idx, (seg, fused) in enumerate(zip(segments, fused_sentences), 1):
        original = seg.text.lower()
        fused_lower = fused.lower()

        # Check if major words are preserved
        original_words = set(original.split())
        fused_words = set(fused_lower.split())

        preserved = original_words & fused_words
        preservation_rate = len(preserved) / len(original_words) * 100 if original_words else 0

        print(f"\nSegment {idx}:")
        print(f"  Word preservation: {preservation_rate:.1f}%")

        if preservation_rate < 70:
            print(f"  ⚠️  WARNING: Significant paraphrasing detected!")
        elif preservation_rate > 90:
            print(f"  ✅ Excellent preservation!")
        else:
            print(f"  ⚡ Good preservation")

    return fused_sentences


if __name__ == "__main__":
    test_fusion_fix()
