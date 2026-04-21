from __future__ import annotations

import math
import re
from pathlib import Path


def _split_script(script_text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[।!?.,\n]", script_text) if p.strip()]
    return parts or [script_text.strip()]


def _fmt(seconds: float) -> str:
    millis = int((seconds % 1) * 1000)
    whole = int(seconds)
    s = whole % 60
    m = (whole // 60) % 60
    h = whole // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"


def generate_srt(script_text: str, duration: float, output_path: Path) -> Path:
    chunks = _split_script(script_text)
    total_chars = sum(max(len(chunk), 1) for chunk in chunks)
    cursor = 0.0
    lines: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        ratio = max(len(chunk), 1) / total_chars
        chunk_duration = max(1.8, duration * ratio)
        start = cursor
        end = min(duration, cursor + chunk_duration)
        cursor = end
        lines.append(str(idx))
        lines.append(f"{_fmt(start)} --> {_fmt(end)}")
        lines.append(chunk)
        lines.append("")
    if cursor < duration and lines:
        last_end = _fmt(duration)
        lines[-3] = f"{lines[-3].split(' --> ')[0]} --> {last_end}"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def build_subtitle_segments(script_text: str, duration: float) -> list[dict[str, float | str]]:
    chunks = _split_script(script_text)
    total_chars = sum(max(len(chunk), 1) for chunk in chunks)
    segments = []
    cursor = 0.0
    for chunk in chunks:
        ratio = max(len(chunk), 1) / total_chars
        chunk_duration = max(1.8, duration * ratio)
        start = cursor
        end = min(duration, cursor + chunk_duration)
        cursor = end
        segments.append({"start": start, "end": end, "text": chunk})
    if segments:
        segments[-1]["end"] = math.ceil(duration * 1000) / 1000
    return segments
