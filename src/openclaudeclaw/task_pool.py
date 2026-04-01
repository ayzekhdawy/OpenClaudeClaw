"""
Task Pool — Multi-Task Orchestration
───────────────────────────────────
Claude Code TaskCreateTool pattern'i.

Harness agent'a task management tool'u ekler.
7 → 8 tools.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Bir görev."""
    id: str
    name: str
    description: str = ""
    priority: str = "NORMAL"
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_at: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    result: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "due_at": self.due_at,
            "tags": self.tags,
            "assigned_to": self.assigned_to,
            "result": self.result,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            priority=d.get("priority", "NORMAL"),
            status=d.get("status", "pending"),
            created_at=d.get("created_at", datetime.now().isoformat()),
            updated_at=d.get("updated_at", datetime.now().isoformat()),
            due_at=d.get("due_at"),
            tags=d.get("tags", []),
            assigned_to=d.get("assigned_to"),
            result=d.get("result"),
        )


class TaskStore:
    """
    Task depolama — JSON file backend.
    memory/ altında tasks.json
    """
    
    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or Path("/home/ayzek/.openclaw/workspace/memory/tasks.json")
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def _load(self):
        """Store'u yükle."""
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.tasks = {k: Task.from_dict(v) for k, v in data.items()}
            except Exception:
                self.tasks = {}
        else:
            self.tasks = {}
    
    def _save(self):
        """Store'u kaydet."""
        data = {k: v.to_dict() for k, v in self.tasks.items()}
        self.store_path.write_text(json.dumps(data, indent=2))
    
    def create(self, name: str, description: str = "", priority: str = "NORMAL", 
               assigned_to: Optional[str] = None, tags: Optional[list[str]] = None,
               due_at: Optional[str] = None) -> Task:
        """Yeni görev oluştur."""
        task = Task(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            tags=tags or [],
            due_at=due_at,
        )
        
        self.tasks[task.id] = task
        self._save()
        
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """Görev getir."""
        return self.tasks.get(task_id)
    
    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Görev güncelle."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now().isoformat()
        self._save()
        
        return task
    
    def delete(self, task_id: str) -> bool:
        """Görev sil."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()
            return True
        return False
    
    def list(self, status: Optional[str] = None, assigned_to: Optional[str] = None,
             tags: Optional[list[str]] = None) -> list[Task]:
        """Görevleri listele."""
        result = []
        
        for task in self.tasks.values():
            if status and task.status != status:
                continue
            if assigned_to and task.assigned_to != assigned_to:
                continue
            if tags and not any(t in task.tags for t in tags):
                continue
            
            result.append(task)
        
        # Priority + created sort
        priority_order = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}
        result.sort(key=lambda t: (priority_order.get(t.priority, 2), t.created_at))
        
        return result
    
    def get_stats(self) -> dict:
        """İstatistikler."""
        tasks = list(self.tasks.values())
        
        by_status = {}
        for s in TaskStatus:
            by_status[s.value] = len([t for t in tasks if t.status == s.value])
        
        by_priority = {}
        for p in Priority:
            by_priority[p.name] = len([t for t in tasks if t.priority == p.name])
        
        return {
            "total": len(tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "pending": len([t for t in tasks if t.status == "pending"]),
            "done": len([t for t in tasks if t.status == "done"]),
        }


class TaskPool:
    """
    Task management pool.
    
    Harness agent'a eklenen tool'lar:
    - task_create: Yeni görev oluştur
    - task_list: Aktif görevleri listele
    - task_get: Görev detayı getir
    - task_update: Görev güncelle (status, result, ...)
    - task_delete: Görev sil
    """
    
    def __init__(self):
        self.store = TaskStore()
    
    def task_create(
        self,
        name: str,
        description: str = "",
        priority: str = "NORMAL",
        assigned_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
        due_at: Optional[str] = None,
    ) -> dict:
        """
        Yeni görev oluştur.
        
        Returns:
            dict: {"task_id": "...", "name": "...", "status": "created"}
        """
        task = self.store.create(
            name=name,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            tags=tags,
            due_at=due_at,
        )
        
        return {
            "task_id": task.id,
            "name": task.name,
            "status": "created",
            "priority": task.priority,
            "created_at": task.created_at,
        }
    
    def task_list(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 10,
    ) -> dict:
        """
        Görevleri listele.
        
        Returns:
            dict: {"tasks": [...], "total": N, "stats": {...}}
        """
        tasks = self.store.list(status=status, assigned_to=assigned_to)
        
        task_list = []
        for t in tasks[:limit]:
            task_list.append({
                "id": t.id,
                "name": t.name,
                "description": t.description[:50] + "..." if len(t.description) > 50 else t.description,
                "priority": t.priority,
                "status": t.status,
                "assigned_to": t.assigned_to,
                "created_at": t.created_at,
            })
        
        return {
            "tasks": task_list,
            "total": len(tasks),
            "stats": self.store.get_stats(),
        }
    
    def task_get(self, task_id: str) -> Optional[dict]:
        """
        Görev detayı getir.
        
        Returns:
            dict: Task detayları veya None
        """
        task = self.store.get(task_id)
        
        if not task:
            return None
        
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "assigned_to": task.assigned_to,
            "tags": task.tags,
            "due_at": task.due_at,
            "result": task.result,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
    
    def task_update(
        self,
        task_id: str,
        status: Optional[str] = None,
        result: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Görev güncelle.
        
        Args:
            task_id: Görev ID
            status: Yeni status (pending/in_progress/done/cancelled/blocked)
            result: Görev sonucu
        
        Returns:
            dict: Güncellenmiş görev veya error
        """
        updates = {}
        
        if status:
            if status not in [s.value for s in TaskStatus]:
                return {"error": f"Geçersiz status: {status}"}
            updates["status"] = status
        
        if result:
            updates["result"] = result

        if "priority" in kwargs and kwargs["priority"]:
            updates["priority"] = kwargs["priority"]
        if "assigned_to" in kwargs and kwargs["assigned_to"] is not None:
            updates["assigned_to"] = kwargs["assigned_to"]
        if "due_at" in kwargs and kwargs["due_at"] is not None:
            updates["due_at"] = kwargs["due_at"]
        if "tags" in kwargs and kwargs["tags"] is not None:
            updates["tags"] = kwargs["tags"]

        task = self.store.update(task_id, **updates)
        
        if not task:
            return {"error": f"Görev bulunamadı: {task_id}"}
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "updated_at": task.updated_at,
        }
    
    def task_delete(self, task_id: str) -> dict:
        """
        Görev sil.
        
        Returns:
            dict: {"deleted": True/False}
        """
        deleted = self.store.delete(task_id)
        return {"deleted": deleted, "task_id": task_id}

    def task_stop(self, task_id: str, result: Optional[str] = None) -> dict:
        """Görevi iptal/stop et."""
        return self.task_update(task_id=task_id, status="cancelled", result=result)
    
    def task_stats(self) -> dict:
        """İstatistikler."""
        return self.store.get_stats()


# Singleton
_task_pool: Optional[TaskPool] = None


def get_task_pool() -> TaskPool:
    global _task_pool
    if _task_pool is None:
        _task_pool = TaskPool()
    return _task_pool


if __name__ == "__main__":
    pool = get_task_pool()
    
    print("=== TASK POOL TEST ===\n")
    
    # Create
    result = pool.task_create(
        name="Flech içerik planı",
        description="Flech cold brew için içerik planı hazırla",
        priority="HIGH",
        assigned_to="esra",
        tags=["flech", "içerik"],
    )
    print(f"✓ Created: {result}")
    
    # List
    result = pool.task_list(status="pending")
    print(f"\n✓ List: {result['total']} tasks")
    
    # Get
    task_id = result["tasks"][0]["id"]
    result = pool.task_get(task_id)
    print(f"\n✓ Get: {result}")
    
    # Update
    result = pool.task_update(task_id, status="in_progress")
    print(f"\n✓ Update: {result}")
    
    # Stats
    stats = pool.task_stats()
    print(f"\n✓ Stats: {stats}")
