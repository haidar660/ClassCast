# Quick Start Guide

Get started with frame extraction in 3 easy steps!

## Installation

```bash
# 1. Navigate to the package directory
cd frame_extraction_package

# 2. Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### Extract frames from your video:

```bash
python extract_frames.py your_video.mp4
```

That's it! Frames will be saved to the `frames/` directory.

## Common Commands

### Extract with custom interval

```bash
python extract_frames.py video.mp4 --interval 1
```

### Extract specific time range

```bash
python extract_frames.py video.mp4 --start 56 --end 174
```

### High quality for OCR

```bash
python extract_frames.py video.mp4 --quality 98
```

## What You Get

After running the tool, you'll have:

1. **Frame images** in the output directory (e.g., `frames/`)

   - Named like: `frame_0001_t2.0s.jpg`

2. **Metadata JSON** file with timestamps and paths
   - Location: `frames/frames_metadata.json`

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [example_usage.py](example_usage.py) for integration examples
- Use extracted frames with OCR tools for text recognition

## Need Help?

```bash
python extract_frames.py --help
```
