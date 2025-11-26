"""
Example usage scripts for the ClassCast Frame Extraction Tool.

This file demonstrates common usage patterns and integration examples.
"""

import json
from pathlib import Path
from extract_frames import extract_frames, setup_output_directory


def example_basic_extraction():
    """
    Example 1: Basic frame extraction with default settings.
    """
    print("=" * 70)
    print("Example 1: Basic Frame Extraction")
    print("=" * 70)

    video_path = Path("sample_lecture.mp4")
    output_dir = Path("frames_output")

    # Setup output directory
    setup_output_directory(output_dir)

    # Extract frames every 2 seconds
    frames = extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        interval=2.0,
        quality=95
    )

    print(f"\nExtracted {len(frames)} frames")
    print(f"First frame: {frames[0]}")
    print(f"Last frame: {frames[-1]}")


def example_time_range_extraction():
    """
    Example 2: Extract frames from specific time range.
    """
    print("\n" + "=" * 70)
    print("Example 2: Time Range Extraction (56s to 174s)")
    print("=" * 70)

    video_path = Path("lecture_calculus.mp4")
    output_dir = Path("frames_segment")

    setup_output_directory(output_dir)

    # Extract only the interesting segment
    frames = extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        interval=2.0,
        quality=95,
        start_time=56.0,
        end_time=174.0,
        prefix="calculus"
    )

    print(f"\nExtracted {len(frames)} frames from segment")


def example_high_quality_for_ocr():
    """
    Example 3: High-quality extraction optimized for OCR.
    """
    print("\n" + "=" * 70)
    print("Example 3: High-Quality Extraction for OCR")
    print("=" * 70)

    video_path = Path("math_lecture.mp4")
    output_dir = Path("frames_ocr")

    setup_output_directory(output_dir)

    # Extract frames every 1 second with maximum quality
    frames = extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        interval=1.0,      # More frequent sampling
        quality=98,        # Higher quality for better OCR
        prefix="math"
    )

    print(f"\nExtracted {len(frames)} high-quality frames")


def example_batch_processing():
    """
    Example 4: Process multiple videos in batch.
    """
    print("\n" + "=" * 70)
    print("Example 4: Batch Processing Multiple Videos")
    print("=" * 70)

    videos = [
        ("lecture_01.mp4", "frames/lecture_01"),
        ("lecture_02.mp4", "frames/lecture_02"),
        ("lecture_03.mp4", "frames/lecture_03"),
    ]

    for video_file, output_dir in videos:
        video_path = Path(video_file)
        if not video_path.exists():
            print(f"Skipping {video_file} (not found)")
            continue

        output = Path(output_dir)
        setup_output_directory(output)

        print(f"\nProcessing {video_file}...")
        frames = extract_frames(
            video_path=video_path,
            output_dir=output,
            interval=2.0,
            quality=95
        )
        print(f"  → Extracted {len(frames)} frames")


def example_working_with_metadata():
    """
    Example 5: Load and work with frame metadata.
    """
    print("\n" + "=" * 70)
    print("Example 5: Working with Frame Metadata")
    print("=" * 70)

    # Assume frames were already extracted
    metadata_path = Path("frames/frames_metadata.json")

    if not metadata_path.exists():
        print("No metadata file found. Run extraction first.")
        return

    # Load metadata
    with open(metadata_path, 'r') as f:
        data = json.load(f)

    print(f"Total frames: {data['total_frames']}")
    print("\nFirst 5 frames:")

    for frame in data['frames'][:5]:
        print(f"  {frame['frame_id']}: {frame['timestamp']:.1f}s -> {Path(frame['path']).name}")

    # Find frame at specific time
    target_time = 10.0  # 10 seconds
    closest_frame = min(
        data['frames'],
        key=lambda f: abs(f['timestamp'] - target_time)
    )

    print(f"\nClosest frame to {target_time}s:")
    print(f"  {closest_frame['frame_id']} at {closest_frame['timestamp']:.1f}s")


def example_integration_with_pipeline():
    """
    Example 6: Integration with ClassCast pipeline.
    """
    print("\n" + "=" * 70)
    print("Example 6: ClassCast Pipeline Integration")
    print("=" * 70)

    video_path = Path("lecture.mp4")
    frames_dir = Path("pipeline_frames")
    metadata_path = frames_dir / "frames_metadata.json"

    # Step 1: Extract frames
    print("\n[Step 1/3] Extracting frames...")
    setup_output_directory(frames_dir)

    frames = extract_frames(
        video_path=video_path,
        output_dir=frames_dir,
        interval=2.0,
        quality=95
    )

    # Save metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_frames": len(frames),
            "frames": frames
        }, f, indent=2)

    print(f"  ✓ Extracted {len(frames)} frames")

    # Step 2: Simulate OCR processing
    print("\n[Step 2/3] Processing frames with OCR...")
    print("  (This is where you'd integrate OCR)")

    # Example: Process each frame
    for frame in frames[:3]:  # Just first 3 for demo
        frame_path = frame['path']
        timestamp = frame['timestamp']

        print(f"  Processing {frame['frame_id']} at {timestamp:.1f}s")
        # ocr_result = perform_ocr(frame_path)
        # board_elements = extract_board_elements(ocr_result)

    # Step 3: Create pipeline-compatible output
    print("\n[Step 3/3] Creating pipeline-compatible format...")

    # Convert to FrameInfo format (ClassCast data model)
    pipeline_frames = [
        {
            "time": frame["timestamp"],
            "path": frame["path"]
        }
        for frame in frames
    ]

    pipeline_output = frames_dir / "pipeline_frames.json"
    with open(pipeline_output, 'w', encoding='utf-8') as f:
        json.dump(pipeline_frames, f, indent=2)

    print(f"  ✓ Saved pipeline format to {pipeline_output}")
    print("\n✓ Ready for fusion with transcript segments!")


def main():
    """Run all examples (comment out the ones you don't need)."""

    print("\n" + "=" * 70)
    print("ClassCast Frame Extraction Tool - Usage Examples")
    print("=" * 70)

    # Uncomment the examples you want to run:

    # example_basic_extraction()
    # example_time_range_extraction()
    # example_high_quality_for_ocr()
    # example_batch_processing()
    # example_working_with_metadata()
    # example_integration_with_pipeline()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
    print("\nTo run individual examples, uncomment them in main()")


if __name__ == "__main__":
    main()
