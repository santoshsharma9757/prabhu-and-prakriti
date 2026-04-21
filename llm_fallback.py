from __future__ import annotations

import json
import random
from typing import Any

from viral_topics import get_seed_topics, list_theme_names, search_local_trends


def fallback_ideas(count: int = 1, topic_hint: str | None = None) -> list[dict[str, Any]]:
    if topic_hint:
        matches = search_local_trends(topic_hint, limit=max(count, 5))
        source = matches or get_seed_topics(limit=max(count, 5))
    else:
        source = get_seed_topics(limit=max(count, 5))
    ideas = []
    for idx in range(count):
        seed = source[idx % len(source)]
        ideas.append(
            {
                "theme": seed.get("theme", random.choice(list_theme_names())),
                "topic": seed["topic"],
                "hook": seed["hook"],
                "core_message": (
                    "कठिन समय, भय या भ्रम में भक्ति मन को स्थिर करती है और जीवन को दिशा देती है।"
                ),
                "cta": seed["cta"],
                "visual_queries": seed["queries"],
                "top_text": str(seed["hook"])[:42],
            }
        )
    return ideas


def fallback_script(idea: dict[str, Any]) -> dict[str, Any]:
    hook = idea["hook"]
    topic = idea["topic"]
    cta = idea["cta"]
    lines = [
        hook,
        f"कई बार जीवन में ऐसा दौर आता है, जब {topic.split(' ')[0]} भी दूर लगता है और मन डर से भर जाता है।",
        "लेकिन सनातन हमें याद दिलाता है कि भरोसा, धैर्य और भक्ति कभी व्यर्थ नहीं जाते।",
        "जब इंसान अहंकार छोड़कर श्रद्धा से आगे बढ़ता है, तभी भीतर की शक्ति जागती है।",
        "आज का संदेश यही है, परिस्थिति नहीं, विश्वास तुम्हारी दिशा तय करता है।",
        f"{cta} और ऐसे ही आध्यात्मिक शॉर्ट्स के लिए फॉलो करो।",
    ]
    return {
        "hook": hook,
        "problem": lines[1],
        "insight": f"{lines[2]} {lines[3]}",
        "takeaway": lines[4],
        "cta": lines[5],
        "full_script": " ".join(lines),
        "short_on_screen_text": idea.get("top_text", hook),
    }


def fallback_seo(idea: dict[str, Any], script: dict[str, Any], channel_name: str) -> dict[str, Any]:
    title = idea["topic"]
    description = (
        f"{script['hook']} {script['takeaway']} "
        f"{script['cta']} #{channel_name.replace(' ', '')} #bhakti #sanatan #shorts"
    )
    return {
        "title": title[:65],
        "description": description[:300],
        "hashtags": [
            "#shorts",
            "#bhakti",
            "#sanatan",
            "#mahakal",
            "#hanuman",
            "#motivation",
        ],
        "tags": [
            "bhakti shorts",
            "hindi devotional shorts",
            "sanatan motivation",
            "mahakal status",
            "hanuman ji motivation",
        ],
    }


def parse_json_response(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise
