"""
TodoWriteTool — Task checklist management
─────────────────────────────────────────
Claude Code TodoWriteTool referansı.
Session içinde todo list yönetir.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from ..models import BaseTool, ToolResult, ToolCategory


class TodoStatus(str, Enum):
    IN_PROGRESS = "inProgress"
    NOT_STARTED = "notStarted"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """Single todo item."""
    content: str
    status: TodoStatus = TodoStatus.NOT_STARTED
    activeForm: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


_TODO_FILE = "/home/ayzek/.openclaw/workspace/.harness/todos.json"


def _load_todos() -> list[dict]:
    """Load todos from file."""
    import json
    from pathlib import Path
    f = Path(_TODO_FILE)
    if f.exists():
        return json.loads(f.read_text())
    return []


def _save_todos(todos: list[dict]):
    """Save todos to file."""
    import json
    from pathlib import Path
    Path(_TODO_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(_TODO_FILE).write_text(json.dumps(todos, indent=2, ensure_ascii=False))


class TodoWriteTool(BaseTool):
    """
    Todo list manager - Claude Code pattern.
    
    Actions:
    - write: Replace entire todo list
    - append: Add item to list
    - update: Update single item status
    
    Patterns: todo, görev listesi, checklist
    """
    name = "TodoWrite"
    category = ToolCategory.WRITE
    patterns = ["todo", "görev", "checklist", "task list", "yapılacak"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        import time
        start = time.time()
        
        action = input_data.get("action", "write")
        todos_data = _load_todos()
        
        try:
            if action == "write":
                # Full replace
                new_todos = input_data.get("todos", [])
                _save_todos(new_todos)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"Todo list updated: {len(new_todos)} items",
                    duration_ms=int((time.time() - start) * 1000),
                )
            
            elif action == "append":
                item = input_data.get("item", {})
                content = item.get("content", "")
                status = item.get("status", "notStarted")
                
                new_item = {
                    "content": content,
                    "status": status,
                    "activeForm": item.get("activeForm"),
                    "created_at": datetime.now().isoformat(),
                }
                todos_data.append(new_item)
                _save_todos(todos_data)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"Added: {content[:50]}",
                    duration_ms=int((time.time() - start) * 1000),
                )
            
            elif action == "update":
                index = input_data.get("index", -1)
                status = input_data.get("status")
                
                if 0 <= index < len(todos_data):
                    if status:
                        todos_data[index]["status"] = status
                    _save_todos(todos_data)
                    return ToolResult(
                        tool_name=self.name,
                        success=True,
                        output=f"Updated item {index}: {status}",
                        duration_ms=int((time.time() - start) * 1000),
                    )
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Index {index} out of range",
                    duration_ms=int((time.time() - start) * 1000),
                )
            
            elif action == "list":
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"{len(todos_data)} items\n" + "\n".join(
                        f"[{i}] [{t['status']}] {t['content'][:60]}"
                        for i, t in enumerate(todos_data)
                    ),
                    duration_ms=int((time.time() - start) * 1000),
                )
            
            elif action == "clear":
                _save_todos([])
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output="Todo list cleared",
                    duration_ms=int((time.time() - start) * 1000),
                )
            
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Unknown action: {action}. Use: write, append, update, list, clear",
                    duration_ms=int((time.time() - start) * 1000),
                )
        
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )
