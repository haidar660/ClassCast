"""
Utilities to prepare fusion inputs (segments and board elements) consistently.
"""
from typing import List

from fusion.models.data_models import TranscriptSegment


def filter_incomplete_segments(segments: List[TranscriptSegment], min_words: int = 4) -> List[TranscriptSegment]:
    """Drop obviously incomplete transcript fragments (fewer than min_words)."""
    return [seg for seg in segments if len(seg.text.split()) >= min_words]


def _normalize_board(text: str) -> str:
    cleaned = text.replace("```", "").replace("`", "").strip()
    return " ".join(cleaned.lower().split())


def build_board_elements(segments: List[TranscriptSegment], ocr_results: list) -> List[list]:
    """
    For each segment, attach board text with de-duplication across segments.
    Returns a list parallel to segments, each item either [] or [board_text].
    """
    board_elements: List[list] = []
    board_seen = set()

    for seg in segments:
        seg_mid = seg.midpoint
        closest_ocr = min(ocr_results, key=lambda x: abs(x['timestamp'] - seg_mid))
        raw_board_text = closest_ocr.get('text', '').strip()
        cleaned_text = raw_board_text.replace("```", "").replace("`", "").strip()
        board_norm = _normalize_board(cleaned_text) if cleaned_text else ""

        if board_norm and board_norm not in board_seen:
            board_elements.append([cleaned_text])
            board_seen.add(board_norm)
        else:
            board_elements.append([])

    return board_elements


__all__ = ["filter_incomplete_segments", "build_board_elements"]
