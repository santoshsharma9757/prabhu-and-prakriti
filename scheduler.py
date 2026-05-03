from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from config import DATA_DIR, Settings, read_json, write_json


SCHEDULE_FILE = DATA_DIR / "schedule_queue.json"


@dataclass(slots=True)
class ScheduleItem:
    topic: str
    publish_at: str
    status: str = "planned"


def plan_schedule(topics: list[str], settings: Settings | None = None) -> list[ScheduleItem]:
    """Schedules 2 Shorts per day using stronger day-specific windows."""
    timezone_name = settings.scheduler_timezone if settings else "Asia/Kolkata"
    tz = ZoneInfo(timezone_name)
    now = datetime.now(tz)
    start_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # Based on recent Shorts timing guidance: evenings dominate, with Friday strongest.
    # Weekday mapping uses the strongest 2 slots for each day in local channel time.
    daily_slots: dict[int, list[tuple[int, int]]] = {
        0: [(20, 0), (17, 0)],  # Monday: 8 PM, 5 PM
        1: [(20, 0), (21, 0)],  # Tuesday: 8 PM, 9 PM
        2: [(19, 0), (20, 0)],  # Wednesday: 7 PM, 8 PM
        3: [(19, 0), (20, 0)],  # Thursday: 7 PM, 8 PM
        4: [(16, 0), (18, 0)],  # Friday: 4 PM, 6 PM
        5: [(19, 0), (11, 0)],  # Saturday: 7 PM, 11 AM
        6: [(19, 0), (20, 0)],  # Sunday: 7 PM, 8 PM
    }

    items = []
    current_topic_idx = 0
    day_offset = 0

    while current_topic_idx < len(topics):
        current_day = start_date + timedelta(days=day_offset)
        slots = daily_slots[current_day.weekday()]
        for hour, minute in slots:
            if current_topic_idx >= len(topics):
                break

            publish_time = current_day.replace(hour=hour, minute=minute)
            publish_str = publish_time.isoformat(timespec="seconds")

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
