# Reproducibility Guide

This document explains exactly how to reproduce the full ClassCast pipeline results, experiments, and evaluation metrics.

Reproducibility means that if someone clones this repository, installs the environment, and uses the same input videos and configuration, they will obtain the same behavior and similar results.

---


How to Reproduce the Exact Experiments From the Report
git clone <repo_url>
cd classcast

# 1. Create environment
pip install -r requirements.txt

# 2. Create your .env
cp .env.example .env
# fill in API keys

# 3. Ensure test videos exist
ls data/test_videos/

# 4. Run all experiments
python scripts/run_all_experiments.py


All results will appear under:

test_output/runs/

# 1. Environment

## Python & OS
- Python **3.11** (recommended)
- Tested on:
  - Windows 11
  - Ubuntu 22.04

## Dependencies
All dependencies are fully pinned in:

requirements.txt


2. API Keys & Configuration:
all in:
.env.example file


3. Test Dataset

All experiments use fixed videos stored in:

data/test_videos/


If a video is too large to include, its download instructions are described in:

data/README_data.md


Each experiment run includes:

the video filename

the segment duration

the exact source URL (if downloaded from YouTube)

This ensures that anyone can regenerate the input data.

4. Running the Full Pipeline

The full pipeline is executed using:

python scripts/run_all_experiments.py


This script:

Automatically detects all videos in data/test_videos/

Runs the complete pipeline for each

Saves outputs under:

test_output/runs/<run_id>/


Each run directory includes:

OCR JSON

Transcript JSON

Frame metadata

Fused text results

Generated TTS audio

A consolidated complete_results.json file

A copy of the configuration used for the run

This enables exact reproduction of every experiment.


Limitation:
Because the project depends on external APIs (OpenAI, AssemblyAI), some minor variations may occur over time due to backend updates.