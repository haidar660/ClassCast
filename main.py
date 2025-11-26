"""
FastAPI backend for ClassCast: From Whiteboard to Podcast.
Provides web UI for uploading videos and running the pipeline.
"""
import json
import shutil
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils.logging_utils import setup_logger, log_step
from utils.paths import (
    ensure_data_directories,
    get_file_prefix,
    INPUT_VIDEO_DIR,
    STATIC_DIR,
    TEMPLATES_DIR,
    get_audio_path,
    get_transcript_json_path,
    get_ocr_json_path,
    get_fused_json_path,
    get_markdown_path,
    get_pdf_path,
    get_tts_audio_path
)

from audio_pipeline.extract_audio import extract_audio_from_video
from audio_pipeline.asr_assemblyai import transcribe_audio
from visual_pipeline.frame_extractor import extract_frames
from visual_pipeline.ocr_tesseract import perform_ocr_on_frames  # Using Tesseract instead of EasyOCR
from fusion.fuse_streams import fuse_asr_and_ocr
from export.export_markdown import export_to_markdown
from export.export_pdf import export_to_pdf
from export.tts_pyttsx3 import generate_podcast_audio

logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ClassCast", description="From Whiteboard to Podcast")

# Ensure data directories exist
ensure_data_directories()

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Handle video upload and run the complete pipeline.

    Args:
        file: Uploaded video file

    Returns:
        Redirect to result page
    """
    logger.info("=" * 80)
    logger.info("NEW VIDEO UPLOAD")
    logger.info("=" * 80)

    # Validate file
    if not file.filename.endswith('.mp4'):
        raise HTTPException(status_code=400, detail="Only .mp4 files are supported")

    # Generate prefix from filename
    prefix = get_file_prefix(file.filename)
    logger.info(f"Processing video: {file.filename} (prefix: {prefix})")

    # Save uploaded file
    video_path = INPUT_VIDEO_DIR / file.filename
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info(f"Video saved to: {video_path}")

    try:
        # Run complete pipeline
        run_pipeline(video_path, prefix)

        # Redirect to result page
        return RedirectResponse(url=f"/result/{prefix}", status_code=303)

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


def run_pipeline(video_path: Path, prefix: str):
    """
    Run the complete ClassCast pipeline.

    Args:
        video_path: Path to input video
        prefix: File prefix for outputs
    """
    # Step 1: Extract Audio
    log_step(logger, "Extract Audio")
    audio_path = get_audio_path(prefix)
    extract_audio_from_video(video_path, audio_path)

    # Step 2: Transcribe Audio (ASR)
    log_step(logger, "Transcribe Audio (AssemblyAI)")
    asr_segments = transcribe_audio(audio_path)

    # Save ASR results
    transcript_json_path = get_transcript_json_path(prefix)
    with open(transcript_json_path, 'w', encoding='utf-8') as f:
        json.dump(asr_segments, f, indent=2)
    logger.info(f"Transcript saved to: {transcript_json_path}")

    # Step 3: Extract Frames
    log_step(logger, "Extract Frames")
    frames_metadata = extract_frames(video_path, prefix)

    # Step 4: Perform OCR
    log_step(logger, "Perform OCR (Tesseract)")
    ocr_results = perform_ocr_on_frames(frames_metadata)

    # Save OCR results
    ocr_json_path = get_ocr_json_path(prefix)
    with open(ocr_json_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2)
    logger.info(f"OCR results saved to: {ocr_json_path}")

    # Step 5: Fuse ASR and OCR
    log_step(logger, "Fuse ASR and OCR Streams")
    fused_segments = fuse_asr_and_ocr(asr_segments, ocr_results)

    # Save fused results
    fused_json_path = get_fused_json_path(prefix)
    with open(fused_json_path, 'w', encoding='utf-8') as f:
        json.dump(fused_segments, f, indent=2)
    logger.info(f"Fused data saved to: {fused_json_path}")

    # Step 6: Export to Markdown
    log_step(logger, "Export to Markdown")
    markdown_path = get_markdown_path(prefix)
    export_to_markdown(fused_segments, markdown_path)

    # Step 7: Export to PDF
    log_step(logger, "Export to PDF")
    pdf_path = get_pdf_path(prefix)
    export_to_pdf(fused_segments, pdf_path)

    # Step 8: Generate TTS Audio (optional)
    log_step(logger, "Generate TTS Podcast Audio")
    tts_path = get_tts_audio_path(prefix)
    generate_podcast_audio(fused_segments, tts_path)

    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETE!")
    logger.info("=" * 80)


@app.get("/result/{prefix}", response_class=HTMLResponse)
async def show_result(request: Request, prefix: str):
    """
    Display the results page with transcript and download links.

    Args:
        request: FastAPI request object
        prefix: File prefix

    Returns:
        Rendered result page
    """
    # Load fused data
    fused_json_path = get_fused_json_path(prefix)

    if not fused_json_path.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    with open(fused_json_path, 'r', encoding='utf-8') as f:
        fused_segments = json.load(f)

    # Check which files exist
    markdown_exists = get_markdown_path(prefix).exists()
    pdf_exists = get_pdf_path(prefix).exists()
    tts_exists = get_tts_audio_path(prefix).exists()

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "prefix": prefix,
            "segments": fused_segments,
            "markdown_exists": markdown_exists,
            "pdf_exists": pdf_exists,
            "tts_exists": tts_exists
        }
    )


@app.get("/download/{prefix}/markdown")
async def download_markdown(prefix: str):
    """Download Markdown transcript."""
    markdown_path = get_markdown_path(prefix)

    if not markdown_path.exists():
        raise HTTPException(status_code=404, detail="Markdown file not found")

    return FileResponse(
        path=markdown_path,
        filename=f"{prefix}.md",
        media_type="text/markdown"
    )


@app.get("/download/{prefix}/pdf")
async def download_pdf(prefix: str):
    """Download PDF transcript."""
    pdf_path = get_pdf_path(prefix)

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=pdf_path,
        filename=f"{prefix}.pdf",
        media_type="application/pdf"
    )


@app.get("/download/{prefix}/tts")
async def download_tts(prefix: str):
    """Download TTS audio podcast."""
    tts_path = get_tts_audio_path(prefix)

    if not tts_path.exists():
        raise HTTPException(status_code=404, detail="TTS audio file not found")

    return FileResponse(
        path=tts_path,
        filename=f"{prefix}_podcast.mp3",
        media_type="audio/mpeg"
    )


@app.get("/debug-ocr", response_class=HTMLResponse)
async def debug_ocr_page(request: Request):
    """
    Debug page for OCR + Fusion testing.

    Loads and displays results from the test pipeline.
    """
    results_json = Path("data/fusion_results/ocr_fusion_debug_results.json")

    if not results_json.exists():
        # Results not yet generated
        return templates.TemplateResponse(
            "debug_ocr.html",
            {
                "request": request,
                "results": [],
                "has_results": False,
                "message": "No results found. Run the debug pipeline first: python test_ocr_fusion_debug.py"
            }
        )

    # Load results
    with open(results_json, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Calculate summary statistics
    total = len(results)
    successful = sum(1 for r in results if 'error' not in r or not r.get('error'))
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0

    return templates.TemplateResponse(
        "debug_ocr.html",
        {
            "request": request,
            "results": results,
            "has_results": True,
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }
    )


@app.post("/debug-ocr/run")
async def run_debug_pipeline():
    """
    Run the OCR debug pipeline on all test frames.
    """
    import subprocess

    try:
        # Run the test script
        result = subprocess.run(
            ["python", "test_ocr_fusion_debug.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode == 0:
            return {"status": "success", "message": "Pipeline completed successfully"}
        else:
            return {
                "status": "error",
                "message": f"Pipeline failed with exit code {result.returncode}",
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Pipeline timed out after 5 minutes"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ClassCast server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
