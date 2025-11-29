# Frame Extraction

- **Input:** Source video (YouTube download or upload).
- **Tool:** `frame_extraction.extract_frames` (OpenCV).
- **Sampling:** Interval seconds → frame stride; optional start/end trim for YouTube clips.
- **Outputs:** JPEG frames with timestamps plus `frames_kept.json` metadata.
- **Dedup:** Histogram correlation + pixel-diff checks skip near-identical frames while keeping periodic safeguards for gradual board changes.
- **Why:** Reduce redundant OCR calls and keep frames aligned to speech midpoints.
