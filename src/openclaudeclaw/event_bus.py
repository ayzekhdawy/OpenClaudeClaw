"""
Harness Event Bus — lightweight JSONL event stream for runtime/session/tool activity
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
EVENT_LOG_PATH = WORKSPACE / ".harness" / "events.jsonl"


@dataclass
class HarnessEvent:
    type: str
    session_id: str = "system"
    source: str = "harness"
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class EventBus:
    def __init__(self, path: Path = EVENT_LOG_PATH):
        self.path = path

    def publish(self, event_type: str, *, session_id: str = "system", source: str = "harness", payload: Optional[dict] = None) -> dict:
        event = HarnessEvent(type=event_type, session_id=session_id, source=source, payload=payload or {})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return event.to_dict()

    def recent(self, *, session_id: Optional[str] = None, limit: int = 20, event_type: Optional[str] = None) -> list[dict]:
        if not self.path.exists():
            return []
        items: list[dict] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            if session_id and item.get("session_id") != session_id:
                continue
            if event_type and item.get("type") != event_type:
                continue
            items.append(item)
        return items[-limit:]

    def summary(self, *, session_id: Optional[str] = None, limit: int = 20) -> dict:
        recent = self.recent(session_id=session_id, limit=limit)
        counts: dict[str, int] = {}
        for item in recent:
            counts[item.get("type", "unknown")] = counts.get(item.get("type", "unknown"), 0) + 1
        return {
            "path": str(self.path),
            "count": len(recent),
            "types": counts,
            "items": recent,
        }


_EVENT_BUS: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _EVENT_BUS
    if _EVENT_BUS is None:
        _EVENT_BUS = EventBus()
    return _EVENT_BUS
