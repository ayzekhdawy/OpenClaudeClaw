"""
Session Cleanup & Cost Tracker — session lifecycle cleanup and real token/cost accounting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
PLATFORM_SESSIONS_PATH = WORKSPACE / "memory" / "platform_sessions.json"
COST_LOG_PATH = WORKSPACE / ".harness" / "cost_log.jsonl"


@dataclass
class CostEntry:
    session_id: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ms": self.duration_ms,
            "cost": self.cost,
            "timestamp": self.timestamp,
        }


# Approximate cost per 1M tokens (USD)
TOKEN_COSTS = {
    "claude-sonnet-4.5": {"input_per_m": 3.0, "output_per_m": 15.0},
    "qwen2.5:14b": {"input_per_m": 0.0, "output_per_m": 0.0},
    "qwen3.5:397b-cloud": {"input_per_m": 0.1, "output_per_m": 0.3},
}


class SessionCleanup:
    def __init__(self, sessions_path: Path = PLATFORM_SESSIONS_PATH):
        self.sessions_path = sessions_path
        self.sessions = {}
        self.load()

    def load(self) -> dict:
        if self.sessions_path.exists():
            try:
                self.sessions = json.loads(self.sessions_path.read_text())
            except Exception:
                self.sessions = {}
        return self.sessions

    def save(self) -> Path:
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        self.sessions_path.write_text(json.dumps(self.sessions, indent=2))
        return self.sessions_path

    def list_sessions(self) -> list[dict]:
        return list(self.sessions.values())

    def cleanup_stale(self, max_age_hours: int = 24) -> list[str]:
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        removed = []
        for sid, sess in list(self.sessions.items()):
            last_seen_str = sess.get("last_seen", "")
            if last_seen_str:
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    if last_seen < cutoff:
                        del self.sessions[sid]
                        removed.append(sid)
                except Exception:
                    pass
        if removed:
            self.save()
        return removed

    def cleanup_completed(self) -> list[str]:
        removed = []
        for sid, sess in list(self.sessions.items()):
            lifecycle = sess.get("lifecycle", "")
            if lifecycle in ("completed", "exited", "timeout"):
                del self.sessions[sid]
                removed.append(sid)
        if removed:
            self.save()
        return removed

    def update_last_seen(self, session_id: str) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        self.sessions[session_id]["last_seen"] = datetime.now().isoformat()
        self.save()


class CostTracker:
    def __init__(self, log_path: Path = COST_LOG_PATH):
        self.log_path = log_path

    def log_cost(self, entry: CostEntry) -> Path:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return self.log_path

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = TOKEN_COSTS.get(model, {"input_per_m": 0.0, "output_per_m": 0.0})
        return (input_tokens / 1_000_000) * rates["input_per_m"] + (output_tokens / 1_000_000) * rates["output_per_m"]

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def total_cost(self, session_id: Optional[str] = None) -> float:
        if not self.log_path.exists():
            return 0.0
        total = 0.0
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if session_id and entry.get("session_id") != session_id:
                    continue
                total += entry.get("cost", 0.0)
            except Exception:
                continue
        return round(total, 6)

    def summary(self, session_id: Optional[str] = None) -> dict:
        if not self.log_path.exists():
            return {"total_cost": 0.0, "entries": 0, "session_id": session_id}
        entries = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if session_id and entry.get("session_id") != session_id:
                    continue
                entries.append(entry)
            except Exception:
                continue
        return {
            "total_cost": round(sum(e.get("cost", 0.0) for e in entries), 6),
            "entries": len(entries),
            "session_id": session_id,
        }


_SESSION_CLEANUP: Optional[SessionCleanup] = None
_COST_TRACKER: Optional[CostTracker] = None


def get_session_cleanup() -> SessionCleanup:
    global _SESSION_CLEANUP
    if _SESSION_CLEANUP is None:
        _SESSION_CLEANUP = SessionCleanup()
    return _SESSION_CLEANUP


def get_cost_tracker() -> CostTracker:
    global _COST_TRACKER
    if _COST_TRACKER is None:
        _COST_TRACKER = CostTracker()
    return _COST_TRACKER
