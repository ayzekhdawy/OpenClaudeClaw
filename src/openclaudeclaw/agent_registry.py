"""
Harness Agent registry — minimum viable sub-agent/background process surface
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .session_adapter import get_session_adapter

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
REGISTRY_PATH = WORKSPACE / "memory" / "agents.json"


@dataclass
class AgentRun:
    id: str
    name: str
    prompt: str
    command: str
    cwd: str
    pid: Optional[int] = None
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentRegistry:
    def __init__(self, path: Path = REGISTRY_PATH):
        self.path = path
        self.runs: dict[str, AgentRun] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.runs = {k: AgentRun(**v) for k, v in data.items()}
            except Exception:
                self.runs = {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: asdict(v) for k, v in self.runs.items()}, indent=2))

    def spawn(self, prompt: str, name: str = "subagent", command: Optional[str] = None, cwd: str = str(WORKSPACE)) -> dict:
        agent_id = str(uuid.uuid4())[:8]
        command = command or f"python3 -m src.harness.cli run {json.dumps(prompt)}"
        proc = subprocess.Popen(command, shell=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run = AgentRun(id=agent_id, name=name, prompt=prompt, command=command, cwd=cwd, pid=proc.pid, status="running")
        self.runs[agent_id] = run
        get_session_adapter().register_run(
            agent_id=agent_id,
            prompt=prompt,
            command=command,
            cwd=cwd,
            pid=proc.pid,
            title=name,
            metadata={"registry": "local", "surface": "adapter"},
        )
        self._save()
        return {"status": "running", **asdict(run)}

    def _refresh(self, run: AgentRun):
        if not run.pid:
            return
        try:
            os.kill(run.pid, 0)
            run.status = "running"
            get_session_adapter().update_status(run.id, "running", pid=run.pid, cwd=run.cwd)
        except OSError:
            if run.status == "running":
                run.status = "completed"
                get_session_adapter().update_status(run.id, "completed")
        run.updated_at = datetime.now().isoformat()

    def list(self) -> dict:
        for run in self.runs.values():
            self._refresh(run)
        self._save()
        return {"total": len(self.runs), "items": [asdict(x) for x in self.runs.values()]}

    def get(self, agent_id: str) -> Optional[dict]:
        run = self.runs.get(agent_id)
        if not run:
            return None
        self._refresh(run)
        self._save()
        return asdict(run)

    def stop(self, agent_id: str) -> dict:
        run = self.runs.get(agent_id)
        if not run:
            return {"error": f"Agent not found: {agent_id}"}
        if run.pid:
            try:
                os.kill(run.pid, signal.SIGTERM)
            except OSError:
                pass
        run.status = "stopped"
        run.updated_at = datetime.now().isoformat()
        get_session_adapter().update_status(run.id, "stopped")
        self._save()
        return {"status": "stopped", **asdict(run)}


_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
