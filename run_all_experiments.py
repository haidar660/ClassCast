"""
Run the ClassCast pipeline over every test video in data/test_videos.

Usage:
    python scripts/run_all_experiments.py
"""
from pathlib import Path
from typing import List, Dict

from run_complete_pipeline import run_pipeline


VIDEO_DIR = Path("data/test_videos")
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def find_videos() -> List[Path]:
    """Return all video files under VIDEO_DIR matching the allowed extensions."""
    if not VIDEO_DIR.exists():
        return []
    return sorted(
        p for p in VIDEO_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )


def main() -> None:
    videos = find_videos()
    if not videos:
        print(f"No videos found in {VIDEO_DIR.resolve()}")
        return

    experiment_log: List[Dict[str, str]] = []

    for video_path in videos:
        print("\n" + "=" * 80)
        print(f"Running experiment for: {video_path.name}")
        print(f"Selected file: {video_path.resolve()}")

        try:
            result = run_pipeline(
                youtube_url="",
                duration=None,
                local_video_path=video_path,
            )

            run_id = result.get("run_id", "")
            output_dir = result.get("output_dir", "")

            print(f"Run ID: {run_id}")
            print(f"Output directory: {output_dir}")

            experiment_log.append(
                {
                    "video": video_path.name,
                    "status": "success",
                    "run_id": run_id,
                    "output_dir": output_dir,
                }
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] Experiment failed for {video_path.name}: {exc}")
            experiment_log.append(
                {
                    "video": video_path.name,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue

    print("\n" + "=" * 80)
    print("EXPERIMENT SUMMARY")
    print("=" * 80)
    for entry in experiment_log:
        if entry["status"] == "success":
            print(
                f"{entry['video']}: SUCCESS | run_id={entry['run_id']} | dir={entry['output_dir']}"
            )
        else:
            print(f"{entry['video']}: FAILED | error={entry.get('error', '')}")


if __name__ == "__main__":
    main()
