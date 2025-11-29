"""
Complete ClassCast Pipeline with Fixed ASR + TTS
- Sentence-level segmentation (AssemblyAI)
- Fixed fusion (no paraphrasing)
- TTS audio generation
"""
import os
import sys
import io
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import shutil
from dotenv import load_dotenv

# Note: Avoid modifying stdio streams to prevent conflicts with servers/logging.

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from frame_extraction.extract_frames import extract_frames
from audio_pipeline import transcribe_video_to_sentence_segments
from ocr.visual_pipeline.ocr_openai import perform_ocr_on_frames
from fusion.fusion_engine.fusion_controller import FusionController
from fusion.models.data_models import TranscriptSegment, FrameInfo
from fusion.fusion_engine.math_to_speech import merge_speech_and_board_naturally
from fusion.fusion_engine.fusion_inputs import filter_incomplete_segments, build_board_elements
from TTS import generate_tts_audio

# Load environment variables
load_dotenv()


def download_youtube_video(url: str, output_path: Path, duration: int = 20) -> Path:
    """Download the first N seconds of a YouTube video."""
    print(f"\n{'='*80}")
    print(f"STEP 1: DOWNLOAD VIDEO")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"Duration: {duration} seconds")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]",
        "--download-sections", f"*0-{duration}",
        "-o", str(output_path),
        url
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[OK] Video downloaded: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Download failed: {e.stderr}")
        raise


def run_pipeline(
    youtube_url: str,
    duration: Optional[int] = 20,
    *,
    local_video_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the complete fusion pipeline with sentence-level ASR and TTS.

    When ``local_video_path`` is provided, skips YouTube download and uses the given file.
    If a local file is provided, the ``duration`` parameter is ignored and the full file is used.
    """

    print(f"\n{'='*80}")
    print(f"CLASSCAST COMPLETE PIPELINE")
    print(f"NEW: Sentence-level ASR + TTS")
    print(f"{'='*80}")

    # Setup directories
    base_dir = Path(__file__).parent
    test_dir = output_dir if output_dir else (base_dir / "test_output")
    test_dir.mkdir(parents=True, exist_ok=True)

    video_path = test_dir / "downloaded.mp4"
    frames_dir = test_dir / "frames"

    # Step 1: Download video (or use provided local file)
    effective_duration = duration if not local_video_path else None
    if local_video_path:
        print(f"[INFO] Using existing local video: {local_video_path}")
        video_path = Path(local_video_path)
    else:
        download_youtube_video(youtube_url, video_path, effective_duration or 20)

    # Step 2: Extract frames
    print(f"\n{'='*80}")
    print(f"STEP 2: EXTRACT FRAMES")
    print(f"{'='*80}")
    frames_dir.mkdir(exist_ok=True)
    frames_metadata = extract_frames(
        video_path=video_path,
        output_dir=frames_dir,
        interval=3.0,
        quality=95,
        start_time=0,
        end_time=effective_duration
    )

    # Save kept frames list and copies for inspection (frames already deduped in extract_frames)
    kept_dir = test_dir / "frames_kept"
    kept_dir.mkdir(exist_ok=True)
    for f in frames_metadata:
        src = Path(f["path"])
        dst = kept_dir / src.name
        try:
            shutil.copy(src, dst)
        except Exception:
            pass
    kept_list_path = test_dir / "frames_kept.json"
    with open(kept_list_path, "w", encoding="utf-8") as fp:
        json.dump(frames_metadata, fp, indent=2)

    # Step 3: OCR
    print(f"\n{'='*80}")
    print(f"STEP 3: OCR ON FRAMES")
    print(f"{'='*80}")
    ocr_results = perform_ocr_on_frames(frames_metadata, model="gpt-4o-mini")

    ocr_output_path = test_dir / "ocr_results.json"
    with open(ocr_output_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2)
    print(f"[SAVED] OCR results saved to: {ocr_output_path}")

    # Step 4: ASR with sentence-level segmentation (centralized in audio_pipeline)
    print(f"\n{'='*80}")
    print(f"STEP 4: AUDIO TRANSCRIPTION (SENTENCE-LEVEL)")
    print(f"{'='*80}")
    segments = transcribe_video_to_sentence_segments(video_path)

    # Drop obviously incomplete sentence fragments (very short)
    segments = filter_incomplete_segments(segments, min_words=4)

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
    print(f"[SAVED] Transcript saved to: {transcript_path}")

    # Step 5: Pairing
    print(f"\n{'='*80}")
    print(f"STEP 5: PAIRING SEGMENTS WITH FRAMES")
    print(f"{'='*80}")

    frame_infos = [
        FrameInfo(time=frame['timestamp'], path=frame['path'])
        for frame in frames_metadata
    ]

    from fusion.models.data_models import find_closest_frame
    segment_to_frame = find_closest_frame(segments, frame_infos)
    aligned_frames = [segment_to_frame[i] for i in range(len(segments))]

    # Extract board elements
    board_elements = build_board_elements(segments, ocr_results)

    print(f"[OK] Paired {len(segments)} segments with {len(aligned_frames)} frames")

    # Step 6: Fusion (with fixed prompt)
    print(f"\n{'='*80}")
    print(f"STEP 6: FUSION (NO PARAPHRASING)")
    print(f"{'='*80}")

    controller = FusionController(batch_size=4)
    fused_sentences = controller.fuse_pipeline(
        segments=segments,
        frames=aligned_frames,
        board_elements=board_elements
    )

    def _dedup_clauses(text: str) -> str:
        if not isinstance(text, str):
            text = "" if text is None else str(text)
        parts = [p.strip() for p in re.split(r'[.;!?]+', text) if p.strip()]
        cleaned = []
        for p in parts:
            if not cleaned or cleaned[-1].lower() != p.lower():
                cleaned.append(p)
        return ". ".join(cleaned)

    # Gently weave board labels into fused text when useful
    for i, fused in enumerate(fused_sentences):
        board_text = board_elements[i][0] if board_elements[i] else ""
        safe_fused = fused if isinstance(fused, str) else ""
        if board_text:
            safe_fused = merge_speech_and_board_naturally(safe_fused, board_text)
        fused_sentences[i] = _dedup_clauses(safe_fused)

    fusion_path = test_dir / "fusion_results.txt"
    with open(fusion_path, 'w', encoding='utf-8') as f:
        for idx, (seg, fused) in enumerate(zip(segments, fused_sentences), 1):
            f.write(f"[Segment {idx}] {seg.start:.1f}s - {seg.end:.1f}s\n")
            f.write(f"Original: {seg.text}\n")
            f.write(f"Fused: {fused}\n\n")

    # Save fused results as JSON for easy inspection
    fusion_json_path = test_dir / "fusion_results.json"
    with open(fusion_json_path, 'w', encoding='utf-8') as f:
        json.dump(
            [
                {
                    "id": i + 1,
                    "start": seg.start,
                    "end": seg.end,
                    "original": seg.text,
                    "fused": fused,
                }
                for i, (seg, fused) in enumerate(zip(segments, fused_sentences))
            ],
            f,
            indent=2,
        )

    print(f"[SAVED] Fusion results saved to: {fusion_path}")

    # Step 7: TTS (NEW)
    print(f"\n{'='*80}")
    print(f"STEP 7: TEXT-TO-SPEECH GENERATION")
    print(f"{'='*80}")
    audio_files = generate_tts_audio(fused_sentences, test_dir)

    # Prepare results
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
                "board_text": board_elements[i][0] if board_elements[i] else "",
                "audio_path": audio_files[i] if i < len(audio_files) else ""
            }
            for i, (seg, fused) in enumerate(zip(segments, fused_sentences))
        ]
    }

    results_path = test_dir / "complete_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"PIPELINE COMPLETE!")
    print(f"{'='*80}")
    print(f"[OK] Results saved to: {test_dir}")

    return results


def main():
    """Main entry point."""
    print(f"\n{'='*80}")
    print(f"CLASSCAST PIPELINE - COMPLETE VERSION")
    print(f"[OK] Sentence-level ASR (FIXED)")
    print(f"[OK] No paraphrasing (FIXED)")
    print(f"[OK] TTS audio generation (NEW)")
    print(f"{'='*80}")

    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] ERROR: OPENAI_API_KEY not found in .env file")
        sys.exit(1)

    if not os.getenv("ASSEMBLYAI_API_KEY"):
        print("[ERROR] ERROR: ASSEMBLYAI_API_KEY not found in .env file")
        sys.exit(1)

    print("[OK] API keys found")

    # YouTube URL
    youtube_url = "https://youtu.be/i4g1krYYIFE?si=DA1ZLa8SbDYr88Vx"
    duration = 20

    try:
        # Check if assemblyai is installed
        try:
            import assemblyai
        except ImportError:
            print("Installing assemblyai...")
            subprocess.run([sys.executable, "-m", "pip", "install", "assemblyai"], check=True)

        # Run pipeline
        results = run_pipeline(youtube_url, duration)

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Video URL: {youtube_url}")
        print(f"Duration: {duration} seconds")
        print(f"Frames extracted: {results['total_frames']}")
        print(f"Transcript segments: {results['total_segments']} (sentence-based)")
        print(f"Audio files generated: {len([s for s in results['segments'] if s.get('audio_path')])}")

        print(f"\nFirst 3 segments:")
        print(f"{'-'*80}")

        for seg in results['segments'][:3]:
            print(f"\n[{seg['id']}] {seg['start']:.1f}s - {seg['end']:.1f}s")
            print(f"  Original: {seg['original_text']}")
            print(f"  Fused:    {seg['fused_text']}")
            if seg['board_text']:
                print(f"  Board:    {seg['board_text'][:100]}")

        return results

    except Exception as e:
        print(f"\n[ERROR] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    results = main()
