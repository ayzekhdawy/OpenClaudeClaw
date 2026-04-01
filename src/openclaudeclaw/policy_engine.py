"""
Unified Policy Engine — single decision surface for tool/model/permission/risk
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .context_builder import analyze_context
from .model_routing import get_model_router
from .permissions import get_permission_manager
from .providers import get_provider_registry


@dataclass
class UnifiedPolicyDecision:
    task: str
    tool_name: Optional[str] = None
    readonly: bool = False
    risk_summary: dict = field(default_factory=dict)
    permission: dict = field(default_factory=dict)
    model: Optional[dict] = None
    provider_mapping: Optional[dict] = None
    context_pressure: float = 0.0
    route_hint: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "tool_name": self.tool_name,
            "readonly": self.readonly,
            "risk_summary": self.risk_summary,
            "permission": self.permission,
            "model": self.model,
            "provider_mapping": self.provider_mapping,
            "context_pressure": round(self.context_pressure, 4),
            "route_hint": self.route_hint,
        }


class UnifiedPolicyEngine:
    def __init__(self):
        self.router = get_model_router()
        self.permissions = get_permission_manager()
        self.providers = get_provider_registry()

    def evaluate(
        self,
        *,
        task: str = "",
        tool_name: Optional[str] = None,
        input_data: Optional[dict] = None,
        readonly: bool = False,
        token_count: int = 0,
        route_hint: Optional[str] = None,
    ) -> UnifiedPolicyDecision:
        input_data = input_data or {}
        analysis = analyze_context(task) if task else {"risk": "low", "tool_suggestions": []}
        risk = analysis.get("risk", "low")
        risk_summary = {
            "level": risk,
            "workspace_summary": analysis.get("workspace_summary", ""),
            "tool_suggestions": analysis.get("tool_suggestions", []),
            "relevant_memories": analysis.get("relevant_memories", []),
        }

        permission_decision = None
        permission_payload = {
            "allowed": True,
            "reason": "not-applicable",
            "matched_rule": None,
        }
        if tool_name:
            permission_decision = self.permissions.check(tool_name, input_data, readonly=readonly)
            permission_payload = {
                "allowed": permission_decision.allowed,
                "reason": permission_decision.reason,
                "matched_rule": permission_decision.matched_rule,
                "state": permission_decision.state,
                "requires_approval": permission_decision.requires_approval,
                "approval_id": permission_decision.approval_id,
            }

        route = self.router.route(
            task,
            token_count=token_count,
            tool_candidates=analysis.get("tool_suggestions", []),
            risk=risk,
            route_hint=route_hint,
        )
        mapping = self.providers.resolve(
            route.target.key,
            route.fallback_target.key if route.fallback_target else None,
        )

        return UnifiedPolicyDecision(
            task=task,
            tool_name=tool_name,
            readonly=readonly,
            risk_summary=risk_summary,
            permission=permission_payload,
            model=route.to_dict(),
            provider_mapping=mapping,
            context_pressure=route.context_pressure,
            route_hint=route_hint,
        )


_POLICY_ENGINE: Optional[UnifiedPolicyEngine] = None


def get_policy_engine() -> UnifiedPolicyEngine:
    global _POLICY_ENGINE
    if _POLICY_ENGINE is None:
        _POLICY_ENGINE = UnifiedPolicyEngine()
    return _POLICY_ENGINE
