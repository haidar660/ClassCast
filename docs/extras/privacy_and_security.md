# Privacy and Security

- **Secrets:** `.env` holds API keys; never commit it (gitignored).
- **Run isolation:** each `/api/runs` request writes to `test_output/runs/<uuid>/`, avoiding cross-user leakage.
- **File serving guard:** `/files/{path}` validates paths under the project root to prevent traversal.
- **Retention:** artifacts persist on disk until cleaned; remove run folders with sensitive content after use.
- **External calls:** videos processed locally; only AssemblyAI/OpenAI receive audio/text needed for ASR/OCR/TTS.
