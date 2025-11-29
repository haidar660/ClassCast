# Explainability

- Each fused segment retains `frame_path`, `frame_url`, timestamps, and attached board text so reviewers can trace what the model saw.
- `test_output/runs/<id>/` stores frames, OCR, transcripts, and fusion JSON for end-to-end inspection.
- Future enhancement: UI overlay to highlight which frame/board lines influenced each fused sentence and a “compare OCR vs fused” toggle.
- Debug tip: compare `fusion_results.json` with `transcript.json` and `ocr_results.json` to spot hallucinations or omissions.
