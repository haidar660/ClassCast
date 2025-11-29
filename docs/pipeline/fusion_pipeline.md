# Fusion Pipeline

- **Purpose:** Merge ASR sentences with contemporaneous board content without paraphrasing.
- **Controller:** `fusion.fusion_engine.fusion_controller.FusionController` calling `batch_fuse_segments`.
- **Batching:** Default batch_size=4 to reduce API calls and keep order; exponential backoff on failures.
- **Prompt rules:** Preserve professor wording; only weave board text when explicitly referenced; avoid “on the board/image”; JSON response enforced.
- **Board handling:** Board text is pre-cleaned and converted to spoken form (`merge_speech_and_board_naturally`) while avoiding duplicates.
- **Outputs:** `fusion_results.txt` and `fusion_results.json` with fused text per segment; clauses deduped to prevent repetition.
- **Failure mode:** If a batch fails, items get an error marker string but the pipeline continues.
