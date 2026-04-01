"""
Unified Model Routing — OpenClaw + Claude Code + Ollama fabric
──────────────────────────────────────────────────────────────
Minimum viable model router that decides which model target should
handle a task based on risk, context pressure, tool intensity, and intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelTarget:
    key: str
    provider: str
    model: str
    class_name: str
    max_context_tokens: int
    latency_tier: str
    cost_tier: str
    strengths: list[str] = field(default_factory=list)


@dataclass
class ModelRouteDecision:
    target: ModelTarget
    reason: str
    confidence: float
    task_type: str
    context_pressure: float
    fallback_target: Optional[ModelTarget] = None
    signals: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "target": self.target.__dict__,
            "reason": self.reason,
            "confidence": self.confidence,
            "task_type": self.task_type,
            "context_pressure": round(self.context_pressure, 4),
            "fallback_target": self.fallback_target.__dict__ if self.fallback_target else None,
            "signals": self.signals,
        }


class ModelRouter:
    """Simple but real routing fabric for local/cloud/strong-model targets."""

    def __init__(self):
        self.targets = {
            "local": ModelTarget(
                key="local",
                provider="ollama",
                model="qwen2.5:14b",
                class_name="local",
                max_context_tokens=32768,
                latency_tier="fast",
                cost_tier="low",
                strengths=["classification", "light-summarization", "drafting"],
            ),
            "cloud": ModelTarget(
                key="cloud",
                provider="ollama-cloud",
                model="minimax-m2.7:cloud",
                class_name="cloud",
                max_context_tokens=65536,
                latency_tier="balanced",
                cost_tier="medium",
                strengths=["general-reasoning", "memory-selection", "tool-planning"],
            ),
            "strong": ModelTarget(
                key="strong",
                provider="claude-code",
                model="claude-sonnet-4.5",
                class_name="strong",
                max_context_tokens=200000,
                latency_tier="slower",
                cost_tier="high",
                strengths=["complex-coding", "architecture", "high-risk-reasoning"],
            ),
        }

    def route(
        self,
        task: str,
        *,
        token_count: int = 0,
        tool_candidates: Optional[list[str]] = None,
        risk: str = "low",
        route_hint: Optional[str] = None,
    ) -> ModelRouteDecision:
        tool_candidates = tool_candidates or []
        task_lower = (task or "").lower()
        context_pressure = min(1.0, token_count / self.targets["strong"].max_context_tokens) if token_count else 0.0

        signals = {
            "token_count": token_count,
            "tool_candidates": tool_candidates,
            "risk": risk,
            "route_hint": route_hint,
        }

        heavy_code = any(word in task_lower for word in [
            "refactor", "mimari", "architecture", "runtime", "debug", "agent", "subagent", "integration", "kod", "script",
        ])
        simple_lookup = any(word in task_lower for word in [
            "summarize", "özet", "classify", "etiketle", "draft", "taslak",
        ])
        destructive = any(word in task_lower for word in ["delete", "drop", "kill", "remove", "sil"])
        tool_heavy = any(tool in tool_candidates for tool in ["Bash", "Edit", "Write", "Agent", "MCP", "Task"])

        if risk == "high" or destructive or (heavy_code and tool_heavy):
            return ModelRouteDecision(
                target=self.targets["strong"],
                fallback_target=self.targets["cloud"],
                reason="High-risk or architecture/coding-heavy task routed to strongest cognition tier.",
                confidence=0.9,
                task_type="complex-coding",
                context_pressure=context_pressure,
                signals=signals,
            )

        if context_pressure > 0.55 or route_hint in {"research", "searxng", "code"} or heavy_code:
            return ModelRouteDecision(
                target=self.targets["cloud"],
                fallback_target=self.targets["local"],
                reason="Task needs broader reasoning or elevated context without paying strongest tier by default.",
                confidence=0.78,
                task_type="extended-reasoning",
                context_pressure=context_pressure,
                signals=signals,
            )

        if simple_lookup and not tool_heavy:
            return ModelRouteDecision(
                target=self.targets["local"],
                fallback_target=self.targets["cloud"],
                reason="Low-risk lightweight task fits local/cheap inference.",
                confidence=0.82,
                task_type="lightweight",
                context_pressure=context_pressure,
                signals=signals,
            )

        return ModelRouteDecision(
            target=self.targets["cloud"],
            fallback_target=self.targets["strong"],
            reason="Default balanced routing for general tasks.",
            confidence=0.68,
            task_type="general",
            context_pressure=context_pressure,
            signals=signals,
        )


_GLOBAL_ROUTER: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    global _GLOBAL_ROUTER
    if _GLOBAL_ROUTER is None:
        _GLOBAL_ROUTER = ModelRouter()
    return _GLOBAL_ROUTER
