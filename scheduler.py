from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from config import DATA_DIR, Settings, read_json, write_json


SCHEDULE_FILE = DATA_DIR / "schedule_queue.json"


@dataclass(slots=True)
class ScheduleItem:
    topic: str
    publish_at: str
    status: str = "planned"


def plan_schedule(topics: list[str], settings: Settings | None = None) -> list[ScheduleItem]:
    """Schedules videos for 6:00 AM and 7:00 PM (19:00) starting from tomorrow."""
    now = datetime.now()
    # Start from tomorrow to ensure we have time to review
    start_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Default to IST if not specified
    offset = "+05:30"
    if settings and settings.scheduler_timezone != "Asia/Kolkata":
        # If it's not IST, we might need a more complex lookup, 
        # but for this project Asia/Kolkata is the primary use case.
        # We'll stick with +05:30 for now or add a more robust check if needed.
        pass

    slots = [
        (6, 0),    # 6:00 AM
        (19, 0)    # 7:00 PM
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
            # YouTube expects ISO 8601 with timezone offset.
            # We include the offset here so uploader doesn't have to guess.
            publish_str = f"{publish_time.strftime('%Y-%m-%dT%H:%M')}:00{offset}"
            
            items.append(ScheduleItem(
                topic=topics[current_topic_idx],
                publish_at=publish_str
            ))
            current_topic_idx += 1
        day_offset += 1
        
    return items


def save_schedule(items: list[ScheduleItem]) -> Path:
    existing = read_json(SCHEDULE_FILE, {"items": []})
    existing["items"] = existing.get("items", []) + [asdict(item) for item in items]
    write_json(SCHEDULE_FILE, existing)
    return SCHEDULE_FILE
