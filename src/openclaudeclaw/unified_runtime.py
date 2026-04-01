"""
Unified Runtime — OpenClaw platform bus + Claude Code cognition + Ollama routing
────────────────────────────────────────────────────────────────────────────────
This layer sits above the existing HarnessRuntime and provides:
- unified diagnostics / status
- model routing decisions
- memory fabric selection
- platform session adapter visibility
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .context_builder import analyze_context
from .event_bus import get_event_bus
from .executor import ExecutionRequest, ExecutionResult, UnifiedExecutor, get_unified_executor
from .memory_fabric import get_memory_fabric, MemoryFabric
from .model_routing import get_model_router, ModelRouteDecision, ModelRouter
from .policy_engine import get_policy_engine, UnifiedPolicyEngine
from .providers import get_provider_registry, ProviderRegistry
from .session_adapter import get_session_adapter, OpenClawSessionAdapter


@dataclass
class UnifiedDiagnostics:
    session_id: str
    context_pressure: float = 0.0
    model_decision: Optional[dict] = None
    provider_mapping: Optional[dict] = None
    permission_outcome: Optional[dict] = None
    risk_summary: Optional[dict] = None
    surfaced_memory: Optional[dict] = None
    platform_sessions: Optional[dict] = None
    session_lifecycle: Optional[dict] = None
    recent_events: Optional[dict] = None
    executor_status: Optional[dict] = None
    approval_state: Optional[dict] = None
    analyze_context: Optional[dict] = None
    recent_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "context_pressure": round(self.context_pressure, 4),
            "model_decision": self.model_decision,
            "provider_mapping": self.provider_mapping,
            "permission_outcome": self.permission_outcome,
            "risk_summary": self.risk_summary,
            "surfaced_memory": self.surfaced_memory,
            "platform_sessions": self.platform_sessions,
            "session_lifecycle": self.session_lifecycle,
            "recent_events": self.recent_events,
            "executor_status": self.executor_status,
            "approval_state": self.approval_state,
            "analyze_context": self.analyze_context,
            "recent_tools": self.recent_tools,
        }


class UnifiedRuntime:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.router: ModelRouter = get_model_router()
        self.memory_fabric: MemoryFabric = get_memory_fabric(session_id)
        self.session_adapter: OpenClawSessionAdapter = get_session_adapter()
        self.providers: ProviderRegistry = get_provider_registry()
        self.policy: UnifiedPolicyEngine = get_policy_engine()
        self.executor: UnifiedExecutor = get_unified_executor()
        self.events = get_event_bus()
        self.last_decision: Optional[ModelRouteDecision] = None
        self.last_policy: Optional[dict] = None
        self.last_execution: Optional[dict] = None

    def execute(self, task: str, *, prompt: Optional[str] = None, token_count: int = 0, route_hint: Optional[str] = None) -> ExecutionResult:
        decision = self.decide_model(task, token_count=token_count, route_hint=route_hint)
        request = ExecutionRequest(
            session_id=self.session_id,
            task=task,
            prompt=prompt or task,
            target=decision.target.key,
            fallback_target=decision.fallback_target.key if decision.fallback_target else None,
            metadata={"route_hint": route_hint},
        )
        result = self.executor.execute(request)
        self.last_execution = result.to_dict()
        return result

    def decide_model(self, task: str, *, token_count: int = 0, tool_candidates: Optional[list[str]] = None, risk: str = "low", route_hint: Optional[str] = None) -> ModelRouteDecision:
        policy = self.policy.evaluate(
            task=task,
            token_count=token_count,
            route_hint=route_hint,
        )
        self.last_policy = policy.to_dict()
        routed = policy.model or {}
        target = routed.get("target") or {}
        fallback = routed.get("fallback_target")
        self.last_decision = self.router.route(
            task,
            token_count=token_count,
            tool_candidates=tool_candidates or policy.risk_summary.get("tool_suggestions", []),
            risk=risk or policy.risk_summary.get("level", "low"),
            route_hint=route_hint,
        )
        return self.last_decision

    def build_memory_context(self, task: str) -> str:
        return self.memory_fabric.build_context(task)

    def diagnostics(self, task: str = "", *, token_count: int = 0, recent_tools: Optional[list[str]] = None) -> UnifiedDiagnostics:
        analyze = analyze_context(task) if task else None
        policy = self.policy.evaluate(task=task, token_count=token_count) if task else None
        if policy:
            self.last_policy = policy.to_dict()
        decision = self.decide_model(task, token_count=token_count) if task else self.last_decision
        context_pressure = (policy.context_pressure if policy else (decision.context_pressure if decision else 0.0))
        platform_sessions = self.session_adapter.list_sessions()
        recent_events = self.events.summary(session_id=self.session_id, limit=20)

        return UnifiedDiagnostics(
            session_id=self.session_id,
            context_pressure=context_pressure,
            model_decision=decision.to_dict() if decision else None,
            provider_mapping=(policy.provider_mapping if policy else (self.last_policy or {}).get("provider_mapping")),
            permission_outcome=(policy.permission if policy else (self.last_policy or {}).get("permission")),
            risk_summary=(policy.risk_summary if policy else (self.last_policy or {}).get("risk_summary")),
            surfaced_memory=self.memory_fabric.diagnostics(),
            platform_sessions=platform_sessions,
            session_lifecycle=platform_sessions.get("lifecycle"),
            recent_events=recent_events,
            executor_status=self.last_execution,
            approval_state=(policy.permission if policy else (self.last_policy or {}).get("permission")),
            analyze_context=analyze,
            recent_tools=recent_tools or [],
        )


_UNIFIED_RUNTIMES: dict[str, UnifiedRuntime] = {}


def get_unified_runtime(session_id: str) -> UnifiedRuntime:
    if session_id not in _UNIFIED_RUNTIMES:
        _UNIFIED_RUNTIMES[session_id] = UnifiedRuntime(session_id)
    return _UNIFIED_RUNTIMES[session_id]
