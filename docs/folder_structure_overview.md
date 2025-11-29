# Folder Structure Overview

```
ClassCast/
├── app.py                    # FastAPI server + routes/UI mount
├── run_complete_pipeline.py  # End-to-end pipeline runner
├── config.py                 # Global settings and API keys
├── audio_pipeline/           # Audio extraction + ASR (AssemblyAI sentence segments)
├── frame_extraction/         # Frame sampling + dedup utilities
├── ocr/                      # Vision OCR (OpenAI Vision) and tests
├── fusion/                   # Fusion engine (batch LLM), data models, tests
├── TTS/                      # Local TTS helper (pyttsx3)
├── utils/                    # Logging, LaTeX/text helpers, paths
├── templates/                # Jinja2 templates (UI)
├── static/                   # Frontend assets (CSS)
├── data/                     # Sample inputs (test video, OCR frames)
├── test_output/              # Generated artifacts; `/runs/<id>/` per API run
├── docs/                     # Documentation (design, pipeline, problem, reproducibility, etc.)
├── requirements.txt
└── README.md
```

- **Auto-generated:** `test_output/` and `test_output/runs/<uuid>/` (frames, OCR, transcripts, fusion JSON, audio, podcasts). Safe to delete between runs; avoid committing.
- **Inputs:** Place custom videos in `data/` or upload via UI/API; sample YouTube URL lives in `run_complete_pipeline.py`.
- **Do not edit:** Reference outputs in `fusion/test_output/` and `ocr/tests/preprocessed_images/` are kept for inspection.
- **Ignored:** `.env`, caches (`__pycache__/`), logs, `.claude/` per `.gitignore`.
