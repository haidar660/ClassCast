"""
Lightweight OCR pipeline using OpenAI vision.

Goals:
- Avoid hammering the API on near-identical frames.
- Emit only *new* board lines once, suppressing repeats.
- Keep the interface used by run_complete_pipeline: ``perform_ocr_on_frames``.

We keep helpers in ``ocr/vision`` (e.g., preprocessing, LaTeX cleaning) intact.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import List, Dict, Any, Tuple

import cv2
import numpy as np
from openai import OpenAI

from ocr.vision.latex_converter import latex_to_text

client = OpenAI()


def _encode_image(image_path: Path) -> str:
    data = Path(image_path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def _image_similarity(img_a: np.ndarray, img_b: np.ndarray) -> float:
    """
    Simple structural similarity proxy (no skimage dependency):
    resize to 64x64, compute histogram correlation across channels.
    Returns 0..1 (1 = identical).
    """
    if img_a is None or img_b is None:
        return 0.0
    img_a_small = cv2.resize(img_a, (64, 64), interpolation=cv2.INTER_AREA)
    img_b_small = cv2.resize(img_b, (64, 64), interpolation=cv2.INTER_AREA)
    img_a_small = cv2.cvtColor(img_a_small, cv2.COLOR_BGR2RGB)
    img_b_small = cv2.cvtColor(img_b_small, cv2.COLOR_BGR2RGB)

    sim = 0.0
    for ch in range(3):
        hist_a = cv2.calcHist([img_a_small], [ch], None, [32], [0, 256])
        hist_b = cv2.calcHist([img_b_small], [ch], None, [32], [0, 256])
        cv2.normalize(hist_a, hist_a)
        cv2.normalize(hist_b, hist_b)
        sim += cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)
    sim /= 3.0
    # Clamp correlation [-1,1] to [0,1]
    return max(0.0, min(1.0, (sim + 1) / 2))


def _pixel_change_ratio(img_a: np.ndarray, img_b: np.ndarray, threshold: int = 15) -> float:
    """
    Fraction of pixels whose absolute difference exceeds `threshold`.
    Useful to detect small board updates that histogram similarity might miss.
    """
    if img_a is None or img_b is None:
        return 1.0
    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
    if gray_a.shape != gray_b.shape:
        gray_b = cv2.resize(gray_b, (gray_a.shape[1], gray_a.shape[0]), interpolation=cv2.INTER_AREA)
    diff = cv2.absdiff(gray_a, gray_b)
    changed = np.count_nonzero(diff > threshold)
    total = diff.size
    return changed / float(total) if total else 1.0


def _normalize_line(line: str) -> str:
    return " ".join((line or "").replace("```", "").replace("`", "").split()).lower()


def _dedupe_lines(text: str, seen: set[str]) -> Tuple[str, set[str]]:
    """Return only lines not seen before; update seen set."""
    if not text:
        return "", seen
    new_lines = []
    for ln in [ln.strip() for ln in text.splitlines() if ln.strip()]:
        norm = _normalize_line(ln)
        if norm and norm not in seen:
            new_lines.append(ln)
            seen.add(norm)
    return "\n".join(new_lines), seen


def _call_openai_vision(image_path: Path, model: str) -> str:
    b64 = _encode_image(image_path)
    prompt = (
        "Extract all readable board/slide text. "
        "Return plain text only, preserve math layout with simple newlines. "
        "Do NOT add explanations or paraphrase."
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def perform_ocr_on_frames(
    frames_metadata: List[Dict[str, Any]],
    *,
    model: str = "gpt-4o-mini",
    similarity_threshold: float = 0.88,
    min_change_ratio: float = 0.003,
) -> List[Dict[str, Any]]:
    """
    Run OCR on a list of frames, skipping near-duplicates and suppressing
    repeated lines across frames.
    """
    results: List[Dict[str, Any]] = []
    last_image: np.ndarray | None = None
    seen_lines: set[str] = set()

    for frame in sorted(frames_metadata, key=lambda x: x.get("timestamp", 0.0)):
        frame_path = Path(frame["path"])
        frame_id = frame.get("frame_id") or frame_path.stem
        ts = frame.get("timestamp", 0.0)

        img = cv2.imread(str(frame_path))
        sim = _image_similarity(last_image, img) if last_image is not None else 0.0
        change_ratio = _pixel_change_ratio(last_image, img) if last_image is not None else 1.0

        if last_image is not None and sim >= similarity_threshold and change_ratio < min_change_ratio:
            results.append(
                {
                    "frame_id": frame_id,
                    "timestamp": ts,
                    "path": str(frame_path),
                    "text": "",
                    "markdown": "",
                    "latex": "",
                    "has_math": False,
                    "has_tables": False,
                    "has_diagrams": False,
                    "confidence": 0.0,
                    "method": f"skipped_similar_frame (sim={sim:.3f}, change={change_ratio:.4f})",
                }
            )
            continue

        raw_text = _call_openai_vision(frame_path, model=model)
        raw_text = raw_text.replace("\u200b", " ").strip()
        # Remove fenced code markers often returned by models
        raw_text = raw_text.replace("```", "").strip()

        deduped, seen_lines = _dedupe_lines(raw_text, seen_lines)
        cleaned_text = latex_to_text(deduped) if deduped else ""

        results.append(
            {
                "frame_id": frame_id,
                "timestamp": ts,
                "path": str(frame_path),
                "text": cleaned_text,
                "markdown": "",
                "latex": "",
                "has_math": False,
                "has_tables": False,
                "has_diagrams": False,
                "confidence": 0.9 if cleaned_text else 0.0,
                "method": f"openai_{model}",
            }
        )

        last_image = img

    return results


__all__ = ["perform_ocr_on_frames"]
