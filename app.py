"""
FastAPI server for the ClassCast pipeline + new AI features.

Features:
- Run full pipeline on uploaded video or YouTube URL.
- Semantic search (with embeddings) over fused transcript + OCR.
- Timeline-aware Q&A chatbot.
- Multi-language podcast synthesis with OpenAI TTS.
"""
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional
import sys
import textwrap

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from numpy.linalg import norm
import numpy as np
from openai import OpenAI
from starlette.requests import Request

from run_complete_pipeline import run_pipeline

# Ensure stdio streams are open (some environments close them, breaking logging/uvicorn)
if getattr(sys.stdout, "closed", False):
    sys.stdout = sys.__stdout__
if getattr(sys.stderr, "closed", False):
    sys.stderr = sys.__stderr__

load_dotenv()

BASE_DIR = Path(__file__).parent
RUN_DIR = BASE_DIR / "test_output" / "runs"
RUN_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI()
app = FastAPI(title="ClassCast")

# Serve static assets
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# --- In-memory run store (simple for demo; swap to DB/Redis if needed) ---
class RunState:
    def __init__(self):
        self.status: str = "queued"
        self.error: Optional[str] = None
        self.results: Optional[Dict] = None
        self.embeddings: Optional[np.ndarray] = None
        self.embedding_meta: List[Dict] = []
        self.audio_exports: Dict[str, str] = {}
        self.selected_languages: List[str] = []


runs: Dict[str, RunState] = {}


def _build_embeddings(run_state: RunState):
    """Embed fused text + board text for semantic search."""
    results = run_state.results or {}
    segments = results.get("segments", [])
    if not segments:
        return

    texts = []
    meta = []
    for seg in segments:
        fused = seg.get("fused_text") or ""
        board = seg.get("board_text") or ""
        combined = fused
        if board:
            combined += f" | board: {board}"
        texts.append(combined)
        meta.append(
            {
                "id": seg.get("id"),
                "start": seg.get("start"),
                "end": seg.get("end"),
                "frame_path": seg.get("frame_path"),
                "text": fused,
                "board": board,
            }
        )

    try:
        resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    except Exception as exc:
        run_state.error = f"Embedding failed: {exc}"
        return

    embeddings = np.array([np.array(item.embedding) for item in resp.data])
    run_state.embeddings = embeddings
    run_state.embedding_meta = meta


def _run_full_pipeline(run_id: str, *, youtube_url: str = "", video_path: Optional[Path] = None, duration: int = 20):
    run_state = runs[run_id]
    run_state.status = "running"
    run_output_dir = RUN_DIR / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)
    try:
        results = run_pipeline(
            youtube_url,
            duration,
            local_video_path=video_path,
            output_dir=run_output_dir,
        )
        run_state.results = results
        _build_embeddings(run_state)
        if run_state.selected_languages:
            _synthesize_podcast(run_state, run_state.selected_languages, run_id)
        run_state.status = "completed"
    except Exception as exc:  # noqa: BLE001
        run_state.status = "failed"
        run_state.error = str(exc)


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (norm(a) * norm(b) + 1e-10))


def _semantic_search(run_state: RunState, query: str, k: int = 5):
    if run_state.embeddings is None:
        raise HTTPException(status_code=400, detail="No embeddings available for this run.")

    resp = client.embeddings.create(model="text-embedding-3-small", input=[query])
    q_emb = np.array(resp.data[0].embedding)
    sims = [_cosine_sim(q_emb, emb) for emb in run_state.embeddings]
    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)

    # Filter out low-similarity hits to avoid irrelevant matches
    threshold = 0.30
    ranked = [(idx, score) for idx, score in ranked if score >= threshold][:k]

    results = []
    for idx, score in ranked:
        meta = run_state.embedding_meta[idx]
        results.append(
            {
                "score": score,
                **meta,
            }
        )
    return results


def _answer_question(run_state: RunState, question: str) -> str:
    # General Q&A: only send the user's question (no transcript context).
    prompt = (
        "You are a concise tutor. Answer clearly and helpfully. "
        "If the question is ambiguous, provide the most common interpretation."
    )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]

    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.2)
    return resp.choices[0].message.content.strip()


def _synthesize_podcast(run_state: RunState, languages: List[str], run_id: str):
    segments = run_state.results.get("segments", []) if run_state.results else []
    if not segments:
        raise HTTPException(status_code=400, detail="No transcript available.")

    base_out = RUN_DIR / run_id / "podcasts"
    base_out.mkdir(parents=True, exist_ok=True)

    # Guard against None values from upstream fusion
    sentences = [(seg.get("fused_text") or "") for seg in segments]
    # Keep line-per-segment to preserve order and avoid summarization
    joined = "\n".join(sentences)

    outputs: Dict[str, str] = {}

    for lang in languages:
        lang_dir = base_out / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        out_path = lang_dir / f"podcast_{lang}.mp3"

        # Translate once and synthesize one unified audio
        trans_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Translate the following lecture lines into {lang}. "
                        "Preserve ALL content and ordering. "
                        "Do NOT summarize or shorten. "
                        "Return the translated lines separated by newlines."
                    ),
                },
                {"role": "user", "content": joined},
            ],
            temperature=0.1,
        )
        translated = trans_resp.choices[0].message.content.strip()
        # Chunk very long text to avoid TTS limits while keeping sequence
        chunks = textwrap.wrap(translated, width=3200, replace_whitespace=False)

        with open(out_path, "wb") as f:
            for chunk in chunks:
                speech = client.audio.speech.create(model="tts-1", voice="alloy", input=chunk)
                for piece in speech.iter_bytes():
                    f.write(piece)

        outputs[lang] = str(out_path.relative_to(BASE_DIR))

    run_state.audio_exports = outputs
    return outputs


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/runs")
async def create_run(
    background_tasks: BackgroundTasks,
    youtube_url: str = Form(""),
    duration: int = Form(20),
    languages: str = Form(""),
    file: UploadFile = File(None),
):
    run_id = str(uuid.uuid4())
    runs[run_id] = RunState()
    video_path = None
    langs = [l.strip() for l in languages.split(",") if l.strip()]
    if not langs:
        langs = ["English"]
    runs[run_id].selected_languages = langs

    run_output_dir = RUN_DIR / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    duration_to_use: Optional[int] = duration

    if file and file.filename:
        target_dir = run_output_dir
        video_path = target_dir / file.filename
        content = await file.read()
        video_path.write_bytes(content)
        # For uploaded files, ignore the duration field and process full video
        duration_to_use = None

    background_tasks.add_task(
        _run_full_pipeline,
        run_id,
        youtube_url=youtube_url,
        video_path=video_path,
        duration=duration_to_use,
    )
    return {"run_id": run_id, "status": "queued"}


@app.get("/api/runs/{run_id}")
async def run_status(run_id: str):
    run_state = runs.get(run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")

    # Produce a safe, relative-friendly view of results for the UI
    results = run_state.results
    if results and results.get("segments"):
        safe_segments = []
        for seg in results["segments"]:
            safe_seg = dict(seg)
            frame_path = seg.get("frame_path")
            if frame_path:
                p = Path(frame_path)
                try:
                    rel = p.relative_to(BASE_DIR)
                    safe_seg["frame_url"] = f"/files/{rel.as_posix()}"
                except ValueError:
                    safe_seg["frame_url"] = ""
            safe_segments.append(safe_seg)
        results = dict(results)
        results["segments"] = safe_segments

    return {
        "status": run_state.status,
        "error": run_state.error,
        "results": results,
        "audio": run_state.audio_exports,
    }


@app.get("/api/search")
async def semantic_search(run_id: str, q: str, k: int = 5):
    run_state = runs.get(run_id)
    if not run_state or run_state.status != "completed":
        raise HTTPException(status_code=400, detail="Run not ready")
    results = _semantic_search(run_state, q, k)
    return {"results": results}


@app.post("/api/chat")
async def chat(run_id: str = Form(...), question: str = Form(...)):
    run_state = runs.get(run_id)
    if not run_state or run_state.status != "completed":
        raise HTTPException(status_code=400, detail="Run not ready")
    answer = _answer_question(run_state, question)
    return {"answer": answer}


@app.post("/api/podcast")
async def podcast(run_id: str = Form(...), languages: str = Form(...)):
    run_state = runs.get(run_id)
    if not run_state or run_state.status != "completed":
        raise HTTPException(status_code=400, detail="Run not ready")

    langs = [l.strip() for l in languages.split(",") if l.strip()]
    if not langs:
        raise HTTPException(status_code=400, detail="No languages provided")

    outputs = _synthesize_podcast(run_state, langs, run_id)
    return {"audio": outputs}


@app.get("/files/{path:path}")
async def serve_file(path: str):
    target = (BASE_DIR / path).resolve()
    if BASE_DIR not in target.parents and target != BASE_DIR:
        raise HTTPException(status_code=404, detail="File not found")
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target)


def start():
    """Convenience entrypoint for `python app.py`."""
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    start()
