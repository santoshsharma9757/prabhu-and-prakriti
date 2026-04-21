from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from openai import OpenAI

from config import DATA_DIR, Settings, read_json, write_json
from llm_fallback import fallback_script, parse_json_response


LOGGER = logging.getLogger(__name__)
CONTENT_HISTORY_FILE = DATA_DIR / "content_history.json"


class ScriptGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = (
            OpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    def generate(self, idea: dict[str, Any]) -> dict[str, Any]:
        script = self._generate_with_llm(idea) if self.client else fallback_script(idea)
        self._save_content_record(idea, script)
        return script

    def _generate_with_llm(self, idea: dict[str, Any]) -> dict[str, Any]:
        prompt = {
            "task": "Write a storytelling devotional YouTube Shorts script. The audio will be in Hindi but on-screen text must be in Hinglish.",
            "rules": [
                "Target duration 30-45 seconds.",
                "Style: Master Storyteller about Sanatan Dharma (Hanuman Ji, Ram Ji, Shiva, etc).",
                "You must provide 'tts_script' in pure Devanagari Hindi. This will be used for the voiceover.",
                "You must provide 'full_script' in Hinglish (Hindi written in English alphabet) matching the tts_script exactly. This will be used for subtitles.",
                "You must provide 'short_on_screen_text' in Hinglish. This is the top title.",
                "Tone: Narrative, cinematic, emotionally deep.",
                "Return JSON ONLY.",
            ],
            "idea": idea,
            "output_schema": {
                "tts_script": "एक बार हनुमान जी ने राम जी से कहा...",
                "full_script": "Ek baar Hanuman Ji ne Ram Ji se kaha...",
                "short_on_screen_text": "Hanuman Ji Ki Bhakti",
            },
        }
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a master spiritual storyteller. You write magnetic, emotionally powerful "
                            "devotional stories. You output Devanagari for TTS and Hinglish for subtitles."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                temperature=0.85,
                max_tokens=800,
            )
            return parse_json_response(response.choices[0].message.content)
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Falling back from OpenAI script due to: %s", exc)
            return fallback_script(idea)

    def _save_content_record(self, idea: dict[str, Any], script: dict[str, Any]) -> None:
        from datetime import timezone
        history = read_json(CONTENT_HISTORY_FILE, {"items": []})
        history["items"] = history.get("items", [])[-300:] + [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "topic": idea["topic"],
                "theme": idea["theme"],
                "script": script["full_script"],
            }
        ]
        write_json(CONTENT_HISTORY_FILE, history)
