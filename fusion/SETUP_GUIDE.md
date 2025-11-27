# Quick Setup Guide for ClassCast Fusion Package

## 🚀 Installation (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable loader
- `requests` - HTTP library
- `Pillow` - Image processing
- `colorama` - Enhanced console colors

### Step 2: Configure API Key
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### Step 3: Test the System
```bash
python test_fusion.py
```

**Expected output:**
```
================================================================================
CLASSCAST FUSION SYSTEM - QUICK TEST
================================================================================

✓ OpenAI API key found

📊 Test Data:
   - 4 transcript segments
   - 4 video frames
   - 4 board equations

🚀 Running batch fusion (batch_size=2)...
   This will make 2 API calls to OpenAI GPT-4o-mini
   With retry logic for rate limiting...

================================================================================
RESULTS: Original Transcript → Fused Podcast Script
================================================================================

[Segment 1] 0.0s - 3.0s
  📝 Original:  Let us examine this derivative
  📐 Board:     \frac{d}{dx}(x^2) = 2x
  🎙️  Fused:     Let us examine this derivative: the derivative with respect to x of x squared equals two x

[Segment 2] 3.0s - 6.0s
  📝 Original:  Now consider this limit expression
  📐 Board:     \lim_{x \to \infty} \frac{1}{x} = 0
  🎙️  Fused:     Now consider this limit expression: the limit as x approaches infinity of one over x equals zero

[Segment 3] 6.0s - 9.0s
  📝 Original:  We can simplify the integral
  📐 Board:     \int_0^1 x^2 dx = \frac{1}{3}
  🎙️  Fused:     We can simplify the integral: the integral from zero to one of x squared dx equals one third

[Segment 4] 9.0s - 12.0s
  📝 Original:  And finally this quadratic formula
  📐 Board:     x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}
  🎙️  Fused:     And finally this quadratic formula: x equals negative b plus or minus the square root of b squared minus four a c all over two a

================================================================================
SUMMARY
================================================================================
✓ Total segments processed:  4
✓ API calls made:            2
✓ Old method would need:     4 calls
✓ API calls saved:           2
✓ Efficiency gain:           50%

🎉 SUCCESS! Fusion system is working perfectly!
================================================================================
```

---

## 📝 Basic Usage

### Minimal Example
```python
from fusion.batch_fuse_segments import batch_fuse_segments

# Your data
segments = [
    {'text': 'Consider this integral', 'start': 0, 'end': 3}
]

frames = [
    {'path': 'frame.jpg', 'time': 1.5}
]

board_elements = [
    ['\\int_0^1 x^2 dx']
]

# Run fusion
fused = batch_fuse_segments(segments, frames, board_elements, batch_size=4)

print(fused[0])
# Output: "Consider this integral: the integral from zero to one of x squared dx"
```

### Using the Controller (Recommended)
```python
from fusion.fusion_controller import FusionController
from data_models import TranscriptSegment, FrameInfo

# Your data
segments = [
    TranscriptSegment(text="Let's solve this", start=0.0, end=5.0),
    # ... more segments
]

frames = [
    FrameInfo(path="frame_001.jpg", time=2.5),
    # ... more frames
]

# Initialize controller
controller = FusionController(batch_size=4)

# Run fusion
fused_sentences = controller.fuse_pipeline(segments, frames)

# Use results
for i, (seg, fused) in enumerate(zip(segments, fused_sentences), 1):
    print(f"{i}. [{seg.start:.1f}s] {fused}")
```

---

## 🔧 Troubleshooting

### "Invalid API key"
**Problem:** OpenAI API key is missing or incorrect

**Solution:**
1. Check `.env` file exists in the same directory
2. Verify it contains: `OPENAI_API_KEY=sk-proj-...`
3. Get a valid key from https://platform.openai.com/api-keys
4. Ensure no extra spaces or quotes around the key

### "Rate limit exceeded"
**Problem:** Too many requests too quickly

**Solution:**
The system has built-in retry logic, but you can:
1. Reduce batch_size to 2 or 3
2. Wait a few seconds between runs
3. Check your API tier limits at https://platform.openai.com/account/limits

### "ModuleNotFoundError"
**Problem:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Import errors
**Problem:** Running from wrong directory

**Solution:**
```bash
# Make sure you're in the fusion_package directory
cd fusion_package
python test_fusion.py
```

---

## 💰 Cost Estimate

**GPT-4o-mini Pricing:**
- Input: $0.00015 / 1K tokens
- Output: $0.00060 / 1K tokens

**Typical Usage:**
- 1 segment ≈ 200 tokens (with batch_size=4) → **$0.00005 per segment**
- 100 segments = 25 batches → **$0.005 total** (half a cent!)
- 1000 segments = 250 batches → **$0.05 total** (5 cents!)

The test script costs approximately **$0.0002** (0.02 cents) per run.

---

## 📦 What's Included

```
fusion_package/
├── README.md              # Full documentation
├── SETUP_GUIDE.md        # This file
├── PACKAGE_CONTENTS.md   # File listing
├── requirements.txt       # Dependencies
├── test_fusion.py        # Test script
├── .env.example          # API key template
├── fusion/               # Core fusion engine (3 files)
├── models/               # Data structures (1 file)
├── utils/                # Utilities (2 files)
├── data_models.py        # Legacy data models
└── pairing.py           # Segment-frame matching
```

**Total:** 15 Python files + 4 documentation files

---

## ✅ Verification Checklist

Before sharing with your friend, verify:

- [ ] `.env` file is NOT included (only `.env.example`)
- [ ] All files are present (15 Python files)
- [ ] `requirements.txt` exists
- [ ] Test script runs successfully
- [ ] No personal API keys in any files
- [ ] README.md is included

To create a shareable package:
```bash
# Navigate to parent directory
cd ..

# Create zip file (Windows)
tar -czf fusion_package.zip fusion_package/

# Or use GUI: Right-click fusion_package → Send to → Compressed (zipped) folder
```

---

## 🎯 Next Steps

1. **Test locally**: Run `python test_fusion.py`
2. **Integrate**: Import `FusionController` into your pipeline
3. **Customize**: Adjust `batch_size` based on your rate limits
4. **Scale**: Process hundreds of segments efficiently

---

**Version:** 1.0 Final
**Last Updated:** 2025-11-26
**Status:** ✅ Production Ready
