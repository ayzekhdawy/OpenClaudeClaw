"""
OpenClaw Session Adapter — bridge local registry to platform-like session runs
─────────────────────────────────────────────────────────────────────────────
Creates a safer adapter layer so the harness can move toward native OpenClaw
session/subagent semantics without hard-coupling to live platform APIs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
import os
from typing import Optional

from .event_bus import get_event_bus

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
SESSION_REGISTRY_PATH = WORKSPACE / "memory" / "platform_sessions.json"


@dataclass
class PlatformSessionRun:
    id: str
    agent_id: str
    session_type: str = "subagent"
    platform: str = "openclaw-compatible"
    title: str = ""
    prompt: str = ""
    command: str = ""
    cwd: str = str(WORKSPACE)
    pid: Optional[int] = None
    status: str = "created"
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class OpenClawSessionAdapter:
    def __init__(self, path: Path = SESSION_REGISTRY_PATH):
        self.path = path
        self.sessions: dict[str, PlatformSessionRun] = {}
        self.events = get_event_bus()
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text())
            self.sessions = {k: PlatformSessionRun(**v) for k, v in payload.items()}
        except Exception:
            self.sessions = {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: asdict(v) for k, v in self.sessions.items()}, indent=2))

    def register_run(self, *, agent_id: str, prompt: str, command: str, cwd: str, pid: Optional[int], title: str = "", metadata: Optional[dict] = None) -> dict:
        session_id = f"sess-{agent_id}"
        run = PlatformSessionRun(
            id=session_id,
            agent_id=agent_id,
            title=title or f"Subagent {agent_id}",
            prompt=prompt,
            command=command,
            cwd=cwd,
            pid=pid,
            status="running" if pid else "created",
            metadata=metadata or {},
        )
        self.sessions[session_id] = run
        self._save()
        self.events.publish("session.registered", session_id=session_id, source="session_adapter", payload=asdict(run))
        return asdict(run)

    def refresh_session(self, agent_id: str) -> Optional[dict]:
        session_id = f"sess-{agent_id}"
        run = self.sessions.get(session_id)
        if not run:
            return None
        previous = run.status
        if run.pid:
            try:
                os.kill(run.pid, 0)
                if run.status in {"created", "running"}:
                    run.status = "running"
            except OSError:
                if previous not in {"stopped", "failed"}:
                    run.status = "completed" if previous == "running" else "exited"
        run.updated_at = datetime.now().isoformat()
        self._save()
        if previous != run.status:
            self.events.publish("session.lifecycle", session_id=session_id, source="session_adapter", payload={"previous": previous, "current": run.status, "agent_id": agent_id})
        return asdict(run)

    def update_status(self, agent_id: str, status: str, **metadata) -> Optional[dict]:
        session_id = f"sess-{agent_id}"
        run = self.sessions.get(session_id)
        if not run:
            return None
        run.status = status
        run.updated_at = datetime.now().isoformat()
        if metadata:
            run.metadata.update(metadata)
        self._save()
        self.events.publish("session.lifecycle", session_id=session_id, source="session_adapter", payload={"current": status, "agent_id": agent_id, "metadata": metadata})
        return asdict(run)

    def get_by_agent(self, agent_id: str) -> Optional[dict]:
        return self.refresh_session(agent_id)

    def list_sessions(self) -> dict:
        items = []
        lifecycle = {}
        for session_id, item in list(self.sessions.items()):
            agent_id = session_id.replace("sess-", "", 1)
            refreshed = self.refresh_session(agent_id) or asdict(item)
            items.append(refreshed)
            lifecycle[refreshed["status"]] = lifecycle.get(refreshed["status"], 0) + 1
        return {"total": len(items), "items": items, "lifecycle": lifecycle}


_GLOBAL_ADAPTER: Optional[OpenClawSessionAdapter] = None


def get_session_adapter() -> OpenClawSessionAdapter:
    global _GLOBAL_ADAPTER
    if _GLOBAL_ADAPTER is None:
        _GLOBAL_ADAPTER = OpenClawSessionAdapter()
    return _GLOBAL_ADAPTER
