# ClassCast

## 1. Overview
ClassCast is a video-to-podcast pipeline that extracts frames, runs OCR, performs ASR, fuses speech with board content, and generates TTS audio plus a web UI for exploration.

## 2. Problem Definition & Impact
Turn lecture videos into searchable, accessible study artifacts: aligned transcript + board text, semantic search, Q&A, and multilingual podcast audio to improve accessibility and review speed.

## 3. System Architecture
- FastAPI backend (`app.py`) serving pipeline APIs, search, chat, and TTS export.
- Core pipeline (`run_complete_pipeline.py`) orchestrating extraction → OCR → ASR → fusion → TTS.
- Frontend templates (`templates/`, `static/`) rendered by FastAPI.
- Utilities (`utils/`, `fusion/`, `ocr/`, `audio_pipeline/`, `frame_extraction/`, `TTS/`) for each stage.

## 4. Pipeline Stages
1) Download/ingest video (or use local file)  
2) Frame extraction (OpenCV) with deduping  
3) OCR on frames (OpenAI vision)  
4) ASR (AssemblyAI) with sentence-level segmentation fallback  
5) Pair segments to frames  
6) Fusion (OpenAI) to blend speech + board content  
7) TTS (pyttsx3) per segment  
8) Results packaging (JSON, audio, frames)

## 5. Preprocessing Summary
- Frame sampling every 2–3s, JPEG quality 95, dedupe similar frames.
- Optional image preprocessing lives in `ocr/vision/ocr_preprocess.py` (not used in the main path).

## 6. Feature Engineering Summary
- Board text normalization and de-duplication per segment (`fusion/fusion_engine/fusion_inputs.py`).
- Semantic embeddings for search (OpenAI embeddings) when runs complete.
- Math-to-speech normalization for smoother TTS (`fusion/fusion_engine/math_to_speech.py`).

## 7. Installation
```bash
python -m venv .venv
.venv\Scripts\activate          # on Windows
pip install -r requirements.txt
# Ensure OPENAI_API_KEY and ASSEMBLYAI_API_KEY are set in .env
```

## 8. Running Backend
```bash
python app.py
# then open http://127.0.0.1:8000
```

## 9. Run Pipeline on Test Video
Use the batch script to process all videos in `data/test_videos/`:
```bash
python scripts/run_all_experiments.py
```
Or run a single video:
```bash
python - <<\"PY\"
from pathlib import Path
from run_complete_pipeline import run_pipeline
video = Path(\"data/test_videos/test.mp4\")  # or any mp4/mov/m4v path
run_pipeline(youtube_url=\"\", duration=None, local_video_path=video)
PY
```
Results land under `test_output/runs/<run_id>/`.

## 10. Evaluation
- Inspect `test_output/runs/<run_id>/complete_results.json` for segment/frame/board alignment and audio paths.
- Fusion and OCR artifacts: `fusion_results.json`, `ocr_results.json`, `frames/` and `frames_kept/`.

## 11. Reproducibility
- Determinism depends on external APIs (OpenAI, AssemblyAI); set fixed models and reuse the same video input.
- Summaries of experiments are written to `test_output/experiment_summary.json` by the batch runner.

## 12. Docker
Basic workflow (after adding your API keys to `.env`):
```bash
docker build -t classcast .
docker run --env-file .env -p 8000:8000 classcast
```
Then browse to http://127.0.0.1:8000.

## 13. Advanced Features
- Semantic search over fused transcript + board text.
- Q&A chat endpoint grounded in run results.
- Multilingual podcast synthesis via OpenAI TTS (single audio per language).
- Frame de-duplication and board-aware fusion to reduce noise.

## 14. Folder Structure
- `app.py` — FastAPI server and routes
- `run_complete_pipeline.py` — end-to-end pipeline
- `scripts/` — batch runners (e.g., `run_all_experiments.py`)
- `audio_pipeline/`, `frame_extraction/`, `ocr/`, `fusion/`, `TTS/`, `utils/` — stage-specific modules
- `templates/`, `static/` — frontend UI
- `data/` — sample videos and OCR test images
- `test_output/` — per-run artifacts (frames, OCR, transcript, fusion, audio, results JSON)
