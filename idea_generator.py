from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import requests
from pathlib import Path
from openai import OpenAI

from config import DATA_DIR, Settings, read_json, write_json
from content_strategy import normalize_text, score_idea
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
        ranked = sorted(bank, key=lambda item: score_idea(item)[0], reverse=True)
        return ranked[:8]

    def _discover_youtube_trends(self, topic_hint: str | None) -> list[dict[str, Any]]:
        # If API key is provided, use the fast requests method
        if self.settings.bhakti_youtube_api_key:
            return self._discover_with_api_key(topic_hint)
        
        # Fallback: Try to use OAuth token if configured
        if self.settings.bhakti_youtube_client_secret_file and self.settings.bhakti_youtube_token_file:
            return self._discover_with_oauth(topic_hint)
            
        return []

    def _discover_with_api_key(self, topic_hint: str | None) -> list[dict[str, Any]]:
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
                        "order": "viewCount",
                        "maxResults": 5,
                        "q": query,
                        "regionCode": self.settings.country_code,
                        "relevanceLanguage": "hi",
                        "key": self.settings.bhakti_youtube_api_key,
                    },
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
                for item in data.get("items", []):
                    title = item.get("snippet", {}).get("title", "").strip()
                    if title:
                        ideas.append({
                            "theme": "Spirituality",
                            "topic": title,
                            "hook": "Aakhir is baat ka raaz kya hai?",
                            "cta": "Comment mein apni bhakti likho.",
                            "queries": ["spiritual india", "temple bells", "meditation india"],
                        })
            except Exception as exc:
                LOGGER.warning("YouTube trend discovery failed for '%s': %s", query, exc)
        return ideas

    def _discover_with_oauth(self, topic_hint: str | None) -> list[dict[str, Any]]:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            scopes = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube"]
            token_path = Path(self.settings.bhakti_youtube_token_file)
            if not token_path.exists():
                return []
                
            credentials = Credentials.from_authorized_user_file(str(token_path), scopes)
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
            youtube = build("youtube", "v3", credentials=credentials)
            
            trend_queries = [topic_hint, "spiritual stories", "ancient wisdom"]
            trend_queries = [item for item in trend_queries if item]
            ideas = []
            
            for query in trend_queries:
                request = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    order="viewCount",
                    maxResults=5,
                    regionCode=self.settings.country_code,
                    relevanceLanguage="hi"
                )
                response = request.execute()
                for item in response.get("items", []):
                    title = item["snippet"]["title"]
                    ideas.append({
                        "theme": "Spirituality",
                        "topic": title,
                        "hook": "Is video ka raaz kya hai?",
                        "cta": "Like aur subscribe karein.",
                        "queries": ["spiritual india", "temple bells"],
                    })
            return ideas
        except Exception as e:
            LOGGER.warning("OAuth trend discovery failed: %s", e)
            return []

    def generate(self, count: int = 1, topic_hint: str | None = None) -> list[dict[str, Any]]:
        history = self._load_history()
        used_topics = {item.strip().lower() for item in history.get("used_topics", [])}
        seed_bank = self._available_seed_bank(topic_hint)
        candidates = self._generate_with_llm(count=count, topic_hint=topic_hint, seed_bank=seed_bank)

        ranked_candidates = sorted(
            (self._normalize_candidate(item) for item in candidates),
            key=lambda item: score_idea(item)[0],
            reverse=True,
        )

        fresh_items = []
        for item in ranked_candidates:
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

    def _normalize_candidate(self, item: dict[str, Any]) -> dict[str, Any]:
        topic = normalize_text(str(item.get("topic", "")))
        hook = normalize_text(str(item.get("hook", "")))
        item["topic"] = topic
        item["hook"] = hook or f"{topic} ka asli raaz kya hai?"
        item["theme"] = normalize_text(str(item.get("theme", "Bhakti Shorts"))) or "Bhakti Shorts"
        item["core_message"] = normalize_text(str(item.get("core_message", "")))
        item["cta"] = normalize_text(str(item.get("cta", "Comment mein apni bhakti likho.")))
        visual_queries = item.get("visual_queries") or item.get("queries") or []
        item["visual_queries"] = [normalize_text(str(query)) for query in visual_queries][:5]
        if not item["visual_queries"]:
            item["visual_queries"] = ["spiritual india", "temple bells", "cinematic prayer", "sunrise temple"]
        top_text = normalize_text(str(item.get("top_text", "")))
        item["top_text"] = top_text or topic[:36]
        return item

    def _generate_with_llm(
        self,
        count: int,
        topic_hint: str | None,
        seed_bank: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not self.client:
            return fallback_ideas(count=count, topic_hint=topic_hint)

        import random
        # 50% God storytelling, 50% Nature/Universe discussion
        god_focus = "Life lessons from Hanuman Ji, Shiva, Ram Ji, or Krishna. Focus on their stories and virtues."
        nature_focus = "Pure Nature, Mountains, Rivers, Universe, and Soul. Focus on the beauty of creation, peace, and environment. NO specific mention of deities in these topics."
        
        god_visuals = "'temple india', 'shiva statue', 'hanuman statue', 'indian god', 'hindu prayer'"
        nature_visuals = "'himalayan mountains', 'forest river', 'green valley', 'sunrise nature', 'peaceful landscape'"

        if count >= 2:
            theme_focus = f"A balanced 50/50 mix of '{god_focus}' and '{nature_focus}'."
            visual_focus = f"Use {god_visuals} for God topics and {nature_visuals} for Nature topics."
        else:
            is_nature_theme = random.random() < 0.5
            theme_focus = nature_focus if is_nature_theme else god_focus
            visual_focus = nature_visuals if is_nature_theme else god_visuals

        prompt = {
            "task": f"Generate original YouTube Shorts ideas for a Sanatan/spiritual storytelling channel.",
            "rules": [
                "Return valid JSON only.",
                "Language must be Hinglish (Hindi written in the English alphabet).",
                f"Topic FOCUS for this generation: {theme_focus}",
                "Each item needs theme, topic, hook, core_message, cta, visual_queries, top_text.",
                "Every topic must be instantly understandable for a new viewer with 0 context.",
                "Prefer curiosity, tension, emotional contrast, hidden lesson, or a surprising spiritual fact.",
                "Avoid broad self-help abstractions like peace, discipline, positivity, inner strength unless tied to a specific story or question.",
                "Keep topic length between 6 and 12 words.",
                "The first 3 words should usually contain the deity, story, or strongest keyword.",
                "Do not produce generic English titles like 'Inner Strength' or 'Nature Reflection'.",
                "visual_queries should be list of 4-5 English terms for Pexels search. Use cinematic, high-quality terms.",
                f"MUST heavily feature words like {visual_focus} but also include descriptive adjectives like 'cinematic', 'epic', 'sacred', 'glowing'.",
                "top_text should be short, punchy Hinglish.",
            ],
            "count": count,
            "topic_hint": topic_hint or "",
            "seed_bank": seed_bank,
            "output_schema": {
                "ideas": [
                    {
                        "theme": "Discussion with God",
                        "topic": "Hanuman Ji ka naam sankat mein kaise bachata hai?",
                        "hook": "Sankat mein sabse pehle Hanuman Ji ka naam hi kyun liya jata hai?",
                        "core_message": "Dukh hume majboot banane ke liye aata hai.",
                        "cta": "Om Shanti likhein.",
                        "visual_queries": ["person praying to sky", "monsoon rain forest", "spiritual light", "meditation nature"],
                        "top_text": "Sankat Ka Raaz",
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
