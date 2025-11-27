"""
Public helpers to run fusion without relying on the pipeline scripts.

Usage sketch:
    from fusion.fusion_engine.fusion_service import fuse_segments_with_board
    fused = fuse_segments_with_board(segments, frames, ocr_results)
"""
from typing import List

from fusion.fusion_engine.fusion_controller import FusionController
from fusion.fusion_engine.fusion_inputs import (
    filter_incomplete_segments,
    build_board_elements,
)
from fusion.models.data_models import FrameInfo, TranscriptSegment, find_closest_frame


def prepare_fusion_inputs(
    segments: List[TranscriptSegment],
    ocr_results: list,
    min_words: int = 4,
) -> tuple[list[TranscriptSegment], list[list[str]]]:
    """
    Filter incomplete segments and build deduped board elements.

    Returns (filtered_segments, board_elements).
    """
    filtered_segments = filter_incomplete_segments(segments, min_words=min_words)
    board_elements = build_board_elements(filtered_segments, ocr_results)
    return filtered_segments, board_elements


def fuse_segments_with_board(
    segments: List[TranscriptSegment],
    frames: List[FrameInfo],
    ocr_results: list,
    batch_size: int = 4,
) -> List[str]:
    """
    High-level fusion entry point independent of run_* scripts.

    Args:
        segments: transcript segments (with start/end/time)
        frames: frame info (FrameInfo objects with time/path)
        ocr_results: list of OCR dicts containing 'timestamp' and 'text'
        batch_size: fusion batch size

    Returns:
        List of fused sentences (aligned to provided segments order)
    """
    filtered_segments, board_elements = prepare_fusion_inputs(segments, ocr_results)

    # Align frames to filtered segments
    segment_to_frame = find_closest_frame(filtered_segments, frames)
    aligned_frames = [segment_to_frame[i] for i in range(len(filtered_segments))]

    controller = FusionController(batch_size=batch_size)
    fused_sentences = controller.fuse_pipeline(
        segments=filtered_segments,
        frames=aligned_frames,
        board_elements=board_elements,
    )

    return fused_sentences


__all__ = ["prepare_fusion_inputs", "fuse_segments_with_board"]
