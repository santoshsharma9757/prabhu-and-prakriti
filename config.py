from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_AUDIO_DIR = OUTPUT_DIR / "audio"
OUTPUT_IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
OUTPUT_VIDEO_DIR = OUTPUT_DIR / "video"
MUSIC_DIR = ASSETS_DIR / "music"
TRENDING_MUSIC_DIR = ASSETS_DIR / "trending_music"
FONTS_DIR = ASSETS_DIR / "fonts"
LOCAL_VIDEOS_DIR = ASSETS_DIR / "localvideos"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _find_font() -> str | None:
    candidate_paths = [
        FONTS_DIR / "NotoSansDevanagari-Regular.ttf",
        FONTS_DIR / "NotoSerifDevanagari-Regular.ttf",
        Path("C:/Windows/Fonts/Nirmala.ttf"),
        Path("C:/Windows/Fonts/Mangal.ttf"),
        Path("C:/Windows/Fonts/Kokila.ttf"),
        Path("C:/Windows/Fonts/aparaj.ttf"),
    ]
    for path in candidate_paths:
        if path.exists():
            return str(path)
    return None


@dataclass(slots=True)
class Settings:
    daily_video_count: int = 2
    scheduler_timezone: str = "Asia/Kolkata"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    gemini_api_key: str = ""
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    bhakti_youtube_api_key: str = ""
    bhakti_youtube_client_secret_file: str = ""
    bhakti_youtube_token_file: str = ""
    upload_enabled: bool = False
    youtube_category_id: str = "27"
    log_level: str = "INFO"
    default_language: str = "hi"
    channel_name: str = "Prabhu & Prakriti"
    channel_handle_hint: str = "@prabhuandprakriti"
    country_code: str = "IN"
    shorts_duration_min: int = 30
    shorts_duration_max: int = 45
    frame_width: int = 1080
    frame_height: int = 1920
    fps: int = 24
    title_max_length: int = 65
    font_path: str | None = None
    top_text_font_size: int = 60
    subtitle_font_size: int = 76
    body_text_margin: int = 70
    safe_topic_mode: bool = True
    brand_keywords: list[str] = field(
        default_factory=lambda: [
            "भक्ति",
            "सनातन",
            "आस्था",
            "प्रेरणा",
            "शक्ति",
            "संकल्प",
        ]
    )

    def to_json(self) -> dict[str, Any]:
        return {
            "channel_name": self.channel_name,
            "country_code": self.country_code,
            "default_language": self.default_language,
            "shorts_duration_range": [
                self.shorts_duration_min,
                self.shorts_duration_max,
            ],
        }


def load_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")
    
    # Handle both project-specific and generic names for YouTube
    yt_api_key = os.getenv("BHAKTI_YOUTUBE_API_KEY") or os.getenv("YOUTUBE_API_KEY", "")
    yt_client_secret = os.getenv("BHAKTI_YOUTUBE_CLIENT_SECRET_FILE") or \
                       os.getenv("YOUTUBE_CLIENT_SECRET_FILE") or \
                       os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "")
    yt_token = os.getenv("BHAKTI_YOUTUBE_TOKEN_FILE") or os.getenv("YOUTUBE_TOKEN_FILE", "")

    settings = Settings(
        daily_video_count=int(os.getenv("DAILY_VIDEO_COUNT", "2")),
        scheduler_timezone=os.getenv("SCHEDULER_TIMEZONE", "Asia/Kolkata").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        pexels_api_key=os.getenv("PEXELS_API_KEY", "").strip(),
        pixabay_api_key=os.getenv("PIXABAY_API_KEY", "").strip(),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", "").strip(),
        elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "").strip(),
        bhakti_youtube_api_key=yt_api_key.strip(),
        bhakti_youtube_client_secret_file=yt_client_secret.strip(),
        bhakti_youtube_token_file=yt_token.strip(),
        upload_enabled=_env_bool("UPLOAD_ENABLED", False),
        youtube_category_id=os.getenv("YOUTUBE_CATEGORY_ID", "27").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        font_path=_find_font(),
    )
    ensure_directories()
    return settings


def ensure_directories() -> None:
    for path in [
        ASSETS_DIR,
        DATA_DIR,
        LOGS_DIR,
        OUTPUT_DIR,
        OUTPUT_AUDIO_DIR,
        OUTPUT_IMAGES_DIR,
        OUTPUT_SUBTITLES_DIR,
        OUTPUT_VIDEO_DIR,
        MUSIC_DIR,
        TRENDING_MUSIC_DIR,
        TRENDING_MUSIC_DIR / "god",
        TRENDING_MUSIC_DIR / "nature",
        FONTS_DIR,
        LOCAL_VIDEOS_DIR,
        LOCAL_VIDEOS_DIR / "nature",
        LOCAL_VIDEOS_DIR / "god",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def setup_logging(level: str) -> None:
    ensure_directories()
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "automation.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
