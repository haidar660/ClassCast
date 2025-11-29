# TTS Pipeline

- **Segment-level audio:** `TTS.generate_tts_audio` uses pyttsx3 to synthesize each fused sentence; outputs `audio/segment_XXX.mp3` for UI-aligned playback.
- **Podcast synthesis:** `app._synthesize_podcast` translates fused lines into requested languages (GPT-4o-mini), chunks long text, then calls OpenAI `tts-1` to emit `podcasts/<lang>/podcast_<lang>.mp3`.
- **Config:** Controlled via `.env` (`TTS_ENABLED`, voice/rate/volume) and request languages list.
- **Fallbacks:** If TTS is disabled or fails, empty path placeholders are returned so the UI remains stable.
