"""
Centralized path utilities for ClassCast project.
Ensures all data directories exist and provides helper functions.
"""
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
INPUT_VIDEO_DIR = DATA_DIR / "input_video"
AUDIO_DIR = DATA_DIR / "audio"
FRAMES_DIR = DATA_DIR / "frames"
OCR_DIR = DATA_DIR / "ocr"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
FUSED_DIR = DATA_DIR / "fused"
TTS_DIR = DATA_DIR / "tts"

# Template and static directories
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"


def ensure_data_directories():
    """Create all data directories if they don't exist."""
    directories = [
        INPUT_VIDEO_DIR,
        AUDIO_DIR,
        FRAMES_DIR,
        OCR_DIR,
        TRANSCRIPTS_DIR,
        FUSED_DIR,
        TTS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_file_prefix(video_filename: str) -> str:
    """
    Extract a clean prefix from the video filename.
    Example: 'lecture_01.mp4' -> 'lecture_01'
    """
    return Path(video_filename).stem


def get_audio_path(prefix: str) -> Path:
    """Get path for extracted audio file."""
    return AUDIO_DIR / f"{prefix}.wav"


def get_frame_path(prefix: str, frame_id: str) -> Path:
    """Get path for a specific frame image."""
    frame_dir = FRAMES_DIR / prefix
    frame_dir.mkdir(parents=True, exist_ok=True)
    return frame_dir / f"{frame_id}.jpg"


def get_ocr_json_path(prefix: str) -> Path:
    """Get path for OCR results JSON."""
    return OCR_DIR / f"{prefix}_ocr.json"


def get_transcript_json_path(prefix: str) -> Path:
    """Get path for ASR transcript JSON."""
    return TRANSCRIPTS_DIR / f"{prefix}_transcript.json"


def get_fused_json_path(prefix: str) -> Path:
    """Get path for fused data JSON."""
    return FUSED_DIR / f"{prefix}_fused.json"


def get_markdown_path(prefix: str) -> Path:
    """Get path for markdown export."""
    return FUSED_DIR / f"{prefix}.md"


def get_pdf_path(prefix: str) -> Path:
    """Get path for PDF export."""
    return FUSED_DIR / f"{prefix}.pdf"


def get_tts_audio_path(prefix: str) -> Path:
    """Get path for TTS audio file."""
    return TTS_DIR / f"{prefix}_podcast.mp3"
