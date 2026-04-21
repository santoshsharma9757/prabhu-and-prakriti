from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from config import DATA_DIR, read_json, write_json


SCHEDULE_FILE = DATA_DIR / "schedule_queue.json"


@dataclass(slots=True)
class ScheduleItem:
    topic: str
    publish_at: str
    status: str = "planned"


def plan_schedule(topics: list[str]) -> list[ScheduleItem]:
    """Schedules videos for 6:00 AM and 7:30 PM (19:30) starting from tomorrow."""
    now = datetime.now()
    # Start from tomorrow to ensure we have time to review
    start_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    slots = [
        (6, 0),    # 6:00 AM
        (19, 30)   # 7:30 PM
    ]
    
    items = []
    current_topic_idx = 0
    day_offset = 0
    
    while current_topic_idx < len(topics):
        current_day = start_date + timedelta(days=day_offset)
        for hour, minute in slots:
            if current_topic_idx >= len(topics):
                break
                
            publish_time = current_day.replace(hour=hour, minute=minute)
            items.append(ScheduleItem(
                topic=topics[current_topic_idx],
                publish_at=publish_time.isoformat(timespec="minutes")
            ))
            current_topic_idx += 1
        day_offset += 1
        
    return items


def save_schedule(items: list[ScheduleItem]) -> Path:
    existing = read_json(SCHEDULE_FILE, {"items": []})
    existing["items"] = existing.get("items", []) + [asdict(item) for item in items]
    write_json(SCHEDULE_FILE, existing)
    return SCHEDULE_FILE
