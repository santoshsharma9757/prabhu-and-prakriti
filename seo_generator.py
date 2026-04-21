from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from config import Settings
from llm_fallback import fallback_seo, parse_json_response


LOGGER = logging.getLogger(__name__)


class SEOGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = (
            OpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    def generate(self, idea: dict[str, Any], script: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return fallback_seo(idea, script, self.settings.channel_name)
        prompt = {
            "task": "Generate SEO metadata for a spiritual/devotional YouTube Short.",
            "rules": [
                "Return JSON only.",
                "Title MUST have a curiosity-gap or emotional hook (e.g. 'Iski wajah se dukh aata hai? #shorts').",
                "Place 1 viral hashtag and 1 niche hashtag at the end of the title (e.g. #shorts #hanuman).",
                "Description should be ultra-short (under 30 words) to encourage loop-watching.",
                "Use 10-15 highly relevant tags in English.",
                "Use Hinglish (Hindi words in English Alphabet) for the title and description.",
            ],
            "channel_name": self.settings.channel_name,
            "idea": {"topic": idea.get("topic"), "theme": idea.get("theme")},
            "script": {"hook": script.get("hook"), "short_title": script.get("short_on_screen_text")},
            "output_schema": {
                "title": "Sabse Badi Shakti Hanuman Ji #shorts #hanuman",
                "description": "Janiye Hanuman ji ki sakti ke bare mein... #hanuman #bhakti",
                "hashtags": ["#shorts", "#hanuman", "#bhakti", "#mahakal", "#sanatan"],
                "tags": [
                    "hanuman ji shorts",
                    "bhakti status hinglish",
                    "sanatan dharma",
                ],
            },
        }
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a YouTube Shorts SEO expert for Indian spiritual audiences who consume Hinglish content."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            data = parse_json_response(response.choices[0].message.content)
            data["title"] = str(data.get("title", ""))[: self.settings.title_max_length]
            return data
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Falling back from OpenAI SEO due to: %s", exc)
            return fallback_seo(idea, script, self.settings.channel_name)
