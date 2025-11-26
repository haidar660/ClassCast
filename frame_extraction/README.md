# ClassCast Frame Extraction Tool

Standalone frame extraction utility for extracting frames from video lectures at regular intervals. This tool is part of the ClassCast project for converting video lectures into podcast-style audio content.

## Features

- Extract frames at configurable intervals (e.g., every 2 seconds)
- High-quality JPEG output with adjustable quality settings
- Time range selection (extract only a portion of the video)
- Automatic metadata generation (JSON file with timestamps and paths)
- Progress tracking during extraction
- Cross-platform support (Windows, macOS, Linux)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. **Extract the package** to your desired location

2. **Install dependencies:**

```bash
# Navigate to the package directory
cd frame_extraction_package

# Install required packages
pip install -r requirements.txt
```

That's it! The tool is ready to use.

## Usage

### Basic Usage

Extract frames every 2 seconds (default):

```bash
python extract_frames.py your_video.mp4
```

This will:

- Create a `frames/` directory
- Extract frames every 2 seconds
- Save frames with 95% JPEG quality
- Generate `frames/frames_metadata.json` with timestamp information

### Common Use Cases

#### 1. High-Quality Extraction for OCR

```bash
python extract_frames.py lecture.mp4 --quality 98 --interval 1
```

Extract frames every 1 second with maximum quality (better for OCR/text recognition).

#### 2. Extract Specific Time Range

```bash
python extract_frames.py lecture.mp4 --start 56 --end 174
```

Extract only the portion from 56 seconds to 174 seconds.

#### 3. Custom Output Directory

```bash
python extract_frames.py lecture.mp4 --output my_frames
```

Save frames to `my_frames/` instead of the default `frames/` directory.

#### 4. Custom Frame Prefix

```bash
python extract_frames.py lecture.mp4 --prefix lecture_001
```

Name frames as `lecture_001_0001_t0.0s.jpg` instead of `frame_0001_t0.0s.jpg`.

#### 5. Batch Processing Example

```bash
python extract_frames.py video1.mp4 --output frames/video1
python extract_frames.py video2.mp4 --output frames/video2
python extract_frames.py video3.mp4 --output frames/video3
```

Process multiple videos with separate output directories.

## Command-Line Options

```
positional arguments:
  video_path            Path to input video file

optional arguments:
  -h, --help            Show this help message and exit

  -o OUTPUT, --output OUTPUT
                        Output directory for frames (default: frames)

  -i INTERVAL, --interval INTERVAL
                        Seconds between frame extractions (default: 2.0)

  -q QUALITY, --quality QUALITY
                        JPEG quality 0-100, higher is better (default: 95)

  -s START, --start START
                        Start extraction at this time in seconds

  -e END, --end END     Stop extraction at this time in seconds

  -p PREFIX, --prefix PREFIX
                        Prefix for frame filenames (default: frame)

  --no-metadata         Don't save metadata JSON file
```

## Output Format

### Extracted Frames

Frames are saved as JPEG images with descriptive filenames:

```
frame_0000_t0.0s.jpg    # Frame 0 at 0.0 seconds
frame_0001_t2.0s.jpg    # Frame 1 at 2.0 seconds
frame_0002_t4.0s.jpg    # Frame 2 at 4.0 seconds
...
```

### Metadata JSON

The `frames_metadata.json` file contains information about all extracted frames:

```json
{
  "total_frames": 60,
  "frames": [
    {
      "frame_id": "frame_0000",
      "frame_number": 0,
      "timestamp": 0.0,
      "absolute_timestamp": 0.0,
      "path": "/absolute/path/to/frames/frame_0000_t0.0s.jpg"
    },
    {
      "frame_id": "frame_0001",
      "frame_number": 1,
      "timestamp": 2.0,
      "absolute_timestamp": 2.0,
      "path": "/absolute/path/to/frames/frame_0001_t2.0s.jpg"
    }
  ]
}
```

**Field Descriptions:**

- `frame_id`: Unique identifier for the frame
- `frame_number`: Sequential frame number (0-indexed)
- `timestamp`: Time in seconds (relative to start_time if specified)
- `absolute_timestamp`: Time in seconds from the beginning of the original video
- `path`: Absolute file path to the frame image

## Integration with ClassCast Pipeline

This tool is designed to integrate seamlessly with the ClassCast video-to-podcast pipeline:

1. **Frame Extraction** (this tool) → Extract visual frames
2. **OCR Processing** → Extract text/math from frames
3. **ASR Transcription** → Extract speech from audio
4. **Fusion** → Combine visual and audio content
5. **TTS Generation** → Create podcast audio

### Python Integration Example

```python
import json
from pathlib import Path

# Load extracted frame metadata
with open("frames/frames_metadata.json") as f:
    data = json.load(f)

# Access frame information
for frame in data["frames"]:
    frame_id = frame["frame_id"]
    timestamp = frame["timestamp"]
    path = frame["path"]

    print(f"Frame {frame_id} at {timestamp}s: {path}")

    # Use frame for OCR, analysis, etc.
    # ocr_result = perform_ocr(path)
```

## Performance Tips

1. **Adjust interval based on content:**

   - Lecture with lots of board changes: `--interval 1` (every 1 second)
   - Slower-paced lecture: `--interval 3` (every 3 seconds)
   - Talking-head only: `--interval 5` (every 5 seconds)

2. **Quality settings:**

   - OCR/text recognition: `--quality 95` or higher
   - General viewing: `--quality 85`
   - Storage-constrained: `--quality 75`

3. **Disk space:**
   - A 10-minute video at 2-second intervals generates ~300 frames
   - At 95% quality, expect ~500KB per frame (150MB total)
   - At 75% quality, expect ~200KB per frame (60MB total)

## Troubleshooting

### "Could not open video file"

**Problem:** Video codec not supported by OpenCV.

**Solution:**

- Try converting video to MP4 with H.264 codec:
  ```bash
  ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
  ```

### "ModuleNotFoundError: No module named 'cv2'"

**Problem:** OpenCV not installed.

**Solution:**

```bash
pip install opencv-python
```

### Frames appear blurry

**Problem:** Quality setting too low or video resolution is low.

**Solution:**

- Increase quality: `--quality 98`
- Check source video resolution
- Use higher-resolution source video

### Memory issues with large videos

**Problem:** Processing very long videos (>2 hours).

**Solution:**

- Process in segments using `--start` and `--end`
- Example:
  ```bash
  python extract_frames.py lecture.mp4 --start 0 --end 1800
  python extract_frames.py lecture.mp4 --start 1800 --end 3600
  ```

## System Requirements

### Minimum

- Python 3.8+
- 2GB RAM
- 500MB disk space (per 10-minute video)

### Recommended

- Python 3.10+
- 4GB RAM
- SSD storage for faster I/O

## Supported Video Formats

The tool supports any video format that OpenCV can read:

- MP4 (H.264, H.265)
- AVI
- MOV
- MKV
- WMV
- FLV
- WebM

For best compatibility, use MP4 with H.264 codec.

## License

This tool is part of the ClassCast project. See the main project repository for license information.

## Support

For issues, questions, or contributions, please refer to the main ClassCast project repository.

## Credits

Developed as part of the ClassCast video-to-podcast pipeline project.
