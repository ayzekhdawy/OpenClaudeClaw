"""
Live Diagnostics / Streaming Event Reader — real-time subscription to event stream with callbacks.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
EVENT_LOG_PATH = WORKSPACE / ".harness" / "events.jsonl"


@dataclass
class Subscription:
    id: str
    callback: Callable[[dict], None]
    filter_type: Optional[str] = None
    filter_session: Optional[str] = None
    active: bool = True
    created_at: float = field(default_factory=lambda: time.time())


class LiveDiagnostics:
    def __init__(self, event_log_path: Path = EVENT_LOG_PATH):
        self.event_log_path = event_log_path
        self.subscriptions: dict[str, Subscription] = {}
        self._lock = threading.Lock()
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_watch = threading.Event()
        self._last_read_position = 0
        if self.event_log_path.exists():
            self._last_read_position = self.event_log_path.stat().st_size

    def subscribe(
        self,
        callback: Callable[[dict], None],
        event_type: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        sub_id = f"sub-{len(self.subscriptions) + 1}"
        sub = Subscription(
            id=sub_id,
            callback=callback,
            filter_type=event_type,
            filter_session=session_id,
        )
        with self._lock:
            self.subscriptions[sub_id] = sub
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        with self._lock:
            if subscription_id in self.subscriptions:
                self.subscriptions[subscription_id].active = False
                del self.subscriptions[subscription_id]
                return True
        return False

    def _dispatch(self, event: dict) -> None:
        with self._lock:
            subs = list(self.subscriptions.values())
        for sub in subs:
            if not sub.active:
                continue
            if sub.filter_type and event.get("type") != sub.filter_type:
                continue
            if sub.filter_session and event.get("session_id") != sub.filter_session:
                continue
            try:
                sub.callback(event)
            except Exception:
                pass

    def read_new_events(self) -> list[dict]:
        if not self.event_log_path.exists():
            return []
        current_size = self.event_log_path.stat().st_size
        if current_size <= self._last_read_position:
            return []
        with self.event_log_path.open("r", encoding="utf-8") as f:
            f.seek(self._last_read_position)
            lines = f.readlines()
            self._last_read_position = f.tell()
        events = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
        return events

    def poll(self, timeout_ms: int = 0) -> list[dict]:
        events = []
        if timeout_ms > 0:
            deadline = time.time() + timeout_ms / 1000
            while time.time() < deadline and not events:
                new_events = self.read_new_events()
                for event in new_events:
                    self._dispatch(event)
                events.extend(new_events)
                if not events:
                    time.sleep(0.05)
        else:
            new_events = self.read_new_events()
            for event in new_events:
                self._dispatch(event)
            events = new_events
        return events

    def start_watching(self, poll_interval: float = 0.5) -> None:
        if self._watch_thread and self._watch_thread.is_alive():
            return
        self._stop_watch.clear()
        def watch_loop():
            while not self._stop_watch.is_set():
                self.poll()
                time.sleep(poll_interval)
        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()

    def stop_watching(self) -> None:
        self._stop_watch.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=2.0)
            self._watch_thread = None

    def snapshot(self) -> dict:
        new_events = self.read_new_events()
        for event in new_events:
            self._dispatch(event)
        return {
            "subscription_count": len([s for s in self.subscriptions.values() if s.active]),
            "watching": self._watch_thread is not None and self._watch_thread.is_alive(),
            "new_events_since_call": len(new_events),
            "events": new_events,
        }


_LIVE_DIAGNOSTICS: Optional[LiveDiagnostics] = None


def get_live_diagnostics() -> LiveDiagnostics:
    global _LIVE_DIAGNOSTICS
    if _LIVE_DIAGNOSTICS is None:
        _LIVE_DIAGNOSTICS = LiveDiagnostics()
    return _LIVE_DIAGNOSTICS
