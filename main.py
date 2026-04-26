from __future__ import annotations

import argparse
import json
import logging
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import (
    DATA_DIR,
    OUTPUT_AUDIO_DIR,
    OUTPUT_SUBTITLES_DIR,
    OUTPUT_VIDEO_DIR,
    load_settings,
    setup_logging,
    write_json,
)
from idea_generator import IdeaGenerator
from scheduler import plan_schedule, save_schedule
from script_generator import ScriptGenerator
from seo_generator import SEOGenerator
from subtitle_generator import generate_srt
from tts import TTSProvider
from uploader import YouTubeUploader
from video_generator import VideoGenerator


LOGGER = logging.getLogger(__name__)


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    return cleaned[:80] or datetime.now().strftime("%Y%m%d_%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hindi devotional YouTube Shorts automation")
    parser.add_argument("--count", type=int, default=1, help="How many Shorts to generate")
    parser.add_argument("--topic", type=str, default=None, help="Explicit Hindi topic hint")
    parser.add_argument("--no-upload", action="store_false", dest="upload", help="Disable automatic upload if configured")
    parser.add_argument("--no-schedule", action="store_false", dest="schedule", help="Disable scheduling for generated topics")
    parser.add_argument("--no-pexels", action="store_false", dest="use_pexels", help="Disable Pexels visuals")
    parser.add_argument("--local", action="store_true", help="Use local videos from assets/localvideos")
    parser.add_argument("--pexel-music", action="store_true", help="Use Pexels visuals with trending music (no storytelling)")
    parser.add_argument("--mix", action="store_true", help="Balanced mix: 50%% local, 50%% pexel-music")
    parser.set_defaults(upload=False, schedule=True, use_pexels=True, local=False, pexel_music=False, mix=False)
    return parser


def save_run_manifest(payload: dict[str, Any]) -> None:
    path = DATA_DIR / "last_run.json"
    write_json(path, payload)


def generate_short(
    idea_generator: IdeaGenerator,
    script_generator: ScriptGenerator,
    seo_generator: SEOGenerator,
    tts_engine: HindiTTS,
    video_generator: VideoGenerator,
    uploader: YouTubeUploader,
    count: int,
    topic_hint: str | None,
    use_pexels: bool,
    upload: bool,
    local: bool = False,
    pexel_music: bool = False,
    mix: bool = False,
) -> list[dict[str, Any]]:
    ideas = idea_generator.generate(count=count, topic_hint=topic_hint)
    items: list[dict[str, Any]] = []

    for i, idea in enumerate(ideas):
        # Handle mixed assets if requested
        curr_local = local
        curr_pexel_music = pexel_music
        
        if mix:
            # 50/50 split: first half local, second half pexel_music
            if i < len(ideas) // 2:
                curr_local = True
                curr_pexel_music = False
            else:
                curr_local = False
                curr_pexel_music = True
        
        script = script_generator.generate(idea)
        seo = seo_generator.generate(idea, script)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{stamp}_{slugify(idea['topic'])}"
        audio_path = OUTPUT_AUDIO_DIR / f"{base_name}.mp3"
        subtitle_path = OUTPUT_SUBTITLES_DIR / f"{base_name}.srt"
        video_path = OUTPUT_VIDEO_DIR / f"{base_name}.mp4"
        meta_dir = DATA_DIR / "metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta_path = meta_dir / f"{base_name}_metadata.json"

        if curr_pexel_music:
            # Skip TTS and storytelling for pexel-music mode
            duration = random.randint(35, 50)
            audio_path = None # Will use trending music in video_generator
            subtitle_path = None
            LOGGER.info("Pexel-music mode: Skipping TTS and storytelling for topic: %s", idea["topic"])
        else:
            tts_engine.synthesize(script.get("tts_script") or script["full_script"], audio_path)
            from moviepy import AudioFileClip
            with AudioFileClip(str(audio_path)) as narration:
                duration = narration.duration
            generate_srt(script["full_script"], duration, subtitle_path)

        video_generator.create_short(
            idea=idea,
            script=script,
            seo=seo,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=video_path,
            use_pexels=use_pexels,
            local=curr_local,
            pexel_music=curr_pexel_music,
        )
        upload_result = (
            uploader.upload(video_path, seo)
            if upload and (uploader.is_configured() or uploader.settings.upload_enabled)
            else {"status": "skipped", "reason": "Upload not requested or not configured."}
        )

        payload = {
            "idea": idea,
            "script": script,
            "seo": seo,
            "audio_path": str(audio_path),
            "subtitle_path": str(subtitle_path),
            "video_path": str(video_path),
            "upload_result": upload_result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        items.append(payload)
        LOGGER.info("Finished short for topic: %s", idea["topic"])
    return items


def check_assets() -> None:
    from config import TRENDING_MUSIC_DIR, LOCAL_VIDEOS_DIR
    print("\n--- Asset Management Summary ---")
    
    for category in ["god", "nature"]:
        music_folder = TRENDING_MUSIC_DIR / category
        music_count = len(list(music_folder.glob("*.mp3"))) + len(list(music_folder.glob("*.wav")))
        video_folder = LOCAL_VIDEOS_DIR / category
        video_count = len(list(video_folder.glob("*.mp4"))) + len(list(video_folder.glob("*.mov")))
        
        print(f"[{category.upper()}] Music: {music_count} files | Local Videos: {video_count} files")
        
        if music_count == 0:
            LOGGER.warning(f"No music found in '{music_folder}'. Please add 'No Copyright' songs here!")
        if video_count == 0:
            LOGGER.info(f"No local videos in '{video_folder}'. Will use Pexels/Gradients as fallback.")
            
    print("--------------------------------\n")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings.log_level)

    idea_generator = IdeaGenerator(settings)
    script_generator = ScriptGenerator(settings)
    seo_generator = SEOGenerator(settings)
    tts_engine = TTSProvider(settings)
    video_generator = VideoGenerator(settings)
    uploader = YouTubeUploader(settings)

    # Asset safety check
    check_assets()

    items = generate_short(
        idea_generator=idea_generator,
        script_generator=script_generator,
        seo_generator=seo_generator,
        tts_engine=tts_engine,
        video_generator=video_generator,
        uploader=uploader,
        count=max(args.count, 1),
        topic_hint=args.topic,
        use_pexels=args.use_pexels,
        upload=args.upload,
        local=args.local,
        pexel_music=args.pexel_music,
        mix=args.mix,
    )

    if args.schedule:
        schedule_items = plan_schedule([item["idea"]["topic"] for item in items], settings=settings)
        for i, item in enumerate(items):
            if i < len(schedule_items):
                item["publish_at"] = schedule_items[i].publish_at
                # Re-write metadata with the time included
                meta_dir = DATA_DIR / "metadata"
                base_name = Path(item["video_path"]).stem
                meta_path = meta_dir / f"{base_name}_metadata.json"
                meta_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        
        save_schedule(schedule_items)
        LOGGER.info("Saved schedule to %s", DATA_DIR / "schedule_queue.json")

    save_run_manifest(
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "topic_hint": args.topic,
            "use_pexels": args.use_pexels,
            "upload": args.upload,
        }
    )

    print(json.dumps({"generated": len(items), "videos": [item["video_path"] for item in items]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
