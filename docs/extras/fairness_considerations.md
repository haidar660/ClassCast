# Fairness Considerations

- **Accents/speech styles:** AssemblyAI sentence ASR handles varied accents; short-fragment filtering avoids bias from broken sentences.
- **Language coverage:** Podcasts can be synthesized in multiple languages; translation prompt preserves content (no summarization) to avoid loss for non-English users.
- **Search bias:** Embedding thresholding reduces spurious hits; expose low-similarity warnings if needed.
- **Data diversity:** Expand samples to diverse handwriting styles and board colors so OCR does not favor only clean whiteboards.
