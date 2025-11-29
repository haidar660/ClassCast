# ASR Pipeline

- **Input:** Full lecture audio from the video.
- **Model:** AssemblyAI `SpeechModel.nano` via `audio_pipeline.transcribe_video_to_sentence_segments`.
- **Segmentation:** Prefer AssemblyAI sentence-level results; fall back to utterances, then punctuation-based splitting if needed.
- **Filtering:** `filter_incomplete_segments` drops very short fragments (default min_words=4).
- **Output:** `transcript.json` with `[{"start": s, "end": e, "text": "..."}]`.
- **Fallback:** If no sentence/utterance data, emit one segment using `audio_duration`.
