from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import edge_tts
from gtts import gTTS

from config import Settings


LOGGER = logging.getLogger(__name__)


class TTSProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Use English voice by default
        self.edge_voice = "en-US-GuyNeural" if settings.default_language == "en" else "hi-IN-SwaraNeural"

    async def _edge_save(self, text: str, path: Path) -> None:
        communicate = edge_tts.Communicate(text, self.edge_voice, rate="-4%")
        await communicate.save(str(path))

    def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            asyncio.run(self._edge_save(text, output_path))
            LOGGER.info(f"Generated {self.settings.default_language} narration with Edge TTS")
            return output_path
        except Exception as exc:
            LOGGER.warning("Edge TTS failed, falling back to gTTS: %s", exc)
            lang = self.settings.default_language
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(str(output_path))
            return output_path
