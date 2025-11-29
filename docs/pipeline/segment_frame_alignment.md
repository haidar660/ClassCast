# Segment-Frame Alignment

- **Goal:** Attach each sentence-level ASR segment to the visual state shown during that speech.
- **Method:** `find_closest_frame` picks the frame whose timestamp is closest to the segment midpoint.
- **Board elements:** `build_board_elements` selects the nearest OCR result by timestamp, cleans/dedupes text, and attaches at most one board snippet per segment.
- **Outputs:** Aligned frame paths and board text stored alongside each segment in `complete_results.json`.
- **Why midpoint:** Minimizes drift between speaking and writing by anchoring to the temporal center of each sentence.
