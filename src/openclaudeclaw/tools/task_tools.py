"""
TaskTool — Task management (Create/Get/Update/Stop)
──────────────────────────────────────────────────
Claude Code TaskCreateTool, TaskGetTool, TaskUpdateTool, TaskStopTool referansı.
Task pool üzerinde CRUD işlemleri.
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from enum import Enum

from ..models import BaseTool, ToolResult, ToolCategory


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


TASK_FILE = Path("/home/ayzek/.openclaw/workspace/.harness/task_log.jsonl")


def _load_tasks() -> list[dict]:
    tasks = []
    if TASK_FILE.exists():
        with open(TASK_FILE) as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
    return tasks


def _save_task(task: dict):
    TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASK_FILE, "a") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")


class TaskCreateTool(BaseTool):
    """Create a new task."""
    name = "TaskCreate"
    category = ToolCategory.WRITE
    patterns = ["task create", "yeni görev", "task oluştur"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        priority = input_data.get("priority", "normal")
        tags = input_data.get("tags", [])
        
        if not title:
            return ToolResult(self.name, False, "", "title is required", int((time.time()-start)*1000))
        
        task = {
            "id": f"task_{int(time.time()*1000)}",
            "title": title,
            "description": description,
            "priority": priority,
            "tags": tags,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        _save_task(task)
        
        return ToolResult(
            self.name, True,
            f"Task created: [{task['id']}] {title}",
            duration_ms=int((time.time()-start)*1000),
            metadata={"task_id": task["id"]}
        )


class TaskGetTool(BaseTool):
    """Get task by ID or list tasks."""
    name = "TaskGet"
    category = ToolCategory.READ
    patterns = ["task get", "task show", "görev göster", "task details"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        task_id = input_data.get("task_id", "")
        tasks = _load_tasks()
        
        if task_id:
            for t in tasks:
                if t.get("id") == task_id:
                    return ToolResult(
                        self.name, True,
                        json.dumps(t, indent=2, ensure_ascii=False),
                        duration_ms=int((time.time()-start)*1000),
                    )
            return ToolResult(self.name, False, "", f"Task not found: {task_id}", int((time.time()-start)*1000))
        
        # List all
        if not tasks:
            return ToolResult(self.name, True, "No tasks found", duration_ms=int((time.time()-start)*1000))
        
        output = f"{len(tasks)} tasks:\n"
        for t in tasks[-20:]:  # Last 20
            output += f"[{t['id']}] [{t['status']}] {t['title'][:60]}\n"
        
        return ToolResult(self.name, True, output, duration_ms=int((time.time()-start)*1000))


class TaskUpdateTool(BaseTool):
    """Update task status or fields."""
    name = "TaskUpdate"
    category = ToolCategory.WRITE
    patterns = ["task update", "task status", "görev güncelle", "task durumu"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        task_id = input_data.get("task_id", "")
        status = input_data.get("status", "")
        fields = input_data.get("fields", {})
        
        if not task_id:
            return ToolResult(self.name, False, "", "task_id is required", int((time.time()-start)*1000))
        
        tasks = _load_tasks()
        updated = False
        
        for i, t in enumerate(tasks):
            if t.get("id") == task_id:
                if status:
                    t["status"] = status
                t["fields"] = fields
                t["updated_at"] = datetime.now().isoformat()
                tasks[i] = t
                updated = True
                break
        
        if updated:
            # Rewrite file
            with open(TASK_FILE, "w") as f:
                for t in tasks:
                    f.write(json.dumps(t, ensure_ascii=False) + "\n")
            
            return ToolResult(
                self.name, True,
                f"Updated [{task_id}]: {status or json.dumps(fields)}",
                duration_ms=int((time.time()-start)*1000),
            )
        
        return ToolResult(self.name, False, "", f"Task not found: {task_id}", int((time.time()-start)*1000))


class TaskStopTool(BaseTool):
    """Stop/cancel a running task."""
    name = "TaskStop"
    category = ToolCategory.EXECUTE
    patterns = ["task stop", "task cancel", "görev durdur", "task iptal"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        task_id = input_data.get("task_id", "")
        
        if not task_id:
            return ToolResult(self.name, False, "", "task_id is required", int((time.time()-start)*1000))
        
        tasks = _load_tasks()
        
        for i, t in enumerate(tasks):
            if t.get("id") == task_id:
                t["status"] = "cancelled"
                t["updated_at"] = datetime.now().isoformat()
                t["stopped_at"] = datetime.now().isoformat()
                tasks[i] = t
                
                with open(TASK_FILE, "w") as f:
                    for task in tasks:
                        f.write(json.dumps(task, ensure_ascii=False) + "\n")
                
                return ToolResult(
                    self.name, True,
                    f"Task cancelled: {task_id}",
                    duration_ms=int((time.time()-start)*1000),
                )
        
        return ToolResult(self.name, False, "", f"Task not found: {task_id}", int((time.time()-start)*1000))
