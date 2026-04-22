from __future__ import annotations

import logging
import random
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
import requests
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import MUSIC_DIR, OUTPUT_IMAGES_DIR, Settings
from subtitle_generator import build_subtitle_segments


LOGGER = logging.getLogger(__name__)


class VideoGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_short(
        self,
        idea: dict[str, Any],
        script: dict[str, Any],
        seo: dict[str, Any],
        audio_path: Path,
        subtitle_path: Path,
        output_path: Path,
        use_pexels: bool = False,
    ) -> Path:
        with AudioFileClip(str(audio_path)) as narration:
            duration = narration.duration
            visual_clip = self._build_background_clip(
                idea=idea,
                duration=duration,
                use_pexels=use_pexels,
            )
            overlays = [
                self._create_top_text_clip(script["short_on_screen_text"], duration=duration),
            ]
            for seg in build_subtitle_segments(script["full_script"], duration):
                overlays.append(
                    self._create_subtitle_clip(
                        seg["text"],
                        start=float(seg["start"]),
                        end=float(seg["end"]),
                    )
                )

            video = CompositeVideoClip(
                [visual_clip] + overlays,
                size=(self.settings.frame_width, self.settings.frame_height),
            )
            audio_mix = self._build_audio_mix(narration)
            final = video.with_audio(audio_mix)
            final.write_videofile(
                str(output_path),
                fps=self.settings.fps,
                codec="libx264",
                audio_codec="aac",
                threads=2,
                preset="medium",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                logger=None,
            )
            final.close()
            video.close()
            visual_clip.close()
            audio_mix.close()
        LOGGER.info("Created video at %s with subtitles %s", output_path, subtitle_path)
        return output_path

    def _build_audio_mix(self, narration: AudioFileClip) -> CompositeAudioClip:
        clips = [narration]
        music_files = sorted(MUSIC_DIR.glob("*"))
        if music_files:
            music = AudioFileClip(str(random.choice(music_files)))
            if music.duration > narration.duration:
                music = music.subclipped(0, narration.duration)
            music = music.with_duration(narration.duration).with_volume_scaled(0.50)
            clips.append(music)
        return CompositeAudioClip(clips)

    def _build_background_clip(
        self,
        idea: dict[str, Any],
        duration: float,
        use_pexels: bool,
    ) -> Any:
        clips = []
        if use_pexels and self.settings.pexels_api_key:
            media_paths = self._download_pexels_media(idea, count=5)
            if media_paths:
                segment_duration = duration / len(media_paths)
                for path in media_paths:
                    try:
                        if path.suffix.lower() in {".mp4", ".mov", ".avi"}:
                            clip = VideoFileClip(str(path)).resized(height=self.settings.frame_height)
                            # Center crop to 9:16
                            w, h = clip.size
                            target_w = int(h * 9 / 16)
                            clip = clip.cropped(x_center=w/2, width=target_w).resized(new_size=(self.settings.frame_width, self.settings.frame_height))
                            
                            if clip.duration > segment_duration:
                                clip = clip.subclipped(0, segment_duration)
                            else:
                                clip = clip.with_duration(segment_duration)
                            clips.append(clip.without_audio())
                        else:
                            clips.append(
                                ImageClip(str(path)).with_duration(segment_duration).resized(
                                    new_size=(self.settings.frame_width, self.settings.frame_height)
                                )
                            )
                    except Exception as e:
                        LOGGER.warning(f"Failed to process clip {path}: {e}")

        if not clips:
            gradient = self._create_gradient_background(idea["theme"])
            return ImageClip(np.array(gradient)).with_duration(duration)
        
        return concatenate_videoclips(clips, method="compose").with_duration(duration)

    def _download_pexels_media(self, idea: dict[str, Any], count: int = 3) -> list[Path]:
        # Mapping for better Pexels search results for Indian deities
        deity_mapping = {
            "mahakal": ["lord shiva statue", "mahadav", "shiva temple", "mountains sunrise"],
            "hanuman ji": ["hanuman statue", "lord hanuman", "indian temple bells", "prayer hands"],
            "maa durga": ["goddess durga", "hindu temple", "indian festival aarti", "diya light"],
            "vishnu ji": ["lord vishnu", "spiritual india", "river aarti", "lotus flower"],
            "krishna bhakti": ["lord krishna statue", "vrindavan temple", "flute peacock", "indian village"],
            "ram bhakti": ["lord ram", "ayodhya temple", "ancient india", "sunrise spiritual"],
        }
        
        theme = idea.get("theme", "").lower()
        topic = idea.get("topic", "").lower()
        
        base_queries = idea.get("visual_queries") or [
            "spiritual india",
            "temple bells",
            "indian monk",
            "himalayas",
        ]
        
        # Inject deity-specific queries at the front
        queries = []
        for key, vals in deity_mapping.items():
            if key in theme or key in topic:
                queries.extend(vals)
        queries.extend(base_queries)
        # Remove duplicates while preserving order
        queries = list(dict.fromkeys(queries))

        headers = {"Authorization": self.settings.pexels_api_key}
        downloaded = []
        
        # Try videos first for better engagement
        for query in queries:
            if len(downloaded) >= count: break
            try:
                # Search for videos
                response = requests.get(
                    "https://api.pexels.com/videos/search",
                    headers=headers,
                    params={"query": query, "orientation": "portrait", "per_page": 2},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                for video_data in data.get("videos", []):
                    if len(downloaded) >= count: break
                    video_files = video_data.get("video_files", [])
                    # Pick a good quality HD file (720p or better)
                    best_file = next((f for f in video_files if f.get("width") and 720 <= f.get("width") <= 1440), None)
                    if not best_file:
                        best_file = video_files[0]
                    
                    media_url = best_file.get("link")
                    if media_url:
                        clean_url = media_url.split("?")[0].split("&")[0]
                        ext = Path(clean_url).suffix or ".mp4"
                        target = OUTPUT_IMAGES_DIR / f"pexels_vid_{abs(hash(query))}_{abs(hash(media_url))}{ext}"
                        if not target.exists():
                            media = requests.get(media_url, timeout=60)
                            media.raise_for_status()
                            target.write_bytes(media.content)
                        downloaded.append(target)
            except Exception as exc:
                LOGGER.warning("Pexels video query failed for '%s': %s", query, exc)

        # Fallback to images if videos are sparse
        if len(downloaded) < count:
            for query in queries:
                if len(downloaded) >= count: break
                try:
                    response = requests.get(
                        "https://api.pexels.com/v1/search",
                        headers=headers,
                        params={"query": query, "orientation": "portrait", "per_page": 2},
                        timeout=30,
                    )
                    response.raise_for_status()
                    data = response.json()
                    for photo in data.get("photos", []):
                        if len(downloaded) >= count: break
                        src = photo.get("src", {})
                        media_url = src.get("portrait") or src.get("large2x")
                        if media_url:
                            clean_url = media_url.split("?")[0]
                            ext = Path(clean_url).suffix or ".jpg"
                            target = OUTPUT_IMAGES_DIR / f"pexels_img_{abs(hash(query))}_{abs(hash(media_url))}{ext}"
                            if not target.exists():
                                media = requests.get(media_url, timeout=60)
                                media.raise_for_status()
                                target.write_bytes(media.content)
                            downloaded.append(target)
                except Exception as exc:
                    LOGGER.warning("Pexels image query failed for '%s': %s", query, exc)
                
        return downloaded

    def _create_gradient_background(self, theme: str) -> Image.Image:
        colors = {
            "mahakal": ((15, 18, 36), (255, 140, 0)),
            "hanuman ji": ((47, 16, 0), (255, 113, 24)),
            "maa durga": ((60, 0, 12), (255, 102, 71)),
            "vishnu ji": ((0, 45, 65), (54, 168, 255)),
            "narasimha": ((47, 16, 0), (255, 180, 0)),
        }
        start, end = colors.get(theme, ((18, 18, 30), (242, 136, 48)))
        img = Image.new("RGB", (self.settings.frame_width, self.settings.frame_height), start)
        draw = ImageDraw.Draw(img)
        for y in range(self.settings.frame_height):
            mix = y / max(self.settings.frame_height - 1, 1)
            color = tuple(int(start[i] * (1 - mix) + end[i] * mix) for i in range(3))
            draw.line((0, y, self.settings.frame_width, y), fill=color)
        vignette = Image.new("L", img.size, 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse(
            (-300, -100, self.settings.frame_width + 300, self.settings.frame_height + 600),
            fill=180,
        )
        vignette = vignette.filter(ImageFilter.GaussianBlur(140))
        glow = Image.new("RGBA", img.size, (255, 210, 150, 0))
        glow.putalpha(vignette)
        return Image.alpha_composite(img.convert("RGBA"), glow)

    def _render_text_card(
        self,
        text: str,
        font_size: int,
        box_width: int,
        fill: tuple[int, int, int, int],
        stroke_fill: tuple[int, int, int, int],
        bg_fill: tuple[int, int, int, int] | None = None,
        align: str = "center",
    ) -> Image.Image:
        try:
            font_file = self.settings.font_path if self.settings.font_path else "C:/Windows/Fonts/arialbd.ttf"
            font = ImageFont.truetype(font_file, font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(text, width=max(10, box_width // max(font_size // 2, 18))))
        canvas = Image.new("RGBA", (box_width, 1200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=12, align=align, stroke_width=2)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (box_width - text_w) // 2
        y = 30
        if bg_fill:
            pad_x = 24
            pad_y = 18
            draw.rounded_rectangle(
                (x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y),
                radius=30,
                fill=bg_fill,
            )
        draw.multiline_text(
            (x, y),
            wrapped,
            font=font,
            fill=fill,
            spacing=12,
            align=align,
            stroke_width=2,
            stroke_fill=stroke_fill,
        )
        return canvas.crop((0, 0, box_width, min(1200, y + text_h + 60)))

    def _create_top_text_clip(self, text: str, duration: float) -> ImageClip:
        img = self._render_text_card(
            text=text,
            font_size=self.settings.top_text_font_size,
            box_width=self.settings.frame_width - 120,
            fill=(255, 245, 225, 255),
            stroke_fill=(20, 10, 5, 255),
            bg_fill=(20, 10, 5, 135),
        )
        return ImageClip(np.array(img)).with_duration(duration).with_position(("center", 120))

    def _create_subtitle_clip(self, text: str, start: float, end: float) -> ImageClip:
        img = self._render_text_card(
            text=text,
            font_size=self.settings.subtitle_font_size,
            box_width=self.settings.frame_width - 100,
            fill=(255, 255, 255, 255),
            stroke_fill=(0, 0, 0, 255),
            bg_fill=(0, 0, 0, 130),
        )
        return (
            ImageClip(np.array(img))
            .with_start(start)
            .with_end(end)
            .with_position(("center", self.settings.frame_height - img.height - 180))
        )
