"""
ClassCast Frame Extraction Tool
================================
Standalone frame extraction utility for extracting frames from video lectures.

Usage:
    python extract_frames.py <video_path> [options]

Example:
    python extract_frames.py lecture.mp4 --interval 2 --quality 95
    python extract_frames.py lecture.mp4 --start 56 --end 174
"""

import argparse
import json
import sys
import io
from pathlib import Path
from typing import List, Dict, Optional
import cv2

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def setup_output_directory(output_dir: Path) -> None:
    """Create output directory if it doesn't exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")


def get_video_info(video_path: Path) -> Dict:
    """
    Get video metadata.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with fps, total_frames, duration
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

    Args:
        video_path: Path to input video file
        output_dir: Directory to save extracted frames
        interval: Seconds between frame extractions (default: 2.0)
        quality: JPEG quality 0-100, higher is better (default: 95)
        start_time: Start extraction at this time in seconds (optional)
        end_time: Stop extraction at this time in seconds (optional)
        prefix: Prefix for frame filenames (default: "frame")

    Returns:
        List of frame metadata dictionaries with keys:
        - frame_id: str
        - frame_number: int
        - timestamp: float (seconds)
        - path: str (absolute path to frame image)
    """
    print(f"🎬 Processing video: {video_path.name}")

    # Open video
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise Exception(f"Could not open video file: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"📊 Video info:")
    print(f"   FPS: {fps:.2f}")
    print(f"   Total frames: {total_frames}")
    print(f"   Duration: {duration:.2f}s")

    # Calculate frame range
    start_frame = int(start_time * fps) if start_time else 0
    end_frame = int(end_time * fps) if end_time else total_frames

    if start_time or end_time:
        print(f"⏱️  Extracting from {start_time or 0:.1f}s to {end_time or duration:.1f}s")

    # Calculate frame interval
    frame_interval = int(fps * interval)
    if frame_interval < 1:
        frame_interval = 1

    print(f"⚙️  Settings:")
    print(f"   Interval: {interval}s ({frame_interval} frames)")
    print(f"   Quality: {quality}")

    # Extract frames
    frames_metadata = []
    current_frame = start_frame
    extracted_count = 0

    # Seek to start position
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    print(f"\n🔄 Extracting frames...")

    while current_frame <= end_frame:
        # Set position
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()

        if not ret:
            break

        # Calculate timestamp (relative to start_time if provided)
        absolute_timestamp = current_frame / fps
        relative_timestamp = absolute_timestamp - (start_time or 0)

        # Generate frame ID and filename
        frame_id = f"{prefix}_{extracted_count:04d}"
        filename = f"{frame_id}_t{relative_timestamp:.1f}s.jpg"
        frame_path = output_dir / filename

        # Save frame with specified quality
        cv2.imwrite(
            str(frame_path),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )

        # Store metadata
        frames_metadata.append({
            "frame_id": frame_id,
            "frame_number": extracted_count,
            "timestamp": relative_timestamp,
            "absolute_timestamp": absolute_timestamp,
            "path": str(frame_path.absolute())
        })

        extracted_count += 1

        # Progress update
        if extracted_count % 10 == 0:
            print(f"   Extracted {extracted_count} frames...")

        # Move to next interval
        current_frame += frame_interval

    cap.release()

    print(f"✅ Extraction complete! {len(frames_metadata)} frames extracted")

    return frames_metadata


def save_metadata(frames_metadata: List[Dict], output_path: Path) -> None:
    """Save frame metadata to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_frames": len(frames_metadata),
            "frames": frames_metadata
        }, f, indent=2)

    print(f"💾 Metadata saved to: {output_path}")


def main():
    """Main entry point for frame extraction."""
    parser = argparse.ArgumentParser(
        description="Extract frames from video lectures at regular intervals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract frames every 2 seconds with default quality
  python extract_frames.py lecture.mp4

  # Extract frames every 1 second with high quality
  python extract_frames.py lecture.mp4 --interval 1 --quality 98

  # Extract frames from specific time range
  python extract_frames.py lecture.mp4 --start 56 --end 174

  # Custom output directory and prefix
  python extract_frames.py lecture.mp4 --output my_frames --prefix lecture
        """
    )

    # Required arguments
    parser.add_argument(
        "video_path",
        type=str,
        help="Path to input video file"
    )

    # Optional arguments
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="frames",
        help="Output directory for frames (default: frames)"
    )

    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=2.0,
        help="Seconds between frame extractions (default: 2.0)"
    )

    parser.add_argument(
        "--quality",
        "-q",
        type=int,
        default=95,
        help="JPEG quality 0-100, higher is better (default: 95)"
    )

    parser.add_argument(
        "--start",
        "-s",
        type=float,
        default=None,
        help="Start extraction at this time in seconds (optional)"
    )

    parser.add_argument(
        "--end",
        "-e",
        type=float,
        default=None,
        help="Stop extraction at this time in seconds (optional)"
    )

    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        default="frame",
        help="Prefix for frame filenames (default: frame)"
    )

    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't save metadata JSON file"
    )

    args = parser.parse_args()

    # Validate inputs
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"❌ Error: Video file not found: {video_path}")
        sys.exit(1)

    if args.quality < 1 or args.quality > 100:
        print(f"❌ Error: Quality must be between 1 and 100")
        sys.exit(1)

    if args.interval <= 0:
        print(f"❌ Error: Interval must be positive")
        sys.exit(1)

    # Setup output directory
    output_dir = Path(args.output)
    setup_output_directory(output_dir)

    try:
        # Extract frames
        frames_metadata = extract_frames(
            video_path=video_path,
            output_dir=output_dir,
            interval=args.interval,
            quality=args.quality,
            start_time=args.start,
            end_time=args.end,
            prefix=args.prefix
        )

        # Save metadata unless disabled
        if not args.no_metadata:
            metadata_path = output_dir / "frames_metadata.json"
            save_metadata(frames_metadata, metadata_path)

        print("\n✨ Frame extraction completed successfully!")
        print(f"📂 Frames saved to: {output_dir.absolute()}")

    except Exception as e:
        print(f"\n❌ Error during frame extraction: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
