# Setup Instructions

Complete setup guide for the ClassCast Frame Extraction Tool.

## For Windows

### Step 1: Install Python

1. Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Install Dependencies

```cmd
cd frame_extraction_package
pip install -r requirements.txt
```

### Step 3: Test Installation

```cmd
python test_installation.py
```

### Step 4: Extract Frames

```cmd
python extract_frames.py your_video.mp4
```

## For macOS

### Step 1: Install Python

Python 3 is usually pre-installed on macOS. Check version:

```bash
python3 --version
```

If not installed or version is old:

```bash
# Install using Homebrew
brew install python3
```

### Step 2: Install Dependencies

```bash
cd frame_extraction_package
pip3 install -r requirements.txt
```

### Step 3: Test Installation

```bash
python3 test_installation.py
```

### Step 4: Extract Frames

```bash
python3 extract_frames.py your_video.mp4
```

## For Linux (Ubuntu/Debian)

### Step 1: Install Python

```bash
sudo apt update
sudo apt install python3 python3-pip
```

Verify:

```bash
python3 --version
```

### Step 2: Install Dependencies

```bash
cd frame_extraction_package
pip3 install -r requirements.txt
```

### Step 3: Test Installation

```bash
python3 test_installation.py
```

### Step 4: Extract Frames

```bash
python3 extract_frames.py your_video.mp4
```

## Troubleshooting

### "pip: command not found"

**Windows:**

```cmd
python -m pip install -r requirements.txt
```

**macOS/Linux:**

```bash
python3 -m pip install -r requirements.txt
```

### Permission denied errors (macOS/Linux)

Try installing to user directory:

```bash
pip3 install --user -r requirements.txt
```

### OpenCV installation fails

Try installing with pre-built wheels:

```bash
pip install opencv-python-headless
```

### Video won't open

Install ffmpeg:

**Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html)

**macOS:**

```bash
brew install ffmpeg
```

**Linux:**

```bash
sudo apt install ffmpeg
```

## Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated:

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To deactivate:

```bash
deactivate
```

## Verification Checklist

After setup, verify:

- [ ] Python 3.8+ installed
- [ ] pip working
- [ ] OpenCV installed (`python -c "import cv2; print(cv2.__version__)"`)
- [ ] test_installation.py passes all tests
- [ ] Can run `python extract_frames.py --help`

## Next Steps

Once setup is complete:

1. Read [QUICKSTART.md](QUICKSTART.md) for basic usage
2. Read [README.md](README.md) for detailed documentation
3. Check [example_usage.py](example_usage.py) for code examples

## Getting Help

If you encounter issues:

1. Run `python test_installation.py` to diagnose problems
2. Check that you're in the correct directory
3. Verify Python version with `python --version`
4. Try reinstalling dependencies: `pip install --upgrade -r requirements.txt`
