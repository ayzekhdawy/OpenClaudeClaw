"""
Provider Mapping — binds logical model targets to concrete backends/models
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
PROVIDER_CONFIG_PATH = WORKSPACE / ".harness" / "providers.json"


DEFAULT_PROVIDER_CONFIG = {
    "defaults": {
        "local": {
            "provider": "ollama",
            "backend": "local-http",
            "model": "qwen2.5:14b",
            "endpoint": "http://localhost:11434",
            "max_context_tokens": 32768,
            "capabilities": ["classification", "draft", "summarization"],
        },
        "cloud": {
            "provider": "ollama-cloud",
            "backend": "cloud-api",
            "model": "qwen3.5:397b-cloud",
            "endpoint": "https://ollama.com/cloud",
            "max_context_tokens": 65536,
            "capabilities": ["reasoning", "planning", "memory-selection"],
        },
        "strong": {
            "provider": "claude-code",
            "backend": "native-runtime",
            "model": "claude-sonnet-4.5",
            "endpoint": "claude-code://runtime",
            "max_context_tokens": 200000,
            "capabilities": ["complex-coding", "architecture", "high-risk"],
        },
    },
    "routing_defaults": {
        "default_target": "cloud",
        "fallback_order": ["cloud", "strong", "local"],
    },
}


@dataclass
class ProviderTarget:
    key: str
    provider: str
    backend: str
    model: str
    endpoint: str
    max_context_tokens: int
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "provider": self.provider,
            "backend": self.backend,
            "model": self.model,
            "endpoint": self.endpoint,
            "max_context_tokens": self.max_context_tokens,
            "capabilities": self.capabilities,
        }


class ProviderRegistry:
    def __init__(self, path: Path = PROVIDER_CONFIG_PATH):
        self.path = path
        self.config = {}
        self.load()

    def load(self) -> dict:
        if self.path.exists():
            try:
                self.config = json.loads(self.path.read_text())
            except Exception:
                self.config = json.loads(json.dumps(DEFAULT_PROVIDER_CONFIG))
        else:
            self.config = json.loads(json.dumps(DEFAULT_PROVIDER_CONFIG))
            self.save()
        return self.config

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.config, indent=2))
        return self.path

    def get_target(self, key: str) -> ProviderTarget:
        defaults = self.config.get("defaults", {})
        raw = defaults.get(key) or defaults.get(self.config.get("routing_defaults", {}).get("default_target", "cloud"), {})
        return ProviderTarget(
            key=key,
            provider=raw.get("provider", "unknown"),
            backend=raw.get("backend", "unknown"),
            model=raw.get("model", "unknown"),
            endpoint=raw.get("endpoint", ""),
            max_context_tokens=int(raw.get("max_context_tokens", 0) or 0),
            capabilities=list(raw.get("capabilities", [])),
        )

    def resolve(self, logical_target: str, fallback_target: Optional[str] = None) -> dict:
        primary = self.get_target(logical_target)
        fallback = self.get_target(fallback_target) if fallback_target else None
        return {
            "logical_target": logical_target,
            "provider_target": primary.to_dict(),
            "fallback_provider_target": fallback.to_dict() if fallback else None,
            "routing_defaults": self.config.get("routing_defaults", {}),
        }

    def get_fallback_chain(self, primary: str, fallback_target: Optional[str] = None) -> list[str]:
        chain: list[str] = []
        for item in [primary, fallback_target, *self.config.get("routing_defaults", {}).get("fallback_order", [])]:
            if item and item not in chain:
                chain.append(item)
        return chain

    def status(self) -> dict:
        return {
            "config_path": str(self.path),
            "targets": {key: self.get_target(key).to_dict() for key in self.config.get("defaults", {})},
            "routing_defaults": self.config.get("routing_defaults", {}),
        }


_PROVIDER_REGISTRY: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    global _PROVIDER_REGISTRY
    if _PROVIDER_REGISTRY is None:
        _PROVIDER_REGISTRY = ProviderRegistry()
    return _PROVIDER_REGISTRY
