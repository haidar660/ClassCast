"""
Data models for ClassCast video-to-podcast pipeline.
Defines dataclasses and helper functions for transcript segments, frames, and board elements.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class TranscriptSegment:
    """A segment of transcribed speech with timestamps."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text for this segment

    @property
    def midpoint(self) -> float:
        """Calculate the midpoint time of this segment."""
        return (self.start + self.end) / 2.0

    @property
    def duration(self) -> float:
        """Calculate the duration of this segment."""
        return self.end - self.start


@dataclass
class FrameInfo:
    """Information about an extracted video frame."""
    time: float  # Time in seconds when this frame was extracted
    path: str    # File path to the frame image


@dataclass
class BoardElement:
    """A mathematical or textual element on the board."""
    id: int              # Unique identifier for this element
    latex: str           # LaTeX representation of the element
    first_seen: float    # Time (seconds) when element first appeared
    last_seen: float     # Time (seconds) when element last appeared

    @property
    def duration(self) -> float:
        """Calculate how long this element was visible."""
        return self.last_seen - self.first_seen

    def is_visible_at(self, time: float) -> bool:
        """Check if this element is visible at a given time."""
        return self.first_seen <= time <= self.last_seen


def find_closest_frame(
    segments: List[TranscriptSegment],
    frames: List[FrameInfo]
) -> Dict[int, FrameInfo]:
    """
    Match each transcript segment with its closest frame.

    For each segment, finds the frame whose timestamp is closest to the
    segment's midpoint time. This ensures that the visual content matches
    what the instructor is talking about at that moment.

    Args:
        segments: List of transcript segments with timestamps
        frames: List of extracted frames with timestamps

    Returns:
        Dictionary mapping segment index to the closest FrameInfo.
        Example: {0: FrameInfo(...), 1: FrameInfo(...), ...}
    """
    if not frames:
        return {}

    segment_to_frame = {}

    for idx, segment in enumerate(segments):
        segment_midpoint = segment.midpoint

        # Find the frame with the smallest time difference
        closest_frame = min(
            frames,
            key=lambda frame: abs(frame.time - segment_midpoint)
        )

        segment_to_frame[idx] = closest_frame

    return segment_to_frame


def get_board_elements_at_time(t: float) -> List[BoardElement]:
    """
    Get all board elements visible at a given time.

    This function will integrate with the existing board_state module
    to retrieve which mathematical elements are present on the board
    at the specified timestamp.

    Args:
        t: Time in seconds

    Returns:
        List of BoardElement objects visible at time t

    TODO: Integrate with existing board_state module implementation.
    The board_state module should provide a method to query elements by time.
    """
    # TODO: Import and call existing board_state module
    # Example integration:
    # from board_state import get_elements_at_timestamp
    # elements = get_elements_at_timestamp(t)
    # return [BoardElement(**elem) for elem in elements]

    raise NotImplementedError(
        "get_board_elements_at_time() needs to be connected to the "
        "existing board_state module implementation."
    )
