"""
Global configuration for the ClassCast MVP project.

IMPORTANT:
- Do NOT commit your real API keys to GitHub.
- API keys are loaded from the `.env` file or OS environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load variables from .env (if present)
load_dotenv()

# === API KEYS ===
# Must be set in .env → ASSEMBLYAI_API_KEY=your_key_here
ASSEMBLYAI_API_KEY: Optional[str] = os.getenv("ASSEMBLYAI_API_KEY")
ASSEMBLYAI_BASE_URL: str = "https://api.assemblyai.com/v2"

if ASSEMBLYAI_API_KEY is None:
    raise RuntimeError(
        "ASSEMBLYAI_API_KEY is not set. "
        "Add it to your .env file or export it as an environment variable."
    )

# === Video / Audio Processing Settings ===
# How often to grab a frame from the lecture video (in seconds)
FRAME_INTERVAL_SECONDS: int = 2

# Frame extraction quality (JPEG quality: 0-100, higher is better)
# Higher quality = better OCR but larger file sizes
FRAME_QUALITY: int = 95

# Audio extraction parameters (for ffmpeg)
AUDIO_SAMPLE_RATE: int = 16000
AUDIO_CHANNELS: int = 1

# === Advanced OCR Settings ===
# Multi-layered OCR system: Docling (primary) + Pix2Text (math) + Tesseract/EasyOCR (fallback)

# Enable GPU acceleration for OCR (EasyOCR, Pix2Text)
OCR_USE_GPU: bool = False

# Enable image preprocessing before OCR
# For whiteboards/blackboards: True (enhances contrast)
# For clean screen recordings: False
OCR_USE_PREPROCESSING: bool = True

# Enable OTSU thresholding
# For whiteboards/blackboards: False (use adaptive methods)
# For photos/handwriting: True
# For screen recordings with UI: False (RECOMMENDED)
OCR_USE_THRESHOLD: bool = False

# Image upscaling factor for OCR (1.0 = no scaling, 2.0 = double size)
# Larger images = better math equation and text recognition
# Recommended: 2.5-3.0 for whiteboards, 2.0 for screen recordings
OCR_UPSCALE_FACTOR: float = 2.5

# Minimum confidence threshold for OCR results (0.0-1.0)
# Lower = more lenient, Higher = stricter
OCR_MIN_CONFIDENCE: float = 0.5

# === Advanced Fusion Settings ===
# Detect board content changes (reduces duplicate frames)
FUSION_DETECT_CHANGES: bool = True

# Similarity threshold for detecting board changes (0.0-1.0)
# Frames more similar than this are considered duplicates
# Lower = more sensitive to changes, Higher = less sensitive
FUSION_SIMILARITY_THRESHOLD: float = 0.85

# Generate semantic notes (combine speech + board meaningfully)
FUSION_GENERATE_SEMANTIC_NOTES: bool = True

# === Language / Transcript Settings ===
DEFAULT_LANGUAGE_CODE: str = "en"

# === TTS Settings (pyttsx3) ===
TTS_ENABLED: bool = True
TTS_RATE: int = 180        # words per minute
TTS_VOLUME: float = 1.0    # 0.0–1.0
TTS_VOICE_NAME: Optional[str] = None  # keep None to use default system voice

# Include whiteboard/OCR text in TTS audio
# When True: Reads "On the board: [text]" when whiteboard content changes
# When False: Only reads the spoken transcript (audio from video)
TTS_INCLUDE_BOARD_TEXT: bool = True

# === Debug / Logging ===
DEBUG_LOGGING: bool = True
