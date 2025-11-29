# OCR Pipeline

- **Input:** Deduped frames sorted by timestamp.
- **Model:** OpenAI Vision (GPT-4o-mini) via `ocr.visual_pipeline.ocr_openai.perform_ocr_on_frames`.
- **Pre-filtering:** Skip frames when histogram similarity is high and pixel-change ratio is below threshold to avoid re-reading static boards.
- **Line dedup:** `_dedupe_lines` suppresses repeated board lines across frames; LaTeX cleaned to text.
- **Output:** `ocr_results.json` with per-frame text, method tags, and confidence placeholder.
- **Limitations:** Vision-only; add specialist math OCR or board crops for messy handwriting or dense formulas.
