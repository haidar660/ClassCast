# Design Decisions

## Goals
- Keep artifacts per run for debugging and grading.
- Minimize preprocessing; lean on robust models with light filtering.
- Modular stages so OCR/ASR/fusion/TTS can be swapped independently.
- Extensible prompts/features without reworking the pipeline.

## Architecture (high level)
- Ingest (upload/YouTube) → frame extraction/dedup → OCR (OpenAI Vision) → ASR (AssemblyAI sentences) → segment-frame pairing → board attach → batched fusion (GPT-4o-mini) → TTS (pyttsx3 per segment + OpenAI podcasts).
- FastAPI (`app.py`) triggers background runs, serves UI, builds embeddings for search/Q&A, and stores artifacts under `test_output/runs/<uuid>/`.
- Frontend (Jinja2 + vanilla JS) polls status, renders semantic search/Q&A, and streams generated audio.

## Key choices
- **Timestamp alignment:** map each sentence to the closest frame midpoint so fusion is grounded.
- **Per-run folders:** simpler inspection vs a DB; easy to swap to DB/queue if scale grows.
- **Background tasks:** long-running work stays off request thread; UI polls `/api/runs/{id}`.
- **Batched fusion:** default batch_size=4 reduces API calls and preserves order with backoff on failures.
- **Dedup for efficiency:** histogram/diff frame filtering before OCR; line-level dedup across frames to avoid repeated board text.
- **Safety rails:** strict fusion prompt forbids paraphrasing; similarity thresholding (0.30) on search results filters noise.
- **TTS split:** pyttsx3 for per-segment alignment; OpenAI TTS for high-quality multilingual podcasts.

## Limitations and improvements
- OCR depends on OpenAI Vision; add math/handwriting OCR or board-region crops for messy boards.
- Frame sampling is fixed interval; adaptive sampling around speech activity could tighten alignment.
- Mostly sequential; OCR and ASR could run in parallel and cache embeddings per run.
- pyttsx3 voice quality varies by OS; cloud per-segment TTS is better quality but costs more.
- No persistent DB/queue; multi-user scale would benefit from workers + object storage.
