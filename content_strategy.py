from __future__ import annotations

import re
from typing import Any


GENERIC_HASHTAGS = {"#viral", "#trending", "#fyp", "#explore"}
PRIMARY_KEYWORDS = (
    "hanuman",
    "mahadev",
    "mahakal",
    "krishna",
    "ram",
    "radha",
    "durga",
    "vishnu",
    "bhakti",
    "sanatan",
    "nature",
    "prakriti",
)
HOOK_PHRASES = (
    "kyun",
    "kaise",
    "jab",
    "raaz",
    "sach",
    "seekh",
    "galti",
    "isliye",
)
ABSTRACT_WORDS = (
    "shanti",
    "discipline",
    "inner strength",
    "motivation",
    "guidance",
    "wisdom",
    "reflection",
    "connection",
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def limit_hashtags(text: str, max_count: int = 2) -> str:
    parts = normalize_text(text).split()
    kept: list[str] = []
    hashtags = 0
    for part in parts:
        if part.startswith("#"):
            if hashtags >= max_count:
                continue
            hashtags += 1
        kept.append(part)
    return " ".join(kept)


def clean_title(title: str, max_length: int) -> str:
    title = limit_hashtags(title, max_count=2)
    title = normalize_text(title)
    words = [word for word in title.split() if word.lower() not in GENERIC_HASHTAGS]
    title = " ".join(words)
    if len(title) <= max_length:
        return title

    shortened = []
    for word in title.split():
        candidate = " ".join(shortened + [word])
        if len(candidate) > max_length:
            break
        shortened.append(word)
    return " ".join(shortened)[:max_length].strip()


def ensure_tags(tags: list[str] | None, idea: dict[str, Any]) -> list[str]:
    values = [normalize_text(str(tag)) for tag in (tags or []) if normalize_text(str(tag))]
    topic = normalize_text(str(idea.get("topic", "")))
    theme = normalize_text(str(idea.get("theme", "")))
    keyword_pool = [topic, theme]
    for keyword in keyword_pool:
        if keyword and keyword.lower() not in {tag.lower() for tag in values}:
            values.append(keyword)
    return values[:12]


def score_idea(idea: dict[str, Any]) -> tuple[int, list[str]]:
    topic = normalize_text(str(idea.get("topic", "")))
    hook = normalize_text(str(idea.get("hook", "")))
    score = 0
    reasons: list[str] = []
    topic_l = topic.lower()
    hook_l = hook.lower()

    if 28 <= len(topic) <= 68:
        score += 20
        reasons.append("topic_length")
    if any(word in topic_l for word in PRIMARY_KEYWORDS):
        score += 20
        reasons.append("search_keyword")
    if any(word in topic_l for word in HOOK_PHRASES):
        score += 20
        reasons.append("curiosity_topic")
    if any(word in hook_l for word in HOOK_PHRASES):
        score += 15
        reasons.append("curiosity_hook")
    if "?" in topic or "?" in hook:
        score += 10
        reasons.append("question_format")
    if not any(word in topic_l for word in ABSTRACT_WORDS):
        score += 10
        reasons.append("specific_topic")
    if len(topic.split()) <= 12:
        score += 10
        reasons.append("compact_topic")
    if topic and hook and topic_l != hook_l:
        score += 5
        reasons.append("distinct_hook")

    return score, reasons


def score_script(script: dict[str, Any]) -> tuple[int, list[str]]:
    text = normalize_text(str(script.get("full_script", "")))
    score = 0
    reasons: list[str] = []
    words = text.split()
    if 55 <= len(words) <= 95:
        score += 25
        reasons.append("shorts_length")
    if len(words) >= 8:
        opener = " ".join(words[:8]).lower()
        if any(word in opener for word in HOOK_PHRASES + PRIMARY_KEYWORDS):
            score += 25
            reasons.append("strong_open")
    if text.count(".") + text.count("!") + text.count("?") >= 4:
        score += 15
        reasons.append("beat_structure")
    if not re.search(r"\bfollow\b|\bsubscribe\b", text.lower()):
        score += 10
        reasons.append("soft_cta")
    if not re.search(r"\bsadak\b|\bgaav mein andhera\b", text.lower()):
        score += 10
        reasons.append("less_generic_story")
    return score, reasons


def score_seo(seo: dict[str, Any], idea: dict[str, Any]) -> tuple[int, list[str]]:
    title = normalize_text(str(seo.get("title", "")))
    description = normalize_text(str(seo.get("description", "")))
    topic = normalize_text(str(idea.get("topic", ""))).lower()
    score = 0
    reasons: list[str] = []

    if 32 <= len(title) <= 62:
        score += 25
        reasons.append("title_length")
    if sum(1 for token in title.split() if token.startswith("#")) <= 2:
        score += 15
        reasons.append("light_hashtags")
    if not any(tag in title.lower() for tag in GENERIC_HASHTAGS):
        score += 15
        reasons.append("no_spam_hashtags")
    if any(keyword in title.lower() for keyword in PRIMARY_KEYWORDS):
        score += 20
        reasons.append("keyword_title")
    if any(token in title.lower() for token in HOOK_PHRASES):
        score += 15
        reasons.append("curiosity_title")
    if description and topic[:18] and topic[:18] not in description.lower():
        score += 10
        reasons.append("description_not_redundant")
    return score, reasons


def build_audit(idea: dict[str, Any], script: dict[str, Any], seo: dict[str, Any]) -> dict[str, Any]:
    idea_score, idea_reasons = score_idea(idea)
    script_score, script_reasons = score_script(script)
    seo_score, seo_reasons = score_seo(seo, idea)
    total = round((idea_score + script_score + seo_score) / 3, 2)
    return {
        "viral_score": total,
        "idea_score": idea_score,
        "script_score": script_score,
        "seo_score": seo_score,
        "idea_reasons": idea_reasons,
        "script_reasons": script_reasons,
        "seo_reasons": seo_reasons,
    }
