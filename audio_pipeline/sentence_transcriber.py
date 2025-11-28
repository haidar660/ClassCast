"""
AssemblyAI transcription helper that returns one segment per sentence.
Uses the AssemblyAI SDK and falls back to utterances or manual punctuation-based splitting.
"""
from pathlib import Path
from typing import List

import assemblyai as aai

import config
from fusion.models.data_models import TranscriptSegment
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def _split_into_sentences(text: str, words: list) -> List[TranscriptSegment]:
    """
    Split transcript text into sentences using punctuation and align with word timings.
    Returns TranscriptSegments with second-level timestamps.
    """
    import re

    sentence_endings = re.split(r"([.!?]+)", text)
    sentences = []
    current_text = ""

    for i in range(0, len(sentence_endings), 2):
        if i < len(sentence_endings):
            current_text = sentence_endings[i]
            if i + 1 < len(sentence_endings):
                current_text += sentence_endings[i + 1]
            current_text = current_text.strip()
            if current_text:
                sentences.append(current_text)

    segments: List[TranscriptSegment] = []
    word_idx = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        if not sentence_words:
            continue

        start_time = None
        end_time = None
        matched_words = 0

        for w in range(word_idx, len(words)):
            word_text = words[w].text.lower().strip(".,!?")

            if matched_words < len(sentence_words):
                if word_text in sentence_words[matched_words].lower():
                    if start_time is None:
                        start_time = words[w].start / 1000.0
                    end_time = words[w].end / 1000.0
                    matched_words += 1

                    if matched_words >= len(sentence_words):
                        word_idx = w + 1
                        break

        if start_time is not None and end_time is not None:
            segments.append(TranscriptSegment(start=start_time, end=end_time, text=sentence))

    return segments


def transcribe_video_to_sentence_segments(video_path: Path) -> List[TranscriptSegment]:
    """
    Transcribe a video/audio file with AssemblyAI and return sentence-level segments.
    Prefers AssemblyAI's sentence detection, falls back to utterances or manual splitting.
    """
    if not config.ASSEMBLYAI_API_KEY:
        raise ValueError("ASSEMBLYAI_API_KEY not found")

    aai.settings.api_key = config.ASSEMBLYAI_API_KEY
    logger.info("Uploading media to AssemblyAI for sentence-level transcription...")

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(
        str(video_path),
        config=aai.TranscriptionConfig(speech_model=aai.SpeechModel.nano),
    )

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"Transcription failed: {transcript.error}")

    segments: List[TranscriptSegment] = []

    if hasattr(transcript, "sentences") and transcript.sentences:
        logger.info("Using AssemblyAI sentence-level segmentation")
        for sentence in transcript.sentences:
            segments.append(
                TranscriptSegment(
                    start=sentence.start / 1000.0,
                    end=sentence.end / 1000.0,
                    text=sentence.text,
                )
            )
        return segments

    if hasattr(transcript, "utterances") and transcript.utterances:
        logger.info("Using utterance-level segmentation")
        for utterance in transcript.utterances:
            segments.append(
                TranscriptSegment(
                    start=utterance.start / 1000.0,
                    end=utterance.end / 1000.0,
                    text=utterance.text,
                )
            )
        return segments

    if hasattr(transcript, "words") and transcript.words and transcript.text:
        logger.info("AssemblyAI did not return sentences; using punctuation-based splitting")
        return _split_into_sentences(transcript.text, transcript.words)

    logger.warning("No sentence/utterance/word data available; returning single full-text segment")
    end_time = getattr(transcript, "audio_duration", 0.0)
    segments.append(TranscriptSegment(start=0.0, end=end_time, text=getattr(transcript, "text", "")))
    return segments


__all__ = ["transcribe_video_to_sentence_segments"]
