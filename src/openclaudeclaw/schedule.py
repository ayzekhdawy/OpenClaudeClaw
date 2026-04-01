"""
Harness Schedule/Cron surface — JSON-backed compatible layer
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
SCHEDULES_PATH = WORKSPACE / "memory" / "schedules.json"
_CRON_RE = re.compile(r"^[\w\*/,\-]+\s+[\w\*/,\-]+\s+[\w\*/,\-]+\s+[\w\*/,\-]+\s+[\w\*/,\-]+$")


@dataclass
class ScheduledTask:
    id: str
    name: str
    cron: str
    command: str
    enabled: bool = True
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run_at: Optional[str] = None


class ScheduleStore:
    def __init__(self, path: Path = SCHEDULES_PATH):
        self.path = path
        self.schedules: dict[str, ScheduledTask] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.schedules = {k: ScheduledTask(**v) for k, v in data.items()}
            except Exception:
                self.schedules = {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: asdict(v) for k, v in self.schedules.items()}, indent=2))

    def validate_cron(self, cron: str) -> bool:
        return bool(_CRON_RE.match(cron.strip()))

    def create(self, name: str, cron: str, command: str, description: str = "") -> dict:
        if not self.validate_cron(cron):
            return {"error": f"Invalid cron expression: {cron}"}
        item = ScheduledTask(id=str(uuid.uuid4())[:8], name=name, cron=cron.strip(), command=command, description=description)
        self.schedules[item.id] = item
        self._save()
        return {"status": "created", **asdict(item)}

    def list(self, enabled: Optional[bool] = None) -> dict:
        items = list(self.schedules.values())
        if enabled is not None:
            items = [x for x in items if x.enabled == enabled]
        return {"total": len(items), "items": [asdict(x) for x in items]}

    def get(self, schedule_id: str) -> Optional[dict]:
        item = self.schedules.get(schedule_id)
        return asdict(item) if item else None

    def update(self, schedule_id: str, **updates) -> dict:
        item = self.schedules.get(schedule_id)
        if not item:
            return {"error": f"Schedule not found: {schedule_id}"}
        if "cron" in updates and updates["cron"] and not self.validate_cron(updates["cron"]):
            return {"error": f"Invalid cron expression: {updates['cron']}"}
        for key, value in updates.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.now().isoformat()
        self._save()
        return {"status": "updated", **asdict(item)}

    def stop(self, schedule_id: str) -> dict:
        return self.update(schedule_id, enabled=False)


_schedule_store: Optional[ScheduleStore] = None


def get_schedule_store() -> ScheduleStore:
    global _schedule_store
    if _schedule_store is None:
        _schedule_store = ScheduleStore()
    return _schedule_store
