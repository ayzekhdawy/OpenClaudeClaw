"""
Core Tools — Bash, Read, Write, Edit, Glob, Grep, Think, Task, MCP, Schedule, Agent, Runtime, AnalyzeContext, WebSearch
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Harness'ın çekirdek tool'ları.
"""

import os
import re
import time
import json
import subprocess
import glob as glob_module
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


# ─── BashTool ───
class BashTool(BaseTool):
    name = "Bash"
    category = ToolCategory.EXECUTE
    patterns = ["bash", "shell", "command", "exec", "run", "çalıştır", "komut"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        cmd = input_data.get("command", "")
        cwd = input_data.get("cwd", os.getcwd())
        timeout = input_data.get("timeout", 30)
        env = input_data.get("env", {})

        if not cmd:
            return ToolResult(self.name, False, "", "command is required", int((time.time()-start)*1000))

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=min(timeout, 120),
                env={**os.environ, **env}
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            return ToolResult(
                self.name, result.returncode == 0, output[:8000],
                int((time.time()-start)*1000),
                metadata={"exit_code": result.returncode}
            )
        except subprocess.TimeoutExpired:
            return ToolResult(self.name, False, "", f"Timeout after {timeout}s", int((time.time()-start)*1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── ReadTool ───
class ReadTool(BaseTool):
    name = "Read"
    category = ToolCategory.READ
    patterns = ["read", "cat", "view", "file", "okuma", "dosya", "görüntüle"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        path = input_data.get("path", "")
        offset = input_data.get("offset", 0)
        limit = input_data.get("limit", 2000)

        if not path:
            return ToolResult(self.name, False, "", "path is required", int((time.time()-start)*1000))

        if not os.path.exists(path):
            return ToolResult(self.name, False, "", f"File not found: {path}", int((time.time()-start)*1000))

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                if offset > 0:
                    lines = f.readlines()
                    content = "".join(lines[offset:offset+limit])
                else:
                    content = f.read(limit * 200)

            return ToolResult(
                self.name, True, content,
                int((time.time()-start)*1000),
                metadata={"path": path, "size_bytes": os.path.getsize(path)}
            )
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── WriteTool ───
class WriteTool(BaseTool):
    name = "Write"
    category = ToolCategory.WRITE
    patterns = ["write", "create", "yaz", "oluştur", "kaydet", "save"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        path = input_data.get("path", "")
        content = input_data.get("content", "")
        append = input_data.get("append", False)

        if not path:
            return ToolResult(self.name, False, "", "path is required", int((time.time()-start)*1000))

        try:
            mode = "a" if append else "w"
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                self.name, True,
                f"{'Appended to' if append else 'Written'}: {path} ({len(content)} chars)",
                int((time.time()-start)*1000),
                metadata={"path": path, "bytes": len(content.encode())}
            )
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── EditTool ───
class EditTool(BaseTool):
    name = "Edit"
    category = ToolCategory.WRITE
    patterns = ["edit", "change", "replace", "düzenle", "değiştir", "guncelle"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        path = input_data.get("path", "")
        old_string = input_data.get("old_string", "")
        new_string = input_data.get("new_string", "")
        old_text = input_data.get("old_text", "") or old_string
        new_text = input_data.get("new_text", "") or new_string

        if not path:
            return ToolResult(self.name, False, "", "path is required", int((time.time()-start)*1000))

        if not old_text:
            return ToolResult(self.name, False, "", "old_text is required", int((time.time()-start)*1000))

        if not os.path.exists(path):
            return ToolResult(self.name, False, "", f"File not found: {path}", int((time.time()-start)*1000))

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_text not in content:
                return ToolResult(self.name, False, "", f"old_text not found in file", int((time.time()-start)*1000))

            new_content = content.replace(old_text, new_text, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(
                self.name, True,
                f"Edited: {path}",
                int((time.time()-start)*1000),
                metadata={"path": path}
            )
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── GlobTool ───
class GlobTool(BaseTool):
    name = "Glob"
    category = ToolCategory.READ
    patterns = ["glob", "find", "list files", "dosya bul", "listele"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        pattern = input_data.get("pattern", "**/*")
        cwd = input_data.get("cwd", os.getcwd())
        recursive = input_data.get("recursive", True)
        max_results = input_data.get("max_results", 100)

        try:
            if recursive:
                files = [str(p) for p in Path(cwd).rglob(pattern)]
            else:
                files = [str(p) for p in Path(cwd).glob(pattern)]

            files = sorted(files)[:max_results]
            return ToolResult(
                self.name, True,
                f"Found {len(files)} files:\n" + "\n".join(files),
                int((time.time()-start)*1000),
                metadata={"count": len(files)}
            )
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── GrepTool ───
class GrepTool(BaseTool):
    name = "Grep"
    category = ToolCategory.READ
    patterns = ["grep", "search", "find", "search in files", "ara", "içinde ara"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        pattern = input_data.get("pattern", "")
        path = input_data.get("path", os.getcwd())
        regex = input_data.get("regex", True)
        case_sensitive = input_data.get("case_sensitive", False)
        context_lines = input_data.get("context", 0)
        max_results = input_data.get("max_results", 50)

        if not pattern:
            return ToolResult(self.name, False, "", "pattern is required", int((time.time()-start)*1000))

        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags) if regex else None
        except re.error as e:
            return ToolResult(self.name, False, "", f"Invalid regex: {e}", int((time.time()-start)*1000))

        results = []
        for py_file in Path(path).rglob("*.py"):
            if ".venv" in str(py_file) or "node_modules" in str(py_file):
                continue
            try:
                with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if compiled.search(line) if compiled else pattern in line:
                        ctx_before = ""
                        ctx_after = ""
                        if context_lines > 0:
                            start_ctx = max(0, i - context_lines - 1)
                            ctx_before = "".join(lines[start_ctx:i-1])
                            ctx_after = "".join(lines[i:i+context_lines])
                        results.append(f"{py_file}:{i}: {line.rstrip()}")
                        if len(results) >= max_results:
                            break
            except:
                continue

        return ToolResult(
            self.name, True,
            f"Found {len(results)} matches:\n" + "\n".join(results),
            int((time.time()-start)*1000),
            metadata={"count": len(results)}
        )


# ─── ThinkTool ───
class ThinkTool(BaseTool):
    name = "Think"
    category = ToolCategory.READ
    patterns = ["think", "düşün", "reason", "analiz et"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        thought = input_data.get("thought", input_data.get("text", ""))
        return ToolResult(
            self.name, True,
            f"[Thinking...] {thought}",
            int((time.time()-start)*1000)
        )


# ─── TaskTool ───
class TaskTool(BaseTool):
    name = "Task"
    category = ToolCategory.READ
    patterns = ["task", "assign", "alt görev", "görev"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        description = input_data.get("description", "")
        task_id = input_data.get("task_id", f"task_{int(time.time())}")
        priority = input_data.get("priority", "normal")

        if not description:
            return ToolResult(self.name, False, "", "description is required", int((time.time()-start)*1000))

        # Save task
        task_file = Path("/home/ayzek/.openclaw/workspace/.harness/tasks.json")
        task_file.parent.mkdir(parents=True, exist_ok=True)

        tasks = {}
        if task_file.exists():
            try:
                tasks = json.loads(task_file.read_text())
            except:
                pass

        tasks[task_id] = {
            "id": task_id,
            "description": description,
            "priority": priority,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        task_file.write_text(json.dumps(tasks, indent=2))

        return ToolResult(
            self.name, True,
            f"Task created: {task_id}\n{description}",
            int((time.time()-start)*1000),
            metadata={"task_id": task_id}
        )


# ─── MCPTool ───
class MCPTool(BaseTool):
    name = "MCP"
    category = ToolCategory.READ
    patterns = ["mcp", "server", "model context", "tool server"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        server = input_data.get("server", "")
        command = input_data.get("command", "")
        args = input_data.get("args", [])

        if not server:
            return ToolResult(self.name, False, "", "server name is required", int((time.time()-start)*1000))

        # List available MCP servers
        if command == "list":
            mcp_config = Path("/home/ayzek/.openclaw/workspace/.mcp/config.json")
            if mcp_config.exists():
                try:
                    config = json.loads(mcp_config.read_text())
                    servers = list(config.get("mcpServers", {}).keys())
                    return ToolResult(
                        self.name, True,
                        f"MCP Servers ({len(servers)}):\n" + "\n".join(f"  - {s}" for s in servers),
                        int((time.time()-start)*1000)
                    )
                except:
                    pass
            return ToolResult(self.name, True, "No MCP servers configured", int((time.time()-start)*1000))

        return ToolResult(
            self.name, True,
            f"MCP server: {server}",
            int((time.time()-start)*1000)
        )


# ─── ScheduleCronTool ───
class ScheduleCronTool(BaseTool):
    name = "Schedule"
    category = ToolCategory.READ
    patterns = ["schedule", "cron", "zamanla", "plan", "later"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        command = input_data.get("command", "list")
        schedule = input_data.get("schedule", "")
        task = input_data.get("task", "")

        if command == "list":
            cron_file = Path("/home/ayzek/.openclaw/workspace/.harness/scheduled_tasks.json")
            if cron_file.exists():
                try:
                    tasks = json.loads(cron_file.read_text())
                    output = "Scheduled tasks:\n"
                    for tid, t in tasks.items():
                        output += f"  {tid}: {t.get('schedule', '')} -> {t.get('task', '')[:50]}\n"
                    return ToolResult(self.name, True, output, int((time.time()-start)*1000))
                except:
                    pass
            return ToolResult(self.name, True, "No scheduled tasks", int((time.time()-start)*1000))

        elif command == "add":
            if not schedule or not task:
                return ToolResult(self.name, False, "", "schedule and task required", int((time.time()-start)*1000))

            cron_file = Path("/home/ayzek/.openclaw/workspace/.harness/scheduled_tasks.json")
            tasks = {}
            if cron_file.exists():
                try:
                    tasks = json.loads(cron_file.read_text())
                except:
                    pass

            task_id = f"task_{int(time.time())}"
            tasks[task_id] = {"schedule": schedule, "task": task, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            cron_file.write_text(json.dumps(tasks, indent=2))

            return ToolResult(
                self.name, True,
                f"Scheduled: {task_id}\nEvery: {schedule}\nTask: {task[:50]}",
                int((time.time()-start)*1000),
                metadata={"task_id": task_id}
            )

        return ToolResult(self.name, False, "", f"Unknown command: {command}", int((time.time()-start)*1000))


# ─── AgentTool ───
class AgentTool(BaseTool):
    name = "Agent"
    category = ToolCategory.READ
    patterns = ["agent", "spawn", "run agent", "alt agent", "yeni agent"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        prompt = input_data.get("prompt", "")
        model = input_data.get("model", "")
        agent_type = input_data.get("type", "general")

        if not prompt:
            return ToolResult(self.name, False, "", "prompt is required", int((time.time()-start)*1000))

        # Simulate agent execution
        return ToolResult(
            self.name, True,
            f"[Agent: {agent_type}] Started with prompt: {prompt[:100]}...\n[Would spawn sub-agent here]",
            int((time.time()-start)*1000),
            metadata={"agent_type": agent_type}
        )


# ─── RuntimeTool ───
class RuntimeTool(BaseTool):
    name = "Runtime"
    category = ToolCategory.READ
    patterns = ["runtime", "system", "status", "sistem durumu"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        command = input_data.get("command", "status")

        if command == "status":
            pool_file = Path("/home/ayzek/.openclaw/workspace/.harness/tool_pool_stats.json")
            stats = {}
            if pool_file.exists():
                try:
                    stats = json.loads(pool_file.read_text())
                except:
                    pass

            output = "Runtime Status\n"
            output += f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"Working dir: {os.getcwd()}\n"
            if stats:
                output += f"Tokens: {stats.get('total_tokens', 0)}\n"
                output += f"Cost: ${stats.get('total_cost', 0):.4f}\n"

            return ToolResult(self.name, True, output, int((time.time()-start)*1000))

        return ToolResult(self.name, True, f"Runtime command: {command}", int((time.time()-start)*1000))


# ─── AnalyzeContextTool ───
class AnalyzeContextTool(BaseTool):
    name = "AnalyzeContext"
    category = ToolCategory.READ
    patterns = ["analyze", "context", "inspect", "analiz", "kontrol"]
    readonly = True

    _CACHE: dict = {}
    _CACHE_MAX_AGE = 60

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        query = input_data.get("query", "")
        path = input_data.get("path", os.getcwd())

        cache_key = f"{path}:{query}"
        now = time.time()
        if cache_key in self._CACHE:
            cached_time, cached_result = self._CACHE[cache_key]
            if now - cached_time < self._CACHE_MAX_AGE:
                return ToolResult(
                    self.name, True,
                    f"[cached] {cached_result}",
                    int((time.time()-start)*1000)
                )

        # Analyze context
        py_files = list(Path(path).rglob("*.py"))
        py_files = [f for f in py_files if ".venv" not in str(f)]

        summary = f"Context analysis for: {path}\n"
        summary += f"Python files: {len(py_files)}\n"

        if query:
            results = []
            for f in py_files[:20]:
                try:
                    with open(f, "r", encoding="utf-8", errors="replace") as fp:
                        if query.lower() in fp.read().lower():
                            results.append(str(f))
                except:
                    pass
            summary += f"\nFiles matching '{query}': {len(results)}\n"
            summary += "\n".join(results[:10])

        result = ToolResult(self.name, True, summary, int((time.time()-start)*1000))
        self._CACHE[cache_key] = (now, summary)
        return result


# ─── WebSearchTool ───
class WebSearchTool(BaseTool):
    name = "WebSearch"
    category = ToolCategory.READ
    patterns = ["search", "web search", "internet ara", "search the web", "google"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        query = input_data.get("query", "")
        limit = input_data.get("limit", 5)

        if not query:
            return ToolResult(self.name, False, "", "query is required", int((time.time()-start)*1000))

        # Check if SearXNG is available
        try:
            import urllib.request
            url = f"http://localhost:8888/search?q={query}&format=json&limit={limit}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                results = data.get("results", [])[:limit]
                output = f"Search results for '{query}':\n\n"
                for r in results:
                    title = r.get("title", "")
                    url_r = r.get("url", "")
                    output += f"• {title}\n  {url_r}\n\n"
                return ToolResult(self.name, True, output, int((time.time()-start)*1000))
        except:
            pass

        return ToolResult(
            self.name, True,
            f"[WebSearch] Query: {query}\n[SearXNG not available - would search the web]",
            int((time.time()-start)*1000)
        )
