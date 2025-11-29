The following is the feature engineering done on each part of the pipeline:
. Automatic Speech Recognition (ASR):
1) We treat each ASR sentence as a feature unit, consisting of:
{ text, start_time, end_time, confidence }.
2) The midpoint timestamp is computed to align each sentence with its closest video frame.
3) Sentence boundaries from AssemblyAI provide natural linguistic segmentation, which works as high-level audio features.

. Optical Character Recognition:
1) Each extracted frame becomes a visual feature with:
{ frame_path, timestamp, OCR_text }.
2) Frames are sampled sparsely (every 5 seconds) to reduce noise and stabilize OCR-derived features.
3) OCR outputs are cleaned by removing repeated text, noisy fragments, and unstable symbols before fusion.
4) Only meaningful board text is retained as a visual feature to avoid misleading the fusion model.

. Fusion:
1) Each fusion input is constructed as a structured feature object:
{ segment_id, transcript, board_text, frame_path, timestamps }.
2) We explicitly remove low-value fragments to prevent the LLM from receiving noisy feature vectors.
3) Only one frame per segment is included to avoid multi-frame confusion.
4) Fusion batches (grouped segments) act as controlled multimodal feature windows, preventing cross-segment bleed.

Text to Speech (TTS):
1) Offline and deterministic: pyttsx3 runs locally, requires no GPU or internet, and produces identical outputs across runs—ideal for reproducibility.
2) Segment-level synthesis: Each fused segment is converted into a separate audio file. This keeps audio aligned with timestamps and allows flexible podcast assembly later.
3) Zero preprocessing required: The engine accepts unmodified fused text. We do not need noise removal, formatting changes, or phoneme preprocessing.
4) Fast preview mechanism: pyttsx3 enables quick playback of fused transcripts during development without incurring OpenAI TTS costs or delays.
5) Used for development & debugging: Local TTS is essential for verifying fusion accuracy, flow, and sentence timing before generating the final multilingual podcast.