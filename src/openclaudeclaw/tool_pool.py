"""
Tool Pool — Tool registration and execution
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

from .agent_registry import get_agent_registry
from .event_bus import get_event_bus
from .mcp_pool import get_mcp_pool
from .models import ToolCategory, ToolResult, ToolSpec
from .policy_engine import get_policy_engine
from .permissions import get_permission_manager
from .schedule import get_schedule_store
from .skills import get_skill_registry
from .unified_runtime import get_unified_runtime
from .tool_prompts import (
    BASH_PROMPT,
    FILE_EDIT_PROMPT,
    FILE_READ_PROMPT,
    FILE_WRITE_PROMPT,
    GLOB_PROMPT,
    GREP_PROMPT,
    TASK_ISHACK_PROMPT,
    THINK_PROMPT,
)

# Standalone tool modules
from .task_output_tool import TaskOutputTool
from .web_search_tool import WebSearchTool
from .tools import (
    TodoWriteTool, WebFetchTool, BriefTool, SendMessageTool,
    TaskCreateTool, TaskGetTool, TaskUpdateTool, TaskStopTool,
    AskUserQuestionTool, ToolSearchTool, SleepTool, ConfigTool,
    EnterPlanModeTool, ExitPlanModeTool, NotebookEditTool,
    ListMcpResourcesTool, ReadMcpResourceTool, SyntheticOutputTool,
    LSPTool, REPLTool,
    EnterWorktreeTool, ExitWorktreeTool, WorktreeListTool,
    UpdatePlanTool, PlanStatusTool,
    AnswerQuestionTool,
)

# BaseTool from models (single source of truth)
from .models import BaseTool


class BashTool(BaseTool):
    name = "Bash"
    description = BASH_PROMPT
    category = ToolCategory.EXECUTE
    patterns = ["bash", "shell", "terminal", "command", "çalıştır"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        command = input_data.get("command", "")
        cwd = input_data.get("cwd", "/home/ayzek/.openclaw/workspace")
        timeout = input_data.get("timeout", 30)
        start = time.time()
        try:
            result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            return ToolResult(
                tool_name=self.name,
                success=result.returncode == 0,
                output=result.stdout[:5000],
                error=result.stderr[:1000] if result.returncode != 0 else None,
                duration_ms=int((time.time() - start) * 1000),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(self.name, False, "", f"Command timed out after {timeout}s", int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class ReadTool(BaseTool):
    name = "Read"
    description = FILE_READ_PROMPT
    category = ToolCategory.READ
    patterns = ["read", "okuma", "dosya", "içerik"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        file_path = input_data.get("path", "")
        offset = input_data.get("offset", 0)
        limit = input_data.get("limit")
        start = time.time()
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(self.name, False, "", f"File not found: {file_path}", int((time.time() - start) * 1000))
            content = path.read_text()
            lines = content.splitlines()
            if offset:
                lines = lines[offset:]
            if limit:
                lines = lines[:limit]
            return ToolResult(self.name, True, "\n".join(lines)[:10000], duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class WriteTool(BaseTool):
    name = "Write"
    description = FILE_WRITE_PROMPT
    category = ToolCategory.WRITE
    patterns = ["write", "yaz", "kaydet", "oluştur"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        file_path = input_data.get("path", "")
        content = input_data.get("content", "")
        append = input_data.get("append", False)
        start = time.time()
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if append and path.exists():
                path.write_text(path.read_text() + content)
            else:
                path.write_text(content)
            return ToolResult(self.name, True, f"Written to {file_path}", duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class EditTool(BaseTool):
    name = "Edit"
    description = FILE_EDIT_PROMPT
    category = ToolCategory.EDIT
    patterns = ["edit", "düzelt", "değiştir", "düzenle"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        file_path = input_data.get("path", "")
        old_text = input_data.get("oldText", "")
        new_text = input_data.get("newText", "")
        start = time.time()
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(self.name, False, "", f"File not found: {file_path}", int((time.time() - start) * 1000))
            content = path.read_text()
            if old_text not in content:
                return ToolResult(self.name, False, "", f"Text not found in file: {old_text[:80]}", int((time.time() - start) * 1000))
            path.write_text(content.replace(old_text, new_text))
            return ToolResult(self.name, True, f"Edited {file_path}", duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class GlobTool(BaseTool):
    name = "Glob"
    description = GLOB_PROMPT
    category = ToolCategory.SEARCH
    patterns = ["glob", "find", "bul", "ara", "dosya"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        pattern = input_data.get("pattern", "**/*")
        cwd = input_data.get("cwd", "/home/ayzek/.openclaw/workspace")
        start = time.time()
        try:
            files = [str(f) for f in Path(cwd).glob(pattern)][:100]
            return ToolResult(self.name, True, json.dumps(files, indent=2), duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class GrepTool(BaseTool):
    name = "Grep"
    description = GREP_PROMPT
    category = ToolCategory.SEARCH
    patterns = ["grep", "search", "içinde ara"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        pattern = input_data.get("pattern", "")
        cwd = input_data.get("cwd", "/home/ayzek/.openclaw/workspace")
        start = time.time()
        try:
            result = subprocess.run(f"grep -rn '{pattern}' {cwd} 2>/dev/null | head -50", shell=True, capture_output=True, text=True)
            return ToolResult(self.name, True, result.stdout or "No matches found", duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class ThinkTool(BaseTool):
    name = "Think"
    description = THINK_PROMPT
    category = ToolCategory.NATURAL
    patterns = ["think", "düşün", "analiz"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        return ToolResult(self.name, True, f"Thinking: {input_data.get('thought', '')}")


class TaskTool(BaseTool):
    name = "Task"
    description = TASK_ISHACK_PROMPT
    category = ToolCategory.EXECUTE
    patterns = ["task", "görev", "todo", "yapılacak"]

    def __init__(self):
        super().__init__()
        self._pool = None

    @property
    def pool(self):
        if self._pool is None:
            from src.harness.task_pool import get_task_pool
            self._pool = get_task_pool()
        return self._pool

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        action = input_data.get("action", "")
        start = time.time()
        try:
            if action == "create":
                result = self.pool.task_create(
                    name=input_data.get("name", ""),
                    description=input_data.get("description", ""),
                    priority=input_data.get("priority", "NORMAL"),
                    assigned_to=input_data.get("assigned_to"),
                    tags=input_data.get("tags"),
                )
            elif action == "list":
                result = self.pool.task_list(status=input_data.get("status"), assigned_to=input_data.get("assigned_to"), limit=input_data.get("limit", 10))
            elif action == "get":
                result = self.pool.task_get(input_data.get("task_id", ""))
                if result is None:
                    return ToolResult(self.name, False, "", f"Task not found: {input_data.get('task_id')}", int((time.time() - start) * 1000))
            elif action == "update":
                result = self.pool.task_update(
                    task_id=input_data.get("task_id", ""),
                    status=input_data.get("status"),
                    result=input_data.get("result"),
                    assigned_to=input_data.get("assigned_to"),
                    priority=input_data.get("priority"),
                    due_at=input_data.get("due_at"),
                    tags=input_data.get("tags"),
                )
            elif action in {"stop", "cancel"}:
                result = self.pool.task_update(task_id=input_data.get("task_id", ""), status="cancelled", result=input_data.get("result"))
            elif action == "delete":
                result = self.pool.task_delete(input_data.get("task_id", ""))
            elif action == "stats":
                result = self.pool.task_stats()
            else:
                return ToolResult(self.name, False, "", "Unknown action: create, list, get, update, stop, cancel, delete, stats", int((time.time() - start) * 1000))
            if isinstance(result, dict) and "error" in result:
                return ToolResult(self.name, False, "", result["error"], int((time.time() - start) * 1000))
            return ToolResult(self.name, True, json.dumps(result, indent=2), duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time() - start) * 1000))


class MCPTool(BaseTool):
    name = "MCP"
    description = "MCP server/tool/resource surface: list servers, list tools, list resources, call tool."
    category = ToolCategory.EXECUTE
    patterns = ["mcp", "server", "resource"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        pool = get_mcp_pool()
        action = input_data.get("action", "list_tools")
        start = time.time()
        if action == "list_servers":
            result = pool.list_servers()
        elif action == "list_tools":
            result = pool.list_tools(input_data.get("server_name"))
        elif action == "list_resources":
            result = pool.list_resources(input_data.get("server_name"))
        elif action == "call":
            result = pool.call_tool(input_data.get("name", ""), input_data.get("arguments", {}))
        else:
            return ToolResult(self.name, False, "", f"Unknown MCP action: {action}", int((time.time() - start) * 1000))
        return ToolResult(self.name, True, json.dumps(result, indent=2), duration_ms=int((time.time() - start) * 1000))


class ScheduleCronTool(BaseTool):
    name = "Schedule"
    description = "Create/list/get/update/stop cron-like scheduled tasks using a JSON-backed surface."
    category = ToolCategory.EXECUTE
    patterns = ["cron", "schedule", "zamanla", "tekrarla"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        store = get_schedule_store()
        action = input_data.get("action", "list")
        start = time.time()
        if action == "create":
            result = store.create(input_data.get("name", ""), input_data.get("cron", ""), input_data.get("command", ""), input_data.get("description", ""))
        elif action == "list":
            enabled = input_data.get("enabled")
            result = store.list(enabled)
        elif action == "get":
            result = store.get(input_data.get("schedule_id", "")) or {"error": "Schedule not found"}
        elif action == "update":
            result = store.update(input_data.get("schedule_id", ""), cron=input_data.get("cron"), command=input_data.get("command"), name=input_data.get("name"), description=input_data.get("description"), enabled=input_data.get("enabled"))
        elif action == "stop":
            result = store.stop(input_data.get("schedule_id", ""))
        else:
            result = {"error": f"Unknown schedule action: {action}"}
        success = "error" not in result
        return ToolResult(self.name, success, json.dumps(result, indent=2) if success else "", result.get("error") if not success else None, int((time.time() - start) * 1000))


class AgentTool(BaseTool):
    name = "Agent"
    description = "Spawn/list/get/stop background sub-agent compatible runs."
    category = ToolCategory.AGENT
    patterns = ["agent", "sub-agent", "spawn"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        registry = get_agent_registry()
        action = input_data.get("action", "list")
        start = time.time()
        if action == "spawn":
            result = registry.spawn(prompt=input_data.get("prompt", ""), name=input_data.get("name", "subagent"), command=input_data.get("command"), cwd=input_data.get("cwd", "/home/ayzek/.openclaw/workspace"))
        elif action == "list":
            result = registry.list()
        elif action == "get":
            result = registry.get(input_data.get("agent_id", "")) or {"error": "Agent not found"}
        elif action == "stop":
            result = registry.stop(input_data.get("agent_id", ""))
        else:
            result = {"error": f"Unknown agent action: {action}"}
        success = "error" not in result
        return ToolResult(self.name, success, json.dumps(result, indent=2) if success else "", result.get("error") if not success else None, int((time.time() - start) * 1000))


class AnalyzeContextTool(BaseTool):
    name = "AnalyzeContext"
    description = "Explain workspace/task context, tool suggestions, memory summary, and risk level."
    category = ToolCategory.NATURAL
    patterns = ["analyzecontext", "context", "visibility"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        from .context_builder import analyze_context
        start = time.time()
        result = analyze_context(input_data.get("task", ""))
        return ToolResult(self.name, True, json.dumps(result, indent=2), duration_ms=int((time.time() - start) * 1000))


class SkillTool(BaseTool):
    name = "Skill"
    description = "Discover and load local skill definitions from workspace/skills."
    category = ToolCategory.READ
    patterns = ["skill", "skills", "yükle"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        registry = get_skill_registry()
        action = input_data.get("action", "discover")
        start = time.time()
        if action == "discover":
            result = registry.discover()
        elif action == "load":
            result = registry.load(input_data.get("name", "")) or {"error": "Skill not found"}
        else:
            result = {"error": f"Unknown skill action: {action}"}
        success = "error" not in result
        return ToolResult(self.name, success, json.dumps(result, indent=2) if success else "", result.get("error") if not success else None, int((time.time() - start) * 1000))


class RuntimeTool(BaseTool):
    name = "Runtime"
    description = "Unified runtime status/diagnostics/model routing visibility surface."
    category = ToolCategory.NATURAL
    patterns = ["runtime", "diagnostics", "status", "model", "visibility"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        session_id = input_data.get("session_id", "default")
        task = input_data.get("task", "")
        token_count = input_data.get("token_count", 0)
        start = time.time()
        runtime = get_unified_runtime(session_id)
        result = runtime.diagnostics(task, token_count=token_count)
        return ToolResult(self.name, True, json.dumps(result.to_dict(), indent=2), duration_ms=int((time.time() - start) * 1000))


class ToolPool:
    def __init__(self):
        self.tools: dict[str, BaseTool] = {}
        self.permissions = get_permission_manager()
        self.policy = get_policy_engine()
        self.events = get_event_bus()
        self._register_builtins()

    def _register_builtins(self):
        for tool in [
            BashTool(), ReadTool(), WriteTool(), EditTool(), GlobTool(), GrepTool(), ThinkTool(),
            TaskTool(), MCPTool(), ScheduleCronTool(), AgentTool(), AnalyzeContextTool(), SkillTool(), RuntimeTool(),
            TaskOutputTool(), WebSearchTool(),
            TodoWriteTool(), WebFetchTool(), BriefTool(), SendMessageTool(),
            TaskCreateTool(), TaskGetTool(), TaskUpdateTool(), TaskStopTool(),
            AskUserQuestionTool(), ToolSearchTool(), SleepTool(), ConfigTool(),
            EnterPlanModeTool(), ExitPlanModeTool(), NotebookEditTool(),
            ListMcpResourcesTool(), ReadMcpResourceTool(), SyntheticOutputTool(),
            # New tools (2026-04-01)
            LSPTool(), REPLTool(),
            EnterWorktreeTool(), ExitWorktreeTool(), WorktreeListTool(),
            UpdatePlanTool(), PlanStatusTool(),
            AnswerQuestionTool(),
        ]:
            self.register(tool)

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def execute(self, tool_name: str, input_data: dict, context: dict | None = None) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(tool_name, False, "", f"Tool not found: {tool_name}")
        
        # Tool-heavy tasks → deepseek-v3.1:671b-cloud
        tool_heavy = ["LSP", "AnalyzeContext", "Skill", "WebSearch", "Grep", "Glob"]
        if tool_name in tool_heavy:
            input_data["model_override"] = "deepseek-v3.1:671b-cloud"
        session_context = context or {}
        session_id = str(input_data.get("session_id") or session_context.get("session_id") or "default")
        task = str(input_data.get("task") or input_data.get("thought") or input_data.get("command") or input_data.get("path") or tool_name)
        policy = self.policy.evaluate(
            task=task,
            tool_name=tool_name,
            input_data=input_data,
            readonly=tool.readonly,
            token_count=int(input_data.get("token_count", 0) or 0),
        )
        self.events.publish("tool.policy_evaluated", session_id=session_id, source="tool_pool", payload={"tool": tool_name, "policy": policy.to_dict()})
        if not policy.permission.get("allowed", True):
            state = policy.permission.get("state")
            self.events.publish("tool.blocked", session_id=session_id, source="tool_pool", payload={"tool": tool_name, "permission": policy.permission})
            return ToolResult(tool_name, False, "", policy.permission.get("reason", "permission denied"), approval_state=state, metadata={"permission": policy.permission})
        self.events.publish("tool.started", session_id=session_id, source="tool_pool", payload={"tool": tool_name})
        result = tool.execute(input_data, context)
        result.approval_state = result.approval_state or policy.permission.get("state")
        result.metadata.setdefault("permission", policy.permission)
        self.events.publish("tool.completed", session_id=session_id, source="tool_pool", payload={"tool": tool_name, "success": result.success, "approval_state": result.approval_state})
        return result

    def list_tools(self) -> list[ToolSpec]:
        return [tool.spec for tool in self.tools.values()]

    def search(self, query: str) -> list[ToolSpec]:
        query = query.lower()
        results = []
        for tool in self.tools.values():
            if query in tool.name.lower() or any(query in p.lower() for p in tool.patterns):
                results.append(tool.spec)
        return results


_GLOBAL_POOL: Optional[ToolPool] = None


def get_tool_pool() -> ToolPool:
    global _GLOBAL_POOL
    if _GLOBAL_POOL is None:
        _GLOBAL_POOL = ToolPool()
    return _GLOBAL_POOL


def register_tool(tool: BaseTool):
    get_tool_pool().register(tool)


def get_tool(name: str) -> Optional[BaseTool]:
    return get_tool_pool().get(name)
