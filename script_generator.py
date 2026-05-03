from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

from openai import OpenAI

from config import DATA_DIR, Settings, read_json, write_json
from content_strategy import normalize_text, score_script
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
        script = self._polish_script(script, idea)
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
                "Open with a 1-line hook in the first 2 seconds.",
                "Use 5-7 short sentences, each easy to read in subtitles.",
                "Focus on one clear payoff, not a broad sermon.",
                "Avoid filler lines, repeated moralizing, or generic 'bhakti gives peace' statements.",
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

    def _polish_script(self, script: dict[str, Any], idea: dict[str, Any]) -> dict[str, Any]:
        full_script = normalize_text(str(script.get("full_script", "")))
        if not full_script:
            full_script = normalize_text(str(idea.get("hook", "")))

        opener = normalize_text(str(script.get("hook", ""))) or normalize_text(str(idea.get("hook", "")))
        if opener and not full_script.lower().startswith(opener.lower()):
            full_script = f"{opener} {full_script}"

        full_script = re.sub(r"\b(follow|subscribe|like and subscribe)\b", "yaad rakho", full_script, flags=re.IGNORECASE)
        script["full_script"] = full_script
        script["tts_script"] = normalize_text(str(script.get("tts_script", ""))) or full_script
        script["short_on_screen_text"] = normalize_text(str(script.get("short_on_screen_text", ""))) or normalize_text(str(idea.get("top_text", ""))) or normalize_text(str(idea.get("topic", "")))[:36]

        score, _ = score_script(script)
        if score < 45:
            script["full_script"] = f"{normalize_text(str(idea.get('hook', '')))} {normalize_text(str(idea.get('core_message', 'Bhakti ka matlab andheron mein bhi disha paana hai.')))} {normalize_text(str(idea.get('cta', 'Comment mein apni bhakti likho.')))}"
        return script

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
