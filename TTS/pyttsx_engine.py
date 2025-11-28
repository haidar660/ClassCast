"""
Lightweight wrapper around pyttsx3 for TTS generation.
Centralizes engine configuration and audio file creation.
"""
import sys
from pathlib import Path
from typing import List, Optional, Sequence

import pyttsx3

from config import TTS_ENABLED, TTS_RATE, TTS_VOLUME, TTS_VOICE_NAME


def _configure_voice(engine: pyttsx3.Engine, desired_name: Optional[str]) -> Optional[str]:
    """Try to set the engine voice by partial name match; return the chosen id or None."""
    if not desired_name:
        return None

    desired_lower = desired_name.lower()
    for voice in engine.getProperty("voices"):
        if desired_lower in voice.name.lower():
            engine.setProperty("voice", voice.id)
            return voice.id

    return None


def generate_tts_audio(
    sentences: Sequence[str],
    output_dir: Path,
    *,
    audio_subdir: str = "audio",
    filename_prefix: str = "segment_",
    audio_extension: str = ".mp3",
) -> List[str]:
    """
    Generate TTS audio files for the provided sentences.

    Args:
        sentences: Ordered list of text snippets to synthesize.
        output_dir: Base directory where the audio subfolder will be created.
        audio_subdir: Name of the folder under output_dir to hold audio files.
        filename_prefix: Prefix for generated file names.
        audio_extension: File extension (e.g., ".mp3" or ".wav").

    Returns:
        List of generated audio file paths (empty string for failures or when disabled).
    """
    if not TTS_ENABLED:
        print("[INFO] TTS disabled via config; skipping audio generation.")
        return ["" for _ in sentences]

    audio_dir = Path(output_dir) / audio_subdir
    audio_dir.mkdir(parents=True, exist_ok=True)

    driver_name = "sapi5" if sys.platform == "win32" else None
    audio_files: List[str] = []
    total = len(sentences)

    for idx, sentence in enumerate(sentences, 1):
        audio_path = audio_dir / f"{filename_prefix}{idx:03d}{audio_extension}"
        print(f"   Generating audio {idx}/{total}...")
        try:
            eng = pyttsx3.init(driverName=driver_name)
            eng.setProperty("rate", TTS_RATE)
            eng.setProperty("volume", TTS_VOLUME)
            _configure_voice(eng, TTS_VOICE_NAME)
            eng.save_to_file(sentence, str(audio_path))
            eng.runAndWait()
            eng.stop()
            audio_files.append(str(audio_path))
        except Exception as exc:
            print(f"   [WARN] TTS failed for segment {idx}: {exc}")
            audio_files.append("")
        finally:
            try:
                del eng
            except Exception:
                pass

    print(f"[OK] Generated {len([f for f in audio_files if f])} audio files")
    return audio_files


__all__ = ["generate_tts_audio"]
