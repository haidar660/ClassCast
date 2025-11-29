The following is the preprocsseing done on each part of the pipeline:
. Automatic Speech Recognition (ASR):
1) Audio cleanup: AssemblyAI automatically performs noise suppression, removes background hum and echo, filters out low-quality frequencies, normalizes loudness, and converts stereo recordings into a clean mono signal to stabilize transcription quality.
2) Smart segmentation (VAD): Built-in voice activity detection identifies where real speech occurs, removes long silences or dead air, and segments the audio into optimal-length chunks so the model only processes meaningful speech.
3) Automatic adaptation: The system transparently handles any audio format or sample rate, performs language detection when unspecified, and runs internal alignment to produce accurate word- and sentence-level timestamps without user preprocessing.
4) Text refinement: After recognition, AssemblyAI automatically inserts punctuation and capitalization, formats numbers, and lightly cleans the output (e.g., removing filler sounds) to produce readable, well-structured sentences.

. Optical Speech Recognition (OCR)
1) Sampler interval tuning: We changed the sampling frame interval from 2 seconds to 5 seconds, which avoided repition and hallucination of the pipeline and reduced cost (less frames sent to OpenAI -> less cost)
2) Frames Deduplication: We used the SSIM method to deduplicate frames that look exactly or almost the same (1 word difference for example), which further reduced the number of frames by removing duplicates (unnecessary ones) by around 40 to 50% which led to a huge drop in cost.
3) Image normalization: The model automatically standardizes input frames by resizing them to its internal resolution, correcting aspect ratios, normalizing pixel ranges, and converting color formats—ensuring consistent image quality before text extraction.

. Fusion:
1) Strict prompts: Fusion is instructed not to paraphrase or invent information. It only adds board text if explicitly relevant to the spoken sentence.
