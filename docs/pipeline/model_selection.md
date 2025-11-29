
 ASR Model Comparison

| **Model**            | **Tested** | **WER (↓)** | **Timestamps** | **Cost** | **Pros** | **Cons** | **Decision** |
|----------------------|------------|--------------|----------------|-----------|----------|-----------|--------------|
| **AssemblyAI**       | Yes        |  ~15-19%         | ✔ Sentence-level | Medium  | High accuracy, robust, easy API | Paid | Selected
| Whisper API (OpenAI) | Considered | ~20-25%      | ✘ None          | Medium  | Simple API | No segmentation | Not chosen |
| Whisper Local        | Considered | ~22-28%      | ✔ Manual        | Free     | Free, customizable | Requires GPU | Not chosen |

. AssemblyAI was chosen as our ASR engine, although AssemblyAI and Whisper API (OpenAI) both performed well, AssemblyAI api cost was much more efficient since it charges almost a constant price which is 0.15$ an hour regardless of the number of words said by the instructor, while Whisper charges based on number of characters, tokens and calls. The Whisper local api performed worse than both other apis


OCR Engine Comparison
-------------------------------------------------------------
**OpenAI Vision (4o-mini)**| Tested: Yes   | Accuracy: High (best)   | Math Handling: Excellent   | Cost: Medium–High |
Google Vision OCR          | Tested: Yes | Accuracy: Medium        | Math Handling: Weak        | Cost: Medium      | 
Tesseract (local)          | Tested: Yes   | Accuracy: Very Low      | Math Handling: Very Weak   | Cost: Free        | 
-------------------------------------------------------------

.OpenAI vision outperformed all other ocr engines we tested expecially for symbols (math symbols). Athough cost was relatively high compared to other engines, we did some preprocessing that decreased it so much. We took a frame every 5 seconds then applied the SSIM method to filter same or almost same images which decreased the number of frames sent to OpenAI by 40-50% depending on the lecture video.
Price before processing for 1 hour: 2-2.7$
After setting fps to 0.2 (1 frame per 5 seconds) and dedupllicating frames: 0.15-0.3$

Fusion Engine:

. For fusion, OpenAI was also used, but we were abledo decrease cost to a very low amount (around 10 to 20 cents) by letting it do all things it has to do in 1 call (cleaning transcript, merge and formatting)

Text to Speech:

| Feature     | Quality                   |    Price                         |
| ----------- | ------------------------- | -------------------------------- |
| OpenAI      | High, natural, human-like | ~0.8$ for an hour                |
| **pyttsx3** | Almost the same as OpenAI | Free                             |
