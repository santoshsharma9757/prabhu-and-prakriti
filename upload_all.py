from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import DATA_DIR, OUTPUT_VIDEO_DIR, load_settings, setup_logging
from uploader import YouTubeUploader


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload all pending devotional Shorts metadata files.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings.log_level)
    uploader = YouTubeUploader(settings)
    
    meta_dir = DATA_DIR / "metadata"
    meta_files = sorted(meta_dir.glob("*_metadata.json"))[: args.limit]
    for meta_file in meta_files:
        try:
            payload = json.loads(meta_file.read_text(encoding="utf-8"))
            video_path = Path(payload["video_path"])
            
            if not video_path.exists():
                print(f"Skipping orphan metadata (video missing): {meta_file.name}")
                meta_file.unlink()
                continue

            publish_at = payload.get("publish_at")
            result = uploader.upload(video_path=video_path, seo=payload["seo"], publish_at=publish_at)
            
            print(json.dumps({"file": meta_file.name, "result": result}, ensure_ascii=False))

            if result.get("status") == "uploaded":
                # Success! Delete local files to save space
                try:
                    # Delete video
                    if video_path.exists(): video_path.unlink()
                    # Delete metadata
                    if meta_file.exists(): meta_file.unlink()
                    # Delete temporary audio/subtitle files if they exist
                    audio_p = Path(payload.get("audio_path", ""))
                    sub_p = Path(payload.get("subtitle_path", ""))
                    if audio_p.exists(): audio_p.unlink()
                    if sub_p.exists(): sub_p.unlink()
                    print(f"Cleaned up local files for: {video_path.name}")
                except Exception as e:
                    print(f"Warning: Failed to delete some local files: {e}")
        except Exception as e:
            print(f"Error processing {meta_file.name}: {e}")


if __name__ == "__main__":
    main()
