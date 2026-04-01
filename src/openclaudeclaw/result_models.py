"""
Structured Result Models — standardized output schema for executor and tool results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ExecutorResult:
    ok: bool
    session_id: str
    requested_target: str
    executor_target: str
    provider: str
    model: str
    backend: str
    output: str
    error: Optional[str] = None
    duration_ms: int = 0
    tokens_used: Optional[int] = None
    tokens_cached: Optional[int] = None
    cost_estimate: Optional[float] = None
    latency_ms: Optional[int] = None
    fallback_used: bool = False
    attempts: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "session_id": self.session_id,
            "requested_target": self.requested_target,
            "executor_target": self.executor_target,
            "provider": self.provider,
            "model": self.model,
            "backend": self.backend,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "tokens_cached": self.tokens_cached,
            "cost_estimate": self.cost_estimate,
            "latency_ms": self.latency_ms,
            "fallback_used": self.fallback_used,
            "attempts": self.attempts,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @property
    def success(self) -> bool:
        return self.ok

    @property
    def structured_output(self) -> dict:
        return {
            "text": self.output,
            "tokens": self.tokens_used,
            "latency_ms": self.latency_ms,
            "cost": self.cost_estimate,
            "model": self.model,
            "provider": self.provider,
        }


@dataclass
class ToolResult:
    ok: bool
    name: str
    output: Any = ""
    error: Optional[str] = None
    duration_ms: int = 0
    approval_state: Optional[str] = None
    approval_id: Optional[str] = None
    policy_decision: Optional[dict] = None
    blocked: bool = False
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "name": self.name,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "approval_state": self.approval_state,
            "approval_id": self.approval_id,
            "policy_decision": self.policy_decision,
            "blocked": self.blocked,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @property
    def success(self) -> bool:
        return self.ok and not self.blocked


@dataclass
class DiagnosticsSnapshot:
    context_pressure: float
    model_decision: str
    provider_target: str
    permission_state: str
    session_lifecycle: str
    executor_status: str
    approval_pending: int
    recent_event_count: int
    active_sessions: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "context_pressure": self.context_pressure,
            "model_decision": self.model_decision,
            "provider_target": self.provider_target,
            "permission_state": self.permission_state,
            "session_lifecycle": self.session_lifecycle,
            "executor_status": self.executor_status,
            "approval_pending": self.approval_pending,
            "recent_event_count": self.recent_event_count,
            "active_sessions": self.active_sessions,
            "timestamp": self.timestamp,
        }


# Backward compatibility alias
class ExecutionResult(ExecutorResult):
    pass
