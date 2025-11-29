# utils/paths.py
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

TEST_OUTPUT_BASE = Path("test_output")
INPUT_VIDEO_DIR = Path("data") / "input_video"


@dataclass
class RunPaths:
    run_id: str
    run_dir: Path
    input_video_path: Path
    frames_dir: Path
    audio_dir: Path
    ocr_path: Path
    transcript_path: Path
    fused_path: Path
    aligned_frames_path: Path


def create_run_paths(base_dir: Optional[Path] = None) -> RunPaths:
    base = base_dir or TEST_OUTPUT_BASE

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = base / "runs" / run_id
    input_video_path = INPUT_VIDEO_DIR / f"{run_id}.mp4"

    frames_dir = run_dir / "frames"
    audio_dir = run_dir / "audio_segments"

    ocr_path = run_dir / "ocr_results.json"
    transcript_path = run_dir / "transcript.json"
    fused_path = run_dir / "fused_results.json"
    aligned_frames_path = run_dir / "aligned_frames.json"

    frames_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    INPUT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    return RunPaths(
        run_id=run_id,
        run_dir=run_dir,
        input_video_path=input_video_path,
        frames_dir=frames_dir,
        audio_dir=audio_dir,
        ocr_path=ocr_path,
        transcript_path=transcript_path,
        fused_path=fused_path,
        aligned_frames_path=aligned_frames_path,
    )
