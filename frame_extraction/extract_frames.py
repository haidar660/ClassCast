"""
ClassCast Frame Extraction Tool
================================
Extract frames from video lectures at regular intervals.

Usage:
    python extract_frames.py <video_path> [options]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

import cv2
import numpy as np


def setup_output_directory(output_dir: Path) -> None:
    """Create output directory if it doesn't exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")


def get_video_info(video_path: Path) -> Dict:
    """
    Get video metadata.
    Returns: dict with fps, total_frames, duration.
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise Exception(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    cap.release()

    return {
        "fps": fps,
        "total_frames": total_frames,
        "duration": duration
    }


def extract_frames(
    video_path: Path,
    output_dir: Path,
    interval: float = 2.0,
    quality: int = 95,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    prefix: str = "frame"
) -> List[Dict]:
    """
    Extract frames from video at regular intervals.
    Returns list of frame metadata dictionaries.
    """
    print(f"[INFO] Processing video: {video_path.name}")

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise Exception(f"Could not open video file: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    print("[INFO] Video info:")
    print(f"   FPS: {fps:.2f}")
    print(f"   Total frames: {total_frames}")
    print(f"   Duration: {duration:.2f}s")

    # Calculate frame range
    start_frame = int(start_time * fps) if start_time else 0
    end_frame = int(end_time * fps) if end_time else total_frames

    if start_time or end_time:
        print(f"[INFO] Extracting from {start_time or 0:.1f}s to {end_time or duration:.1f}s")

    # Calculate frame interval
    frame_interval = int(fps * interval)
    if frame_interval < 1:
        frame_interval = 1

    print("[INFO] Settings:")
    print(f"   Interval: {interval}s ({frame_interval} frames)")
    print(f"   Quality: {quality}")

    # Extract frames
    frames_metadata = []
    current_frame = start_frame
    extracted_count = 0

    # Seek to start position
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    print("\n[INFO] Extracting frames...")

    while current_frame <= end_frame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break

        absolute_timestamp = current_frame / fps
        relative_timestamp = absolute_timestamp - (start_time or 0)

        frame_id = f"{prefix}_{extracted_count:04d}"
        filename = f"{frame_id}_t{relative_timestamp:.1f}s.jpg"
        frame_path = output_dir / filename

        cv2.imwrite(
            str(frame_path),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )

        frames_metadata.append({
            "frame_id": frame_id,
            "frame_number": extracted_count,
            "timestamp": relative_timestamp,
            "absolute_timestamp": absolute_timestamp,
            "path": str(frame_path.absolute())
        })

        extracted_count += 1

        if extracted_count % 10 == 0:
            print(f"   Extracted {extracted_count} frames...")

        current_frame += frame_interval

    cap.release()

    print(f"[OK] Extraction complete! {len(frames_metadata)} frames extracted")

    # Deduplicate near-identical frames using hist/diff and keep-every-N-seconds safeguard
    def _frame_similarity(path_a: Path, path_b: Path) -> float:
        img_a = cv2.imread(str(path_a), cv2.IMREAD_GRAYSCALE)
        img_b = cv2.imread(str(path_b), cv2.IMREAD_GRAYSCALE)
        if img_a is None or img_b is None:
            return 0.0
        hist_a = cv2.calcHist([img_a], [0], None, [32], [0, 256])
        hist_b = cv2.calcHist([img_b], [0], None, [32], [0, 256])
        cv2.normalize(hist_a, hist_a)
        cv2.normalize(hist_b, hist_b)
        return float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))

    def _frame_diff(path_a: Path, path_b: Path) -> float:
        img_a = cv2.imread(str(path_a), cv2.IMREAD_GRAYSCALE)
        img_b = cv2.imread(str(path_b), cv2.IMREAD_GRAYSCALE)
        if img_a is None or img_b is None:
            return 1.0
        img_a = cv2.resize(img_a, (64, 64))
        img_b = cv2.resize(img_b, (64, 64))
        return float(np.mean(np.abs(img_a.astype(np.float32) - img_b.astype(np.float32))) / 255.0)

    hist_threshold = 0.85
    diff_threshold = 0.05
    keep_every_seconds = 5.0

    filtered_frames: List[Dict[str, any]] = []
    last_kept: Optional[Dict[str, any]] = None
    last_kept_ts: Optional[float] = None
    for frame in frames_metadata:
        if last_kept is None:
            filtered_frames.append(frame)
            last_kept = frame
            last_kept_ts = frame.get("timestamp", 0.0)
            continue
        sim = _frame_similarity(Path(last_kept["path"]), Path(frame["path"]))
        diff = _frame_diff(Path(last_kept["path"]), Path(frame["path"]))
        cur_ts = frame.get("timestamp", 0.0)
        time_gap = (cur_ts - last_kept_ts) if last_kept_ts is not None else keep_every_seconds
        if not (sim >= hist_threshold or diff <= diff_threshold) or time_gap >= keep_every_seconds:
            filtered_frames.append(frame)
            last_kept = frame
            last_kept_ts = cur_ts

    if len(filtered_frames) != len(frames_metadata):
        print(f"[INFO] Frame dedup: kept {len(filtered_frames)} / {len(frames_metadata)} frames")

    return filtered_frames


def save_metadata(frames_metadata: List[Dict], output_path: Path) -> None:
    """Save frame metadata to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_frames": len(frames_metadata),
            "frames": frames_metadata
        }, f, indent=2)

    print(f"[OK] Metadata saved to: {output_path}")


def main():
    """Main entry point for frame extraction."""
    parser = argparse.ArgumentParser(
        description="Extract frames from video lectures at regular intervals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_frames.py lecture.mp4
  python extract_frames.py lecture.mp4 --interval 1 --quality 98
  python extract_frames.py lecture.mp4 --start 56 --end 174
  python extract_frames.py lecture.mp4 --output my_frames --prefix lecture
        """
    )

    parser.add_argument("video_path", type=str, help="Path to input video file")
    parser.add_argument("--output", "-o", type=str, default="frames", help="Output directory")
    parser.add_argument("--interval", "-i", type=float, default=2.0, help="Seconds between frames")
    parser.add_argument("--quality", "-q", type=int, default=95, help="JPEG quality 0-100")
    parser.add_argument("--start", "-s", type=float, default=None, help="Start time in seconds")
    parser.add_argument("--end", "-e", type=float, default=None, help="End time in seconds")
    parser.add_argument("--prefix", "-p", type=str, default="frame", help="Prefix for filenames")
    parser.add_argument("--no-metadata", action="store_true", help="Don't save metadata JSON file")

    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"[ERROR] Video file not found: {video_path}")
        sys.exit(1)

    if args.quality < 1 or args.quality > 100:
        print("[ERROR] Quality must be between 1 and 100")
        sys.exit(1)

    if args.interval <= 0:
        print("[ERROR] Interval must be positive")
        sys.exit(1)

    output_dir = Path(args.output)
    setup_output_directory(output_dir)

    try:
        frames_metadata = extract_frames(
            video_path=video_path,
            output_dir=output_dir,
            interval=args.interval,
            quality=args.quality,
            start_time=args.start,
            end_time=args.end,
            prefix=args.prefix
        )

        if not args.no_metadata:
            metadata_path = output_dir / "frames_metadata.json"
            save_metadata(frames_metadata, metadata_path)

        print("\n[OK] Frame extraction completed successfully!")
        print(f"[OK] Frames saved to: {output_dir.absolute()}")

    except Exception as e:
        print(f"\n[ERROR] Error during frame extraction: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
