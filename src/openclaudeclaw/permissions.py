"""
Harness Permissions — approval-aware allow/deny surface
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
PERMISSIONS_PATH = WORKSPACE / ".harness" / "permissions.json"
APPROVALS_PATH = WORKSPACE / ".harness" / "approvals.json"


DEFAULT_RULES = {
    "mode": "allow",
    "deny_tools": [],
    "allow_tools": [],
    "readonly_only": False,
    "require_approval_for": ["Write", "Edit", "Bash", "Agent"],
    "auto_approve_readonly": True,
    "bash": {
        "deny_commands": ["rm -rf /", "shutdown", "reboot", "mkfs", "> /dev/"],
        "allow_commands": [],
    },
}


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str = ""
    matched_rule: Optional[str] = None
    state: str = "approved"
    requires_approval: bool = False
    approval_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "matched_rule": self.matched_rule,
            "state": self.state,
            "requires_approval": self.requires_approval,
            "approval_id": self.approval_id,
        }


@dataclass
class PermissionManager:
    path: Path = PERMISSIONS_PATH
    rules: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.approvals_path = APPROVALS_PATH
        self.approvals: dict[str, Any] = {}
        self.load()
        self._load_approvals()

    def load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                self.rules = {**DEFAULT_RULES, **json.loads(self.path.read_text())}
            except Exception:
                self.rules = DEFAULT_RULES.copy()
        else:
            self.rules = DEFAULT_RULES.copy()
        return self.rules

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.rules, indent=2))
        return self.path

    def _load_approvals(self) -> dict[str, Any]:
        if self.approvals_path.exists():
            try:
                self.approvals = json.loads(self.approvals_path.read_text())
            except Exception:
                self.approvals = {}
        else:
            self.approvals = {}
        return self.approvals

    def _save_approvals(self) -> Path:
        self.approvals_path.parent.mkdir(parents=True, exist_ok=True)
        self.approvals_path.write_text(json.dumps(self.approvals, indent=2))
        return self.approvals_path

    def get_rules(self) -> dict[str, Any]:
        return self.rules

    def update_rules(self, **updates) -> dict[str, Any]:
        self.rules.update(updates)
        self.save()
        return self.rules

    def request_approval(self, tool_name: str, input_data: dict | None = None, reason: str = "approval required") -> dict:
        input_data = input_data or {}
        approval_id = f"apr-{len(self.approvals) + 1}"
        payload = {
            "id": approval_id,
            "tool_name": tool_name,
            "input_data": input_data,
            "reason": reason,
            "state": "required",
        }
        self.approvals[approval_id] = payload
        self._save_approvals()
        return payload

    def resolve_approval(self, approval_id: str, approved: bool, reviewer: str = "system") -> Optional[dict]:
        payload = self.approvals.get(approval_id)
        if not payload:
            return None
        payload["state"] = "approved" if approved else "denied"
        payload["reviewer"] = reviewer
        self._save_approvals()
        return payload

    def approval_status(self, approval_id: str) -> Optional[dict]:
        return self.approvals.get(approval_id)

    def recent_approvals(self, limit: int = 10) -> list[dict]:
        return list(self.approvals.values())[-limit:]

    def check(self, tool_name: str, input_data: dict | None = None, readonly: bool = False) -> PermissionDecision:
        input_data = input_data or {}
        rules = self.rules or DEFAULT_RULES

        if rules.get("readonly_only") and not readonly:
            return PermissionDecision(False, "Readonly-only mode enabled", "readonly_only", state="denied")

        deny_tools = {t.lower() for t in rules.get("deny_tools", [])}
        allow_tools = {t.lower() for t in rules.get("allow_tools", [])}
        tool_key = tool_name.lower()

        if tool_key in deny_tools:
            return PermissionDecision(False, f"Tool denied: {tool_name}", "deny_tools", state="denied")

        if allow_tools and tool_key not in allow_tools:
            return PermissionDecision(False, f"Tool not in allowlist: {tool_name}", "allow_tools", state="denied")

        if tool_key == "bash":
            command = str(input_data.get("command", ""))
            bash_rules = rules.get("bash", {})
            for denied in bash_rules.get("deny_commands", []):
                if denied and denied in command:
                    return PermissionDecision(False, f"Command denied by rule: {denied}", "bash.deny_commands", state="denied")

            allow_commands = bash_rules.get("allow_commands", [])
            if allow_commands:
                if not any(allowed in command for allowed in allow_commands):
                    return PermissionDecision(False, "Command not in bash allowlist", "bash.allow_commands", state="denied")

        if readonly and rules.get("auto_approve_readonly", True):
            return PermissionDecision(True, "readonly auto-approved", None, state="approved")

        requested_id = input_data.get("approval_id")
        if requested_id:
            approval = self.approval_status(str(requested_id))
            if approval:
                if approval.get("state") == "approved":
                    return PermissionDecision(True, "approval granted", "approval", state="approved", approval_id=requested_id)
                if approval.get("state") == "denied":
                    return PermissionDecision(False, "approval denied", "approval", state="denied", approval_id=requested_id)

        require_approval_for = {str(t).lower() for t in rules.get("require_approval_for", [])}
        if tool_key in require_approval_for:
            approval = self.request_approval(tool_name, input_data, reason=f"{tool_name} requires approval")
            return PermissionDecision(False, approval["reason"], "require_approval_for", state="required", requires_approval=True, approval_id=approval["id"])

        return PermissionDecision(True, "allowed", None, state="approved")


_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager
