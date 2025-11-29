# Beyond Basic Requirements

Implemented extras beyond a minimal OCR+ASR pipeline:

- **Semantic search:** embeddings with OpenAI `text-embedding-3-small` over fused text + board snippets; thresholding to drop weak hits.
- **Timeline-aware Q&A UI:** GPT-4o-mini tutor answers plus seekable timestamps from search results.
- **Multilingual podcasts:** translate fused lines then synthesize full-episode MP3s per language with OpenAI `tts-1`.
- **Segment-level audio narration:** pyttsx3 TTS for each fused segment so playback aligns to timestamps.
- **Batch fusion to curb hallucination:** grouped GPT-4o-mini calls, strict no-paraphrase prompt, LaTeX-to-speech cleaning.
- **OCR relevance filtering:** histogram + pixel-change checks to skip near-identical frames; line-level dedup suppresses repeats.
- **Run-scoped artifacts:** `/test_output/runs/<id>/` keeps frames, OCR, transcripts, fusion JSON, audio, podcasts for inspection.
- **YouTube + upload support:** download-and-trim with `yt-dlp` or process uploaded files; duration trimming for YouTube clips.
- **Voice input on UI:** Web Speech API buttons for search and Q&A.
