# ClassCast Fusion System

**Final Production Version** - Batch fusion with exponential backoff retry logic

## Overview

This package contains the complete, production-ready fusion system that combines:
- **ASR Transcript** (what the professor says)
- **OCR Board Text** (LaTeX mathematical notation from the board)
- **Visual Frames** (screenshots of the board)

Into **podcast-ready spoken sentences** with no LaTeX symbols.

## Key Features

✅ **Batch Processing** - Process 4 segments per API call (75% cost reduction)
✅ **Retry Logic** - Exponential backoff for rate limits (5 attempts, up to 31s wait)
✅ **Math Conversion** - 68+ LaTeX symbols → natural speech
✅ **Vision + Text** - GPT-4o-mini combines transcript + board screenshots
✅ **Order Preservation** - Maintains chronological sequence

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your OpenAI API key
cp .env.example .env
# Edit .env and add your API key:
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

## Quick Start

```bash
# Run the test script (no external data needed)
python test_fusion.py
```

This will:
- Test the fusion system with 4 sample segments
- Make 2 API calls to OpenAI (batch_size=2)
- Show before/after comparison
- Display efficiency statistics

## Usage

### Basic Usage

```python
from fusion.batch_fusion import batch_fuse_segments

# Your data
segments = [
    {'text': 'Let us examine this derivative', 'start': 0, 'end': 3},
    {'text': 'Consider this limit', 'start': 3, 'end': 6}
]

frames = [
    {'path': 'frame_0.jpg', 'time': 1.5},
    {'path': 'frame_1.jpg', 'time': 4.5}
]

board_elements = [
    ['d/dx(x^2) = 2x'],
    ['lim_{x→∞} 1/x = 0']
]

# Run fusion
fused = batch_fuse_segments(segments, frames, board_elements, batch_size=4)

# Results
for sentence in fused:
    print(sentence)
# Output:
# "Let us examine this derivative: the derivative with respect to x of x squared equals two x"
# "Consider this limit: the limit as x approaches infinity of one over x equals zero"
```

### Advanced Usage with Controller

```python
from fusion.fusion_controller import FusionController
from data_models import TranscriptSegment, FrameInfo

# Load your data
segments = [
    TranscriptSegment(text="...", start=0.0, end=5.0),
    # ... more segments
]

frames = [
    FrameInfo(path="frame_0.jpg", time=2.5),
    # ... more frames
]

# Initialize controller
controller = FusionController(batch_size=4)

# Run fusion pipeline
fused_sentences = controller.fuse_pipeline(segments, frames)

# Use results
for seg, fused in zip(segments, fused_sentences):
    print(f"[{seg.start:.1f}s] {fused}")
```

## File Structure

```
fusion_package/
├── README.md                    # This file
├── requirements.txt             # Dependencies
├── .env.example                 # API key template
├── test_fusion.py              # Quick test script
│
├── fusion/                      # Core fusion module
│   ├── __init__.py
│   ├── batch_fusion.py         # ⭐ Main: Batching + retry logic
│   ├── fusion_controller.py    # ⭐ High-level orchestration
│   └── math_to_speech.py       # ⭐ LaTeX → spoken text
│
├── models/                      # Data classes
│   ├── __init__.py
│   └── segments.py             # TranscriptSegment, FusedSegment, etc.
│
├── utils/                       # Utilities
│   ├── __init__.py
│   ├── logging_utils.py        # Logger setup
│   └── latex_converter.py      # LaTeX cleaning
│
├── data_models.py              # Legacy data structures
└── pairing.py                  # Segment-frame matching
```

## How It Works

### 1. Batch Processing

Instead of 100 individual API calls, we send batches of 4:
- **Old**: 100 segments = 100 API calls (~2 minutes, $0.50)
- **New**: 100 segments ÷ 4 = 25 API calls (~30 seconds, $0.125)
- **Efficiency**: 75% reduction in cost and time

### 2. Retry Logic

```python
def _fuse_batch_with_retry(batch, max_retries=5):
    for attempt in range(max_retries):
        try:
            return call_openai(batch)
        except RateLimitError:
            delay = 2 ** attempt  # Exponential backoff
            time.sleep(delay)     # 1s, 2s, 4s, 8s, 16s
```

### 3. Math-to-Speech Conversion

**68+ Symbol Mappings**:
- `x^2` → "x squared"
- `∫₀¹ f(x)dx` → "the integral from zero to one of f of x dx"
- `lim_{x→∞}` → "the limit as x approaches infinity"
- `√x` → "the square root of x"
- `∂/∂x` → "the partial derivative with respect to x"

### 4. Example Transformation

**Input**:
- Transcript: "Let us examine this derivative"
- Board: `\frac{d}{dx}(x^2) = 2x`

**Output**:
- Fused: "Let us examine this derivative: the derivative with respect to x of x squared equals two x"

## API Costs

**GPT-4o-mini Pricing**:
- Input: $0.00015 / 1K tokens
- Output: $0.00060 / 1K tokens
- Typical batch: ~500 input + 200 output tokens = **~$0.0002 per batch**
- **Cost per segment**: ~$0.00005 (with batch_size=4)

**Example**:
- 100 segments = 25 batches = **$0.005 total** (half a cent!)

## Error Handling

The system handles:
- ✅ Rate limits (429 errors) → Auto-retry with exponential backoff
- ✅ Malformed responses → Fallback JSON parsing
- ✅ Missing images → Graceful degradation
- ✅ API failures → Error messages in output

## Integration Example

```python
# Full pipeline
from fusion.fusion_controller import FusionController
from pairing import pair_segments_with_context

# 1. Load data (your implementations)
segments = load_asr_segments(video_path, end_time=160.0)
frames = load_frames(video_path, end_time=160.0)

# 2. Pair segments with frames
paired_data = pair_segments_with_context(segments, frames)

# 3. Run batch fusion
controller = FusionController(batch_size=4)
fused_sentences = controller.fuse_pipeline(
    segments=segments,
    frames=[item['frame'] for item in paired_data]
)

# 4. Build output JSON for UI
results = {
    "segments": [
        {
            "id": i + 1,
            "start": seg.start,
            "end": seg.end,
            "transcript": seg.text,
            "frame_path": paired_data[i]['frame'].path,
            "fused_sentence": fused_sentences[i]
        }
        for i, seg in enumerate(segments)
    ],
    "final_podcast_script": fused_sentences
}

# 5. Save
import json
with open("output.json", 'w') as f:
    json.dump(results, f, indent=2)
```

## Troubleshooting

### "Invalid API key"
- Check your `.env` file has `OPENAI_API_KEY=sk-proj-...`
- Verify the key at https://platform.openai.com/api-keys

### "Rate limit exceeded" (even with retries)
- Your API tier may have lower limits
- Reduce `batch_size` to 2 or 3
- Increase `max_retries` in batch_fusion.py

### "Image encoding failed"
- Check that frame paths exist
- For testing without images, use dummy paths (text-based fusion works)

## Support

For issues or questions:
1. Check the test script output for diagnostic info
2. Review error messages in console (detailed logging)
3. Verify API key has credits at https://platform.openai.com/usage

## License

MIT License - Part of ClassCast educational content pipeline

---

**Version**: 1.0 (Final Production)
**Last Updated**: 2025-11-26
**Tested With**: OpenAI GPT-4o-mini, Python 3.8+
