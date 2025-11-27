"""
Pairing module for ClassCast pipeline.
Pairs transcript segments with their corresponding frames and board elements.
"""
from typing import List, Dict

from fusion.models.data_models import TranscriptSegment, FrameInfo, BoardElement, find_closest_frame
# TODO: Import from your existing board_state module when integrated
# from board_state import get_board_elements_at_time


def get_board_elements_at_time(t: float) -> List[BoardElement]:
    """
    Temporary stub for get_board_elements_at_time.
    This will be replaced with the actual import from board_state module.
    """
    # TODO: Replace with actual board_state module import
    return []


def pair_segments_with_context(
    segments: List[TranscriptSegment],
    frames: List[FrameInfo]
) -> List[Dict]:
    """
    Pair each transcript segment with its corresponding frame and board elements.

    For each transcript segment:
    1. Calculates the midpoint time
    2. Finds the closest frame to that midpoint
    3. Retrieves board elements visible at that time

    Args:
        segments: List of transcript segments with timestamps
        frames: List of extracted frames with timestamps

    Returns:
        List of dictionaries, each containing:
        {
            "segment": TranscriptSegment,
            "frame": FrameInfo,
            "board_elements": list[BoardElement]
        }
    """
    # Use find_closest_frame to get the mapping
    segment_to_frame = find_closest_frame(segments, frames)

    paired_data = []

    for idx, segment in enumerate(segments):
        # Get the midpoint time for this segment
        seg_mid = (segment.start + segment.end) / 2.0

        # Get the closest frame (already computed by find_closest_frame)
        frame = segment_to_frame.get(idx)

        # Get board elements active at the segment midpoint
        board_elements = get_board_elements_at_time(seg_mid)

        # Create the pairing
        paired_data.append({
            "segment": segment,
            "frame": frame,
            "board_elements": board_elements
        })

    return paired_data
