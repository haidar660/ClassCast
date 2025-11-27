"""
Complete Fusion Pipeline Test Script
Downloads YouTube video, extracts frames, runs OCR, performs ASR, and fuses everything.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from frame_extraction.extract_frames import extract_frames
from ocr.visual_pipeline.ocr_openai import perform_ocr_on_frames
from fusion.fusion_engine.fusion_controller import FusionController
from fusion.models.data_models import TranscriptSegment, FrameInfo

# Load environment variables
load_dotenv()


def download_youtube_video(url: str, output_path: Path, duration: int = 20) -> Path:
    """
    Download the first N seconds of a YouTube video.

    Args:
        url: YouTube video URL
        output_path: Path to save the video
        duration: Duration in seconds to download

    Returns:
        Path to downloaded video
    """
    print(f"\n{'='*80}")
    print(f"DOWNLOADING VIDEO")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"Duration: {duration} seconds")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download using yt-dlp with time limit
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]",
        "--download-sections", f"*0-{duration}",
        "-o", str(output_path),
        url
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Video downloaded: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e.stderr}")
        raise


def extract_audio_with_assemblyai(video_path: Path) -> List[TranscriptSegment]:
    """
    Extract audio and transcribe using AssemblyAI.

    Args:
        video_path: Path to video file

    Returns:
        List of TranscriptSegment objects
    """
    print(f"\n{'='*80}")
    print(f"EXTRACTING AUDIO & TRANSCRIBING")
    print(f"{'='*80}")

    import assemblyai as aai

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise ValueError("ASSEMBLYAI_API_KEY not found in .env file")

    aai.settings.api_key = api_key

    print("Uploading video to AssemblyAI...")
    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.nano
    )

    transcript = transcriber.transcribe(str(video_path), config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"Transcription failed: {transcript.error}")

    print(f"✅ Transcription complete")
    print(f"   Total words: {len(transcript.words) if transcript.words else 0}")

    # Convert to TranscriptSegment objects
    segments = []
    if transcript.words:
        # Group words into segments of roughly 5-10 seconds
        current_segment = []
        segment_start = None

        for word in transcript.words:
            if segment_start is None:
                segment_start = word.start / 1000.0  # Convert ms to seconds

            current_segment.append(word.text)

            # Create segment every ~7 seconds or at end
            if (word.end / 1000.0 - segment_start) >= 7.0 or word == transcript.words[-1]:
                segment_end = word.end / 1000.0
                segment_text = " ".join(current_segment)

                segments.append(TranscriptSegment(
                    start=segment_start,
                    end=segment_end,
                    text=segment_text
                ))

                current_segment = []
                segment_start = None

    print(f"   Created {len(segments)} transcript segments")
    return segments


def run_pipeline(youtube_url: str, duration: int = 20) -> Dict[str, Any]:
    """
    Run the complete fusion pipeline.

    Args:
        youtube_url: YouTube video URL
        duration: Duration in seconds to process

    Returns:
        Dictionary with all pipeline results
    """
    # Setup directories
    base_dir = Path(__file__).parent
    test_dir = base_dir / "test_output"
    test_dir.mkdir(exist_ok=True)

    video_path = test_dir / "test_video.mp4"
    frames_dir = test_dir / "frames"

    # Step 1: Download video
    print(f"\n{'='*80}")
    print(f"STEP 1: DOWNLOAD VIDEO")
    print(f"{'='*80}")
    download_youtube_video(youtube_url, video_path, duration)

    # Step 2: Extract frames (every 2 seconds)
    print(f"\n{'='*80}")
    print(f"STEP 2: EXTRACT FRAMES")
    print(f"{'='*80}")
    frames_dir.mkdir(exist_ok=True)
    frames_metadata = extract_frames(
        video_path=video_path,
        output_dir=frames_dir,
        interval=2.0,
        quality=95,
        start_time=0,
        end_time=duration
    )

    # Step 3: Perform OCR on frames
    print(f"\n{'='*80}")
    print(f"STEP 3: OCR ON FRAMES")
    print(f"{'='*80}")
    ocr_results = perform_ocr_on_frames(frames_metadata, model="gpt-4o-mini")

    # Save OCR results
    ocr_output_path = test_dir / "ocr_results.json"
    with open(ocr_output_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2)
    print(f"💾 OCR results saved to: {ocr_output_path}")

    # Step 4: Extract audio and transcribe
    print(f"\n{'='*80}")
    print(f"STEP 4: AUDIO TRANSCRIPTION")
    print(f"{'='*80}")
    segments = extract_audio_with_assemblyai(video_path)

    # Save transcript
    transcript_path = test_dir / "transcript.json"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump({
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text
                }
                for seg in segments
            ]
        }, f, indent=2)
    print(f"💾 Transcript saved to: {transcript_path}")

    # Step 5: Pair segments with frames
    print(f"\n{'='*80}")
    print(f"STEP 5: PAIRING SEGMENTS WITH FRAMES")
    print(f"{'='*80}")

    # Convert frames to FrameInfo objects
    frame_infos = [
        FrameInfo(
            time=frame['timestamp'],
            path=frame['path']
        )
        for frame in frames_metadata
    ]

    # Match each segment with closest frame
    from fusion.models.data_models import find_closest_frame
    segment_to_frame = find_closest_frame(segments, frame_infos)

    # Create aligned frames list (one per segment)
    aligned_frames = [segment_to_frame[i] for i in range(len(segments))]

    # Extract board elements from OCR results
    board_elements = []
    for seg in segments:
        seg_mid = seg.midpoint
        # Find closest OCR result
        closest_ocr = min(ocr_results, key=lambda x: abs(x['timestamp'] - seg_mid))
        board_text = closest_ocr.get('text', '').strip()
        board_elements.append([board_text] if board_text else [])

    print(f"✅ Paired {len(segments)} segments with {len(aligned_frames)} frames")

    # Step 6: Run fusion
    print(f"\n{'='*80}")
    print(f"STEP 6: FUSION")
    print(f"{'='*80}")

    controller = FusionController(batch_size=4)
    fused_sentences = controller.fuse_pipeline(
        segments=segments,
        frames=aligned_frames,
        board_elements=board_elements
    )

    # Save fusion results
    fusion_path = test_dir / "fusion_results.txt"
    with open(fusion_path, 'w', encoding='utf-8') as f:
        for idx, (seg, fused) in enumerate(zip(segments, fused_sentences), 1):
            f.write(f"[Segment {idx}] {seg.start:.1f}s - {seg.end:.1f}s\n")
            f.write(f"Original: {seg.text}\n")
            f.write(f"Fused: {fused}\n\n")

    print(f"💾 Fusion results saved to: {fusion_path}")

    # Step 7: Prepare results
    results = {
        "video_url": youtube_url,
        "duration": duration,
        "video_path": str(video_path),
        "frames_dir": str(frames_dir),
        "total_frames": len(frames_metadata),
        "total_segments": len(segments),
        "segments": [
            {
                "id": i + 1,
                "start": seg.start,
                "end": seg.end,
                "original_text": seg.text,
                "fused_text": fused,
                "frame_path": aligned_frames[i].path,
                "frame_time": aligned_frames[i].time,
                "board_text": board_elements[i][0] if board_elements[i] else ""
            }
            for i, (seg, fused) in enumerate(zip(segments, fused_sentences))
        ]
    }

    # Save complete results
    results_path = test_dir / "complete_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"PIPELINE COMPLETE!")
    print(f"{'='*80}")
    print(f"✅ Results saved to: {test_dir}")

    return results


def main():
    """Main entry point."""
    print(f"\n{'='*80}")
    print(f"CLASSCAST FUSION PIPELINE TEST")
    print(f"{'='*80}")

    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        sys.exit(1)

    if not os.getenv("ASSEMBLYAI_API_KEY"):
        print("❌ ERROR: ASSEMBLYAI_API_KEY not found in .env file")
        sys.exit(1)

    print("✅ API keys found")

    # YouTube URL
    youtube_url = "https://youtu.be/i4g1krYYIFE?si=57WFTX9sPFILmvR6"
    duration = 20  # First 20 seconds

    try:
        # Check if assemblyai is installed
        try:
            import assemblyai
        except ImportError:
            print("Installing assemblyai...")
            subprocess.run([sys.executable, "-m", "pip", "install", "assemblyai"], check=True)
            import assemblyai

        # Run pipeline
        results = run_pipeline(youtube_url, duration)

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Video URL: {youtube_url}")
        print(f"Duration: {duration} seconds")
        print(f"Frames extracted: {results['total_frames']}")
        print(f"Transcript segments: {results['total_segments']}")
        print(f"\nFirst 3 fused segments:")
        print(f"{'-'*80}")

        for seg in results['segments'][:3]:
            print(f"\n[{seg['id']}] {seg['start']:.1f}s - {seg['end']:.1f}s")
            print(f"  Original: {seg['original_text']}")
            print(f"  Fused:    {seg['fused_text']}")
            if seg['board_text']:
                print(f"  Board:    {seg['board_text'][:100]}...")

        return results

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    results = main()
