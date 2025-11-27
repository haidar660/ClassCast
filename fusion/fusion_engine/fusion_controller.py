"""
Fusion Controller for ClassCast Pipeline

This module coordinates the fusion process, replacing individual per-segment
API calls with efficient batch processing.

It integrates the batch_fusion engine into the existing pipeline architecture,
ensuring chronological order and proper error handling.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from utils.logging_utils import setup_logger
from fusion.models.data_models import TranscriptSegment, FrameInfo
from fusion.fusion_engine.batch_fusion import batch_fuse_segments, batch_fuse_simple

logger = setup_logger(__name__)


class FusionController:
    """
    Controls the fusion process for the ClassCast pipeline.

    This class replaces the old per-segment fusion approach with
    batch processing to avoid rate limiting and improve efficiency.
    """

    def __init__(self, batch_size: int = 4):
        """
        Initialize the fusion controller.

        Args:
            batch_size: Number of segments to process per API call (default: 4)
        """
        self.batch_size = batch_size
        logger.info(f"FusionController initialized with batch_size={batch_size}")

    def fuse_pipeline(
        self,
        segments: List[TranscriptSegment],
        frames: List[FrameInfo],
        board_elements: Optional[List[List[str]]] = None
    ) -> List[str]:
        """
        Fuse transcript segments with frames and board content using batch processing.

        This is the main entry point for the fusion step in the pipeline.

        Args:
            segments: List of TranscriptSegment objects
            frames: List of FrameInfo objects (must be parallel to segments)
            board_elements: Optional list of LaTeX strings for each segment

        Returns:
            List of fused podcast-ready sentences in chronological order

        Raises:
            ValueError: If segments and frames lists have different lengths
        """
        if len(segments) != len(frames):
            raise ValueError(
                f"Segments ({len(segments)}) and frames ({len(frames)}) must have same length"
            )

        logger.info(f"Starting fusion pipeline for {len(segments)} segments")

        # Convert data models to dicts for batch_fusion
        segment_dicts = [
            {
                'text': seg.text,
                'start': seg.start,
                'end': seg.end
            }
            for seg in segments
        ]

        frame_dicts = [
            {
                'path': frame.path,
                'time': frame.time
            }
            for frame in frames
        ]

        # Run batch fusion
        fused_sentences = batch_fuse_segments(
            segments=segment_dicts,
            frames=frame_dicts,
            board_elements=board_elements,
            batch_size=self.batch_size
        )

        # Verify chronological order (should already be correct)
        if len(fused_sentences) != len(segments):
            logger.error(
                f"Fusion returned {len(fused_sentences)} results, "
                f"expected {len(segments)}"
            )

        logger.info("Fusion pipeline complete")
        return fused_sentences

    def fuse_from_files(
        self,
        segments_json_path: Path,
        frames_json_path: Path,
        board_elements_json_path: Optional[Path] = None,
        output_path: Optional[Path] = None
    ) -> List[str]:
        """
        Load data from JSON files, run fusion, optionally save results.

        Args:
            segments_json_path: Path to transcript segments JSON
            frames_json_path: Path to frames metadata JSON
            board_elements_json_path: Optional path to board elements JSON
            output_path: Optional path to save fused transcript

        Returns:
            List of fused sentences
        """
        logger.info("Loading data from JSON files...")

        # Load segments
        with open(segments_json_path, 'r', encoding='utf-8') as f:
            segments_data = json.load(f)

        if isinstance(segments_data, dict) and 'segments' in segments_data:
            segments_data = segments_data['segments']

        segments = [
            TranscriptSegment(
                start=seg['start'],
                end=seg['end'],
                text=seg['text']
            )
            for seg in segments_data
        ]

        # Load frames
        with open(frames_json_path, 'r', encoding='utf-8') as f:
            frames_data = json.load(f)

        if isinstance(frames_data, dict) and 'frames' in frames_data:
            frames_data = frames_data['frames']

        frames = [
            FrameInfo(
                time=frame['timestamp'] if 'timestamp' in frame else frame['time'],
                path=frame['path']
            )
            for frame in frames_data
        ]

        # Load board elements if provided
        board_elements = None
        if board_elements_json_path:
            with open(board_elements_json_path, 'r', encoding='utf-8') as f:
                board_elements = json.load(f)

        # Run fusion
        fused_sentences = self.fuse_pipeline(segments, frames, board_elements)

        # Save results if output path provided
        if output_path:
            self._save_results(fused_sentences, output_path)

        return fused_sentences

    def _save_results(self, fused_sentences: List[str], output_path: Path):
        """
        Save fused sentences to file.

        Args:
            fused_sentences: List of fused sentences
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, sentence in enumerate(fused_sentences, 1):
                f.write(f"[Segment {idx}]\n")
                f.write(f"{sentence}\n\n")

        logger.info(f"Saved {len(fused_sentences)} fused sentences to: {output_path}")


def process_video_to_podcast(
    video_id: str,
    segments_path: Path,
    frames_path: Path,
    output_path: Path,
    batch_size: int = 4
) -> List[str]:
    """
    High-level function to process a video through the fusion pipeline.

    This is a convenience function that handles the entire fusion workflow.

    Args:
        video_id: Identifier for the video
        segments_path: Path to transcript segments JSON
        frames_path: Path to frames metadata JSON
        output_path: Path to save final podcast script
        batch_size: Number of segments per batch (default: 4)

    Returns:
        List of fused podcast sentences

    Example:
        >>> fused = process_video_to_podcast(
        ...     video_id='lecture_01',
        ...     segments_path=Path('data/segments.json'),
        ...     frames_path=Path('data/frames.json'),
        ...     output_path=Path('output/podcast.txt'),
        ...     batch_size=5
        ... )
    """
    logger.info(f"Processing video '{video_id}' through fusion pipeline")

    controller = FusionController(batch_size=batch_size)

    fused_sentences = controller.fuse_from_files(
        segments_json_path=segments_path,
        frames_json_path=frames_path,
        output_path=output_path
    )

    logger.info(f"Video '{video_id}' processing complete!")
    return fused_sentences


def quick_fuse(transcript_texts: List[str], frame_paths: List[str]) -> List[str]:
    """
    Quick fusion for simple use cases without complex data structures.

    Args:
        transcript_texts: List of transcript text strings
        frame_paths: List of frame image paths

    Returns:
        List of fused sentences

    Example:
        >>> texts = ["Let's discuss derivatives", "The chain rule"]
        >>> paths = ["frame1.jpg", "frame2.jpg"]
        >>> results = quick_fuse(texts, paths)
    """
    return batch_fuse_simple(transcript_texts, frame_paths, batch_size=4)


if __name__ == "__main__":
    """
    Test the fusion controller with real data.
    """
    from pathlib import Path

    logger.info("Testing FusionController...")

    # Test with the demo video data
    segments_file = Path("data/test_video/transcript.json")
    frames_file = Path("data/test_video/frames.json")
    output_file = Path("data/fusion_results/batch_fused_transcript.txt")

    if segments_file.exists() and frames_file.exists():
        logger.info("Found test data, running fusion...")

        controller = FusionController(batch_size=3)

        results = controller.fuse_from_files(
            segments_json_path=segments_file,
            frames_json_path=frames_file,
            output_path=output_file
        )

        print("\n" + "=" * 80)
        print("FUSION CONTROLLER TEST RESULTS")
        print("=" * 80)
        print(f"Processed {len(results)} segments")
        print(f"Output saved to: {output_file}")
        print("\nFirst 3 results:")
        print("-" * 80)
        for idx, sentence in enumerate(results[:3], 1):
            print(f"\n[{idx}] {sentence}")
        print("\n" + "=" * 80)

    else:
        logger.warning("Test data not found. Skipping integration test.")
        logger.info("Create data/test_video/transcript.json and frames.json to test")

        # Show simple example instead
        print("\n" + "=" * 80)
        print("SIMPLE USAGE EXAMPLE")
        print("=" * 80)
        print("""
# Example 1: Using FusionController with data models
from data_models import TranscriptSegment, FrameInfo

segments = [
    TranscriptSegment(start=0, end=5, text="Functions are fundamental"),
    TranscriptSegment(start=5, end=10, text="Derivatives measure change")
]

frames = [
    FrameInfo(time=2.5, path="frame_0.jpg"),
    FrameInfo(time=7.5, path="frame_1.jpg")
]

controller = FusionController(batch_size=4)
results = controller.fuse_pipeline(segments, frames)

# Example 2: Simple text-based fusion
texts = ["Functions are fundamental", "Derivatives measure change"]
paths = ["frame_0.jpg", "frame_1.jpg"]
results = quick_fuse(texts, paths)

# Example 3: From JSON files
results = process_video_to_podcast(
    video_id='lecture_01',
    segments_path=Path('segments.json'),
    frames_path=Path('frames.json'),
    output_path=Path('podcast.txt'),
    batch_size=5
)
        """)
        print("=" * 80)
