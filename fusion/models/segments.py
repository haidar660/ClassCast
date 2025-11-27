"""
Data classes for transcript segments, OCR results, and fused segments.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class TranscriptSegment:
    """
    Represents a segment of transcribed speech.

    Attributes:
        text: The transcribed text
        start: Start time in seconds
        end: End time in seconds
        confidence: Optional confidence score from ASR
    """
    text: str
    start: float
    end: float
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptSegment':
        """Create from dictionary."""
        return cls(
            text=data['text'],
            start=data['start'],
            end=data['end'],
            confidence=data.get('confidence')
        )


@dataclass
class CleanFrameOCR:
    """
    Represents cleaned and structured OCR results from a single frame.

    Attributes:
        text_clean: Cleaned OCR text
        text_raw: Raw OCR text (before cleaning)
        structure: Structure type (e.g., "equation", "bullets", "table", "definition")
        timestamp: Frame timestamp in seconds
        frame_id: Frame identifier
        confidence: OCR confidence score
        math_elements: List of detected mathematical elements
        metadata: Additional metadata (bounding boxes, etc.)
    """
    text_clean: str
    timestamp: float
    structure: str = "unknown"
    text_raw: str = ""
    frame_id: str = ""
    confidence: float = 0.0
    math_elements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text_clean': self.text_clean,
            'text_raw': self.text_raw,
            'structure': self.structure,
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'confidence': self.confidence,
            'math_elements': self.math_elements,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CleanFrameOCR':
        """Create from dictionary."""
        return cls(
            text_clean=data['text_clean'],
            timestamp=data['timestamp'],
            structure=data.get('structure', 'unknown'),
            text_raw=data.get('text_raw', ''),
            frame_id=data.get('frame_id', ''),
            confidence=data.get('confidence', 0.0),
            math_elements=data.get('math_elements', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class FusedSegment:
    """
    Represents a fused segment combining transcript and OCR data.

    Attributes:
        transcript_text: Original transcript text
        ocr_text_clean: Cleaned OCR text
        fused_ui_text: Text suitable for UI display (can contain symbols)
        fused_tts_text: Text optimized for TTS (fully spoken, no formulas)
        start: Start time in seconds
        end: End time in seconds
        structure: OCR structure type
        frame_id: Associated frame ID
    """
    transcript_text: str
    ocr_text_clean: str
    fused_ui_text: str
    fused_tts_text: str
    start: float
    end: float
    structure: str = "unknown"
    frame_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'transcript_text': self.transcript_text,
            'ocr_text_clean': self.ocr_text_clean,
            'fused_ui_text': self.fused_ui_text,
            'fused_tts_text': self.fused_tts_text,
            'start': self.start,
            'end': self.end,
            'structure': self.structure,
            'frame_id': self.frame_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FusedSegment':
        """Create from dictionary."""
        return cls(
            transcript_text=data['transcript_text'],
            ocr_text_clean=data['ocr_text_clean'],
            fused_ui_text=data['fused_ui_text'],
            fused_tts_text=data['fused_tts_text'],
            start=data['start'],
            end=data['end'],
            structure=data.get('structure', 'unknown'),
            frame_id=data.get('frame_id', '')
        )
