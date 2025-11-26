"""
OpenAI-only OCR module using GPT-4o vision.

We removed all other OCR engines (Tesseract, EasyOCR, Google Vision, Pix2Text, etc.)
and rely solely on OpenAI for board/slide text extraction.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import base64
import os
import requests

from utils.logging_utils import setup_logger

logger = setup_logger(__name__)

DEFAULT_OCR_MODEL = os.environ.get("CLASSCAST_OCR_MODEL", "gpt-4o-mini")


def _call_openai_vision(image_path: Path, model: str) -> Dict[str, Any]:
    """
    Call OpenAI vision model to extract text from an image.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set; cannot run OpenAI OCR.")

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert OCR assistant with computer vision capabilities. "
                    "Extract ALL visible text. Preserve line breaks. "
                    "Use LaTeX for math notation where appropriate. "
                    "Do not add commentary—return only the extracted text."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                ],
            },
        ],
        "max_tokens": 1500,
        "temperature": 0.0,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    logger.info(f"Calling OpenAI vision OCR (model={model}) for {image_path}")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(f"OpenAI OCR error {response.status_code}: {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()
    usage = result.get("usage", {})

    logger.debug(f"OCR extracted {len(content)} characters; tokens used: {usage.get('total_tokens', 'n/a')}")

    return {
        "text": content,
        "usage": usage,
    }


def perform_ocr_on_frame(frame_path: Path, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Run OpenAI OCR on a single frame.
    """
    target_model = model or DEFAULT_OCR_MODEL
    try:
        result = _call_openai_vision(frame_path, target_model)
        text = result.get("text", "").strip()
        return {
            "text": text,
            "markdown": "",  # No structured markdown returned; can be added later if needed
            "latex": "",     # Keep placeholder for compatibility
            "has_math": False,
            "has_tables": False,
            "has_diagrams": False,
            "confidence": 0.90 if text else 0.0,
            "method": f"openai_{target_model}",
        }
    except Exception as e:
        logger.error(f"OpenAI OCR failed for {frame_path}: {e}")
        return {
            "text": "",
            "markdown": "",
            "latex": "",
            "has_math": False,
            "has_tables": False,
            "has_diagrams": False,
            "confidence": 0.0,
            "method": f"openai_{target_model}",
            "error": str(e),
        }


def perform_ocr_on_frames(frames_metadata: List[Dict[str, Any]], model: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run OpenAI OCR on all extracted frames.
    Returns a list of OCR results aligned with frame metadata.
    """
    logger.info(f"Performing OpenAI OCR on {len(frames_metadata)} frames (model={model or DEFAULT_OCR_MODEL})")
    ocr_results: List[Dict[str, Any]] = []

    for idx, frame_meta in enumerate(frames_metadata):
        frame_id = frame_meta["frame_id"]
        timestamp = frame_meta["timestamp"]
        path = Path(frame_meta["path"])

        ocr_data = perform_ocr_on_frame(path, model=model)

        result = {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "path": str(path),
            **ocr_data,
        }
        ocr_results.append(result)

        if (idx + 1) % 5 == 0:
            logger.info(f"OCR progress: {idx + 1}/{len(frames_metadata)} frames processed")

    logger.info(f"OCR complete. Processed {len(ocr_results)} frames")
    non_empty = sum(1 for r in ocr_results if r.get("text"))
    logger.info(f"Frames with detected text: {non_empty}/{len(ocr_results)}")

    return ocr_results
