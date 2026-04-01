"""
Task Manager — OpenClaw Todo/Task System
────────────────────────────────────────
Claude Code Task system referansı.
Tüm görevleri izler, önceliklendirir, deadline'ları takip eder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum
import json
import uuid


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Bir görev."""
    id: str
    title: str
    description: str = ""
    priority: Priority = Priority.NORMAL
    status: Status = Status.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_at: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    subtasks: list[str] = field(default_factory=list)
    assigned_to: Optional[str] = None  # "esra", "ishak", "agent-x"
    blocked_by: list[str] = field(default_factory=list)  # task IDs
    context: dict = field(default_factory=dict)  # Ek metadata
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "due_at": self.due_at,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "subtasks": self.subtasks,
            "assigned_to": self.assigned_to,
            "blocked_by": self.blocked_by,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d["id"],
            title=d["title"],
            description=d.get("description", ""),
            priority=Priority[d.get("priority", "NORMAL")],
            status=Status(d.get("status", "pending")),
            created_at=d.get("created_at", datetime.now().isoformat()),
            updated_at=d.get("updated_at", datetime.now().isoformat()),
            due_at=d.get("due_at"),
            tags=d.get("tags", []),
            parent_id=d.get("parent_id"),
            subtasks=d.get("subtasks", []),
            assigned_to=d.get("assigned_to"),
            blocked_by=d.get("blocked_by", []),
            context=d.get("context", {}),
        )


class TaskManager:
    """
    Merkezi görev yönetim sistemi.
    Tüm görevleri izler, önceliklendirir, deadline'ları takip eder.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".openclaw" / "tasks.json"
        self.tasks: dict[str, Task] = {}
        self._load()
    
    def _load(self):
        """Görevleri yükle."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.tasks = {
                    k: Task.from_dict(v) for k, v in data.items()
                }
            except Exception:
                self.tasks = {}
    
    def _save(self):
        """Görevleri kaydet."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v.to_dict() for k, v in self.tasks.items()}
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def create(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.NORMAL,
        due_at: Optional[str] = None,
        tags: Optional[list[str]] = None,
        assigned_to: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Task:
        """
        Yeni görev oluştur.
        
        Args:
            title: Görev başlığı
            description: Detaylı açıklama
            priority: Öncelik
            due_at: Deadline (ISO format)
            tags: Etiketler
            assigned_to: Atanan kişi/agent
            parent_id: Üst görev ID (subtask için)
        
        Returns:
            Oluşturulan Task
        """
        task = Task(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
            tags=tags or [],
            assigned_to=assigned_to,
            parent_id=parent_id,
        )
        
        self.tasks[task.id] = task
        
        # Parent'a subtask olarak ekle
        if parent_id and parent_id in self.tasks:
            self.tasks[parent_id].subtasks.append(task.id)
        
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
                if key == "priority" and isinstance(value, str):
                    value = Priority[value]
                elif key == "status" and isinstance(value, str):
                    value = Status(value)
                setattr(task, key, value)
        
        task.updated_at = datetime.now().isoformat()
        self._save()
        return task
    
    def delete(self, task_id: str) -> bool:
        """Görev sil."""
        if task_id not in self.tasks:
            return False
        
        # Subtask'leri de sil
        task = self.tasks[task_id]
        for subtask_id in task.subtasks:
            self.delete(subtask_id)
        
        # Parent'dan da kaldır
        if task.parent_id and task.parent_id in self.tasks:
            parent = self.tasks[task.parent_id]
            if task_id in parent.subtasks:
                parent.subtasks.remove(task_id)
        
        del self.tasks[task_id]
        self._save()
        return True
    
    def list(
        self,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
        include_subtasks: bool = True,
    ) -> list[Task]:
        """
        Görevleri filtrele ve listele.
        """
        result = []
        
        for task in self.tasks.values():
            # Subtask değilse veya include_subtasks açıksa
            if task.parent_id and not include_subtasks:
                continue
            
            # Filtreler
            if status and task.status != status:
                continue
            if priority and task.priority != priority:
                continue
            if assigned_to and task.assigned_to != assigned_to:
                continue
            if tags and not any(t in task.tags for t in tags):
                continue
            
            result.append(task)
        
        # Önce priority, sonra created_at sırala
        result.sort(key=lambda t: (t.priority.value, t.created_at))
        
        return result
    
    def get_todo_list(self, assigned_to: str = "esra") -> str:
        """
        Todo listesi oluştur (user'a gösterilecek format).
        """
        tasks = self.list(
            status=Status.PENDING,
            assigned_to=assigned_to,
        )
        
        if not tasks:
            return "✅ Yapılacak görev yok."
        
        lines = ["📋 **Yapılacaklar:**", ""]
        
        for i, task in enumerate(tasks[:10], 1):
            priority_icon = {
                Priority.CRITICAL: "🔴",
                Priority.HIGH: "🟠",
                Priority.NORMAL: "🟡",
                Priority.LOW: "⚪",
            }.get(task.priority, "⚪")
            
            lines.append(f"{priority_icon} {i}. {task.title}")
            
            if task.description:
                lines.append(f"   └ {task.description[:50]}...")
            
            if task.due_at:
                lines.append(f"   └ 📅 {task.due_at}")
        
        if len(tasks) > 10:
            lines.append(f"... (+{len(tasks) - 10} görev)")
        
        return '\n'.join(lines)
    
    def get_stats(self) -> dict:
        """İstatistikler."""
        tasks = list(self.tasks.values())
        
        return {
            "total": len(tasks),
            "by_status": {
                s.value: len([t for t in tasks if t.status == s])
                for s in Status
            },
            "by_priority": {
                p.name: len([t for t in tasks if t.priority == p])
                for p in Priority
            },
            "overdue": len([
                t for t in tasks
                if t.status not in (Status.DONE, Status.CANCELLED)
                and t.due_at and t.due_at < datetime.now().isoformat()
            ]),
            "assigned_to_me": len([
                t for t in tasks
                if t.assigned_to == "esra"
                and t.status == Status.PENDING
            ]),
        }
    
    def complete(self, task_id: str) -> bool:
        """Görevi tamamla."""
        return self.update(task_id, status=Status.DONE) is not None
    
    def block_task(self, task_id: str, blocked_by: list[str]) -> bool:
        """Görevi blokla."""
        return self.update(task_id, blocked_by=blocked_by) is not None
    
    def add_subtask(self, parent_id: str, title: str, **kwargs) -> Optional[Task]:
        """Alt görev ekle."""
        if parent_id not in self.tasks:
            return None
        return self.create(title, parent_id=parent_id, **kwargs)


# Singleton
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


if __name__ == "__main__":
    tm = get_task_manager()
    
    print("=== TASK MANAGER TEST ===\n")
    
    # Create task
    task = tm.create(
        title="Test görev",
        description="Bu bir test görevidir",
        priority=Priority.HIGH,
        assigned_to="esra",
    )
    print(f"✓ Task oluşturuldu: {task.id}")
    
    # List
    tasks = tm.list()
    print(f"✓ Toplam görev: {len(tasks)}")
    
    # Stats
    stats = tm.get_stats()
    print(f"✓ Stats: {stats}")
    
    # Todo list
    print("\n" + tm.get_todo_list())
