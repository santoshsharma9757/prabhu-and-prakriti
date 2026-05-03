from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from config import Settings
from content_strategy import clean_title, ensure_tags, normalize_text, score_seo
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
            return self._finalize_seo(
                fallback_seo(idea, script, self.settings.channel_name),
                idea,
            )

        prompt = {
            "task": "Generate high-CTR SEO metadata for a spiritual/devotional YouTube Short.",
            "rules": [
                "Return JSON only.",
                "Title must be in Hinglish and start with the strongest searchable deity, keyword, or topic phrase.",
                "Create curiosity, tension, warning, or emotional surprise in the title.",
                "Use at most 2 hashtags in the title and never use #viral or #trending.",
                "Description should be 1-2 short lines, give a reason to watch, and end with a simple comment CTA.",
                "Use 8-12 highly relevant tags in English and Hinglish.",
                "Use Hinglish (Hindi in English alphabet) for both title and description.",
            ],
            "channel_name": self.settings.channel_name,
            "idea": {"topic": idea.get("topic"), "theme": idea.get("theme")},
            "script": {
                "hook": script.get("hook"),
                "short_title": script.get("short_on_screen_text"),
            },
            "output_schema": {
                "title": "Hanuman Ji ka naam sankat mein kaise bachata hai? #shorts #bhakti",
                "description": "Sankat ke waqt Hanuman bhakti ka asli matlab samajhiye. Comment mein Jai Bajrangbali likho.",
                "hashtags": ["#shorts", "#hanuman", "#bhakti", "#sanatan"],
                "tags": [
                    "hanuman ji shorts",
                    "hanuman ji story",
                    "bhakti status hinglish",
                    "sanatan shorts",
                    "mahadev shorts",
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
                            "You are a YouTube Shorts SEO expert for Indian spiritual audiences."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            data = parse_json_response(response.choices[0].message.content)
            return self._finalize_seo(data, idea)
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Falling back from OpenAI SEO due to: %s", exc)
            return self._finalize_seo(
                fallback_seo(idea, script, self.settings.channel_name),
                idea,
            )

    def _finalize_seo(self, seo: dict[str, Any], idea: dict[str, Any]) -> dict[str, Any]:
        seo["title"] = clean_title(
            str(seo.get("title", "")) or str(idea.get("topic", "")),
            self.settings.title_max_length,
        )
        seo["description"] = normalize_text(str(seo.get("description", "")))
        if not seo["description"]:
            seo["description"] = (
                f"{idea.get('topic', '')} ka chhota sa sach. "
                "Comment mein apni bhakti likho. #shorts #bhakti"
            )
        seo["tags"] = ensure_tags(seo.get("tags"), idea)
        seo["hashtags"] = [
            tag
            for tag in seo.get("hashtags", ["#shorts", "#bhakti", "#sanatan"])
            if str(tag).lower() not in {"#viral", "#trending"}
        ][:5]
        seo_score, seo_reasons = score_seo(seo, idea)
        seo["seo_score"] = seo_score
        seo["seo_reasons"] = seo_reasons
        return seo
