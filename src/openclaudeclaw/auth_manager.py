"""
Auth Manager — credential storage, header injection, API key routing for provider backends.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
AUTH_CONFIG_PATH = WORKSPACE / ".harness" / "auth.json"


DEFAULT_AUTH_CONFIG = {
    "providers": {},
    "envInterpolation": True,
}


@dataclass
class ProviderAuth:
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    custom_headers: dict = field(default_factory=dict)
    env_vars: dict = field(default_factory=dict)
    auth_type: str = "none"

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "bearer_token": self.bearer_token,
            "custom_headers": self.custom_headers,
            "env_vars": self.env_vars,
            "auth_type": self.auth_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderAuth":
        return cls(
            api_key=data.get("api_key"),
            bearer_token=data.get("bearer_token"),
            custom_headers=data.get("custom_headers", {}),
            env_vars=data.get("env_vars", {}),
            auth_type=data.get("auth_type", "none"),
        )

    def build_headers(self) -> dict:
        headers = {}
        for k, v in self.custom_headers.items():
            headers[str(k)] = str(v)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        return headers


class AuthManager:
    def __init__(self, path: Path = AUTH_CONFIG_PATH):
        self.path = path
        self.config = {}
        self.load()

    def load(self) -> dict:
        if self.path.exists():
            try:
                self.config = json.loads(self.path.read_text())
            except Exception:
                self.config = {"providers": {}}
        else:
            self.config = {"providers": {}}
        return self.config

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.config, indent=2))
        return self.path

    def get_auth(self, provider_name: str) -> ProviderAuth:
        raw = self.config.get("providers", {}).get(provider_name, {})
        return ProviderAuth.from_dict(raw)

    def set_auth(self, provider_name: str, auth: ProviderAuth) -> None:
        if "providers" not in self.config:
            self.config["providers"] = {}
        self.config["providers"][provider_name] = auth.to_dict()
        self.save()

    def set_api_key(self, provider_name: str, api_key: str, auth_type: str = "bearer") -> None:
        auth = ProviderAuth(api_key=api_key, auth_type=auth_type)
        self.set_auth(provider_name, auth)

    def set_bearer_token(self, provider_name: str, token: str) -> None:
        auth = ProviderAuth(bearer_token=token, auth_type="bearer")
        self.set_auth(provider_name, auth)

    def set_custom_header(self, provider_name: str, header_key: str, header_value: str) -> None:
        auth = self.get_auth(provider_name)
        auth.custom_headers[header_key] = self._interpolate(header_value)
        self.set_auth(provider_name, auth)

    def _interpolate(self, value: str) -> str:
        if not self.config.get("envInterpolation", True):
            return value
        pattern = re.compile(r"\$\{(\w+)\}|\$(\w+)")
        def replacer(m):
            env_name = m.group(1) or m.group(2)
            return os.environ.get(env_name, m.group(0))
        return pattern.sub(replacer, value)

    def resolve_auth_headers(self, provider_name: str) -> dict:
        auth = self.get_auth(provider_name)
        return auth.build_headers()

    def status(self) -> dict:
        providers = list(self.config.get("providers", {}).keys())
        return {
            "auth_config_path": str(self.path),
            "configured_providers": providers,
            "provider_count": len(providers),
        }


_AUTH_MANAGER: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    global _AUTH_MANAGER
    if _AUTH_MANAGER is None:
        _AUTH_MANAGER = AuthManager()
    return _AUTH_MANAGER
