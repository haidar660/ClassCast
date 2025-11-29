# Track Alignment

- **Vision:** OpenAI Vision (GPT-4o-mini) extracts board/slide text from frames.
- **Audio:** AssemblyAI provides sentence-level ASR with timestamps.
- **Text:** GPT-4o-mini fuses speech + board; OpenAI `tts-1` and pyttsx3 synthesize audio; `text-embedding-3-small` powers semantic search.
- The pipeline grounds each modality via timestamp alignment, producing multimodal outputs (fused text, searchable embeddings, podcasts).
