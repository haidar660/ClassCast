"""
AssemblyAI ASR (Automatic Speech Recognition) client.
Handles audio upload and transcription using AssemblyAI API.
"""
import time
from pathlib import Path
from typing import List, Dict
import requests

import config
from utils.logging_utils import setup_logger
from utils.time_utils import milliseconds_to_seconds

logger = setup_logger(__name__)


def upload_audio_file(audio_path: Path) -> str:
    """
    Upload audio file to AssemblyAI.

    Args:
        audio_path: Path to audio file

    Returns:
        Upload URL string

    Raises:
        Exception: If upload fails
    """
    logger.info(f"Uploading audio file: {audio_path}")

    headers = {
        "authorization": config.ASSEMBLYAI_API_KEY
    }

    upload_url = f"{config.ASSEMBLYAI_BASE_URL}/upload"

    with open(audio_path, "rb") as f:
        response = requests.post(upload_url, headers=headers, data=f)

    if response.status_code != 200:
        logger.error(f"Upload failed with status {response.status_code}: {response.text}")
        raise Exception(f"Audio upload failed: {response.text}")

    upload_url = response.json()["upload_url"]
    logger.info(f"Audio uploaded successfully: {upload_url}")
    return upload_url


def request_transcription(audio_url: str) -> str:
    """
    Request transcription from AssemblyAI.

    Args:
        audio_url: URL of uploaded audio

    Returns:
        Transcription ID

    Raises:
        Exception: If transcription request fails
    """
    logger.info("Requesting transcription from AssemblyAI...")

    headers = {
        "authorization": config.ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }

    transcript_url = f"{config.ASSEMBLYAI_BASE_URL}/transcript"

    json_data = {
        "audio_url": audio_url,
        "language_code": config.DEFAULT_LANGUAGE_CODE,
        "speaker_labels": False,  # Don't need speaker diarization
        "format_text": True  # Format text with punctuation and capitalization
    }

    response = requests.post(transcript_url, json=json_data, headers=headers)

    if response.status_code != 200:
        logger.error(f"Transcription request failed with status {response.status_code}: {response.text}")
        raise Exception(f"Transcription request failed: {response.text}")

    transcript_id = response.json()["id"]
    logger.info(f"Transcription requested successfully. ID: {transcript_id}")
    return transcript_id


def poll_transcription(transcript_id: str, poll_interval: int = 5) -> Dict:
    """
    Poll AssemblyAI for transcription completion.

    Args:
        transcript_id: Transcription ID
        poll_interval: Seconds between polls (default: 5)

    Returns:
        Complete transcription data

    Raises:
        Exception: If transcription fails
    """
    logger.info(f"Polling for transcription completion (ID: {transcript_id})...")

    headers = {
        "authorization": config.ASSEMBLYAI_API_KEY
    }

    polling_url = f"{config.ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}"

    while True:
        response = requests.get(polling_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Polling failed with status {response.status_code}: {response.text}")
            raise Exception(f"Transcription polling failed: {response.text}")

        result = response.json()
        status = result["status"]

        logger.debug(f"Transcription status: {status}")

        if status == "completed":
            logger.info("Transcription completed successfully!")
            return result
        elif status == "error":
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Transcription failed: {error_msg}")
            raise Exception(f"Transcription failed: {error_msg}")

        # Still processing, wait and poll again
        time.sleep(poll_interval)


def group_words_into_sentences(words: List[Dict]) -> List[Dict]:
    """
    Group word-level timestamps into sentence-level segments.

    Sentences are detected by punctuation marks (. ! ?)

    Args:
        words: List of word dictionaries with 'start', 'end', 'text'

    Returns:
        List of sentence segments with start, end, text
    """
    if not words:
        return []

    sentences = []
    current_sentence = []
    sentence_start = None

    for word in words:
        if sentence_start is None:
            sentence_start = word["start"]

        current_sentence.append(word["text"])

        # Check if this word ends with sentence-ending punctuation
        text = word["text"]
        ends_sentence = text.endswith('.') or text.endswith('!') or text.endswith('?')

        if ends_sentence:
            # End of sentence - create segment
            sentences.append({
                "start": milliseconds_to_seconds(sentence_start),
                "end": milliseconds_to_seconds(word["end"]),
                "text": " ".join(current_sentence)
            })
            # Reset for next sentence
            current_sentence = []
            sentence_start = None

    # Handle any remaining words (sentence without ending punctuation)
    if current_sentence:
        sentences.append({
            "start": milliseconds_to_seconds(sentence_start),
            "end": milliseconds_to_seconds(words[-1]["end"]),
            "text": " ".join(current_sentence)
        })

    return sentences


def transcribe_audio(audio_path: Path) -> List[Dict]:
    """
    Complete transcription pipeline: upload, request, poll, and format.

    Args:
        audio_path: Path to audio file

    Returns:
        List of transcript segments:
        [
            {
                "start": float (seconds),
                "end": float (seconds),
                "text": str
            },
            ...
        ]
    """
    # Step 1: Upload audio
    audio_url = upload_audio_file(audio_path)

    # Step 2: Request transcription
    transcript_id = request_transcription(audio_url)

    # Step 3: Poll until complete
    result = poll_transcription(transcript_id)

    # Step 4: Format segments
    # PRIORITY 1: Use full text split by sentences (best for readability)
    if "text" in result and result["text"]:
        # Use AssemblyAI's sentence-level segmentation
        # Group words by sentence for better timestamps
        segments = group_words_into_sentences(result.get("words", []))
        logger.info(f"Transcription complete. Total segments: {len(segments)} (sentence-level)")
        return segments

    # PRIORITY 2: Use utterances if available (speaker turns)
    if "utterances" in result and result["utterances"]:
        segments = []
        for utterance in result["utterances"]:
            segments.append({
                "start": milliseconds_to_seconds(utterance["start"]),
                "end": milliseconds_to_seconds(utterance["end"]),
                "text": utterance["text"]
            })
        logger.info(f"Transcription complete. Total segments: {len(segments)} (utterance-level)")
        return segments

    # FALLBACK: Use word-level (not ideal but better than nothing)
    if "words" in result and result["words"]:
        segments = []
        for word in result["words"]:
            segments.append({
                "start": milliseconds_to_seconds(word["start"]),
                "end": milliseconds_to_seconds(word["end"]),
                "text": word["text"]
            })
        logger.warning("Using word-level segments (not ideal). Consider enabling sentence detection.")
        logger.info(f"Transcription complete. Total segments: {len(segments)} (word-level)")
        return segments

    logger.error("No transcription data available")
    return []
