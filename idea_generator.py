from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import requests
from openai import OpenAI

from config import DATA_DIR, Settings, read_json, write_json
from llm_fallback import fallback_ideas, parse_json_response
from viral_topics import get_seed_topics, list_theme_names, search_local_trends


LOGGER = logging.getLogger(__name__)
IDEA_HISTORY_FILE = DATA_DIR / "idea_history.json"


class IdeaGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = (
            OpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    def _load_history(self) -> dict[str, Any]:
        return read_json(IDEA_HISTORY_FILE, {"used_topics": [], "items": []})

    def _save_history(self, history: dict[str, Any]) -> None:
        write_json(IDEA_HISTORY_FILE, history)

    def _available_seed_bank(self, topic_hint: str | None) -> list[dict[str, Any]]:
        bank = []
        if topic_hint:
            local = search_local_trends(topic_hint, limit=10)
            bank.extend(local)
        bank.extend(self._discover_youtube_trends(topic_hint))
        if not bank:
            bank.extend(get_seed_topics(limit=12))
        return bank[:5]

    def _discover_youtube_trends(self, topic_hint: str | None) -> list[dict[str, Any]]:
        if not self.settings.bhakti_youtube_api_key:
            return []

        trend_queries = [
            topic_hint,
            "spiritual stories",
            "meaning of life shorts",
            "ancient wisdom",
            "faith shorts",
        ]
        trend_queries = [item for item in trend_queries if item]
        ideas: list[dict[str, Any]] = []
        for query in trend_queries[:4]:
            try:
                response = requests.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "type": "video",
                        "order": "relevance",
                        "maxResults": 5,
                        "q": query,
                        "regionCode": self.settings.country_code,
                        "relevanceLanguage": "en",
                        "key": self.settings.bhakti_youtube_api_key,
                    },
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
                for item in data.get("items", []):
                    title = item.get("snippet", {}).get("title", "").strip()
                    if not title:
                        continue
                    ideas.append(
                        {
                            "theme": "Spirituality",
                            "topic": title,
                            "hook": "Ever wondered why...",
                            "cta": "Like and subscribe.",
                            "queries": ["spiritual", "meditation"],
                        }
                    )
            except Exception as exc:
                LOGGER.warning("YouTube trend discovery failed for '%s': %s", query, exc)
        return ideas

    def generate(self, count: int = 1, topic_hint: str | None = None) -> list[dict[str, Any]]:
        history = self._load_history()
        used_topics = {item.strip().lower() for item in history.get("used_topics", [])}
        seed_bank = self._available_seed_bank(topic_hint)
        candidates = self._generate_with_llm(count=count, topic_hint=topic_hint, seed_bank=seed_bank)

        fresh_items = []
        for item in candidates:
            key = str(item["topic"]).strip().lower()
            if key not in used_topics:
                fresh_items.append(item)
                used_topics.add(key)
            if len(fresh_items) >= count:
                break

        if len(fresh_items) < count:
            for item in fallback_ideas(count=count, topic_hint=topic_hint):
                key = str(item["topic"]).strip().lower()
                if key not in used_topics:
                    fresh_items.append(item)
                    used_topics.add(key)
                if len(fresh_items) >= count:
                    break

        timestamp = datetime.now(timezone.utc).isoformat()
        history["used_topics"] = list(used_topics)[-500:]
        history["items"] = history.get("items", [])[-200:] + [
            {"timestamp": timestamp, "topic": item["topic"], "theme": item["theme"]}
            for item in fresh_items
        ]
        self._save_history(history)
        return fresh_items

    def _generate_with_llm(
        self,
        count: int,
        topic_hint: str | None,
        seed_bank: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not self.client:
            return fallback_ideas(count=count, topic_hint=topic_hint)

        import random
        # 70% God storytelling, 30% Nature/Universe discussion
        is_nature_theme = random.random() < 0.3
        
        if is_nature_theme:
            theme_focus = "Nature, Meditation, Karma, Universe, or a devotee asking God for guidance in front of nature."
            visual_focus = "'meditation nature', 'monsoon rain forest', 'person praying to sky', 'spiritual light', 'mountain sunrise'"
        else:
            theme_focus = "God storytelling, Parables, and Life lessons directly from Hanuman Ji, Shiva, Ram Ji, or Krishna."
            visual_focus = "'temple india', 'shiva statue', 'hanuman statue', 'indian god', 'hindu prayer'"

        prompt = {
            "task": f"Generate original YouTube Shorts ideas for a Sanatan/spiritual storytelling channel.",
            "rules": [
                "Return valid JSON only.",
                "Language must be Hinglish (Hindi written in the English alphabet).",
                f"Topic FOCUS for this generation: {theme_focus}",
                "Each item needs theme, topic, hook, core_message, cta, visual_queries, top_text.",
                f"visual_queries should be list of 4-5 English terms for Pexels search. MUST heavily feature words like {visual_focus}.",
                "top_text should be short, punchy Hinglish.",
            ],
            "count": count,
            "topic_hint": topic_hint or "",
            "seed_bank": seed_bank,
            "output_schema": {
                "ideas": [
                    {
                        "theme": "Discussion with God",
                        "topic": "Jab Bhakt Ne Bhagwan Se Pucha Dukh Kyu Hai",
                        "hook": "Ek baar ek bhakt ne ishwar se pucha...",
                        "core_message": "Dukh hume majboot banane ke liye aata hai.",
                        "cta": "Om Shanti likhein.",
                        "visual_queries": ["person praying to sky", "monsoon rain forest", "spiritual light", "meditation nature"],
                        "top_text": "Ishwar Se Samwaad",
                    }
                ]
            },
        }
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an elite YouTube Shorts strategist for global spiritual storytelling. "
                            "You craft viral, deeply emotional narrative topics in English."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                temperature=0.9,
                max_tokens=600,
            )
            raw_text = response.choices[0].message.content
            parsed = parse_json_response(raw_text)
            ideas = parsed.get("ideas", [])
            LOGGER.info("Generated %s ideas from OpenAI", len(ideas))
            return ideas or fallback_ideas(count=count, topic_hint=topic_hint)
        except Exception as exc:
            LOGGER.warning("Falling back from OpenAI ideas due to: %s", exc)
            return fallback_ideas(count=count, topic_hint=topic_hint)
