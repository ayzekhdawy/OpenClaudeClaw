"""
Memory Fabric — surfaced memory tracking and richer selection
────────────────────────────────────────────────────────────
Tracks which memories have already been surfaced in a runtime and
combines semantic + session memory into one reusable context surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .semantic_memory import get_semantic_memory
from .session_memory import get_session_memory


@dataclass
class SurfacedMemory:
    filename: str
    source: str
    excerpt: str
    score: float = 0.0


@dataclass
class MemorySelection:
    query: str
    surfaced: list[SurfacedMemory] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "surfaced": [m.__dict__ for m in self.surfaced],
            "skipped": self.skipped,
        }


class MemoryFabric:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.semantic_memory = get_semantic_memory()
        self.session_memory = get_session_memory(session_id)
        self.surfaced_files: list[str] = []
        self.selection_history: list[MemorySelection] = []

    def select(self, query: str, max_items: int = 5) -> MemorySelection:
        semantic = self.semantic_memory.find_relevant(query, recent_tools=self.surfaced_files, use_llm=False)
        selection = MemorySelection(query=query)

        for memory in semantic[:max_items]:
            if memory.filename in self.surfaced_files:
                selection.skipped.append(memory.filename)
                continue
            content = self.semantic_memory.get_content(memory.filename) or memory.description
            selection.surfaced.append(
                SurfacedMemory(
                    filename=memory.filename,
                    source="semantic",
                    excerpt=content[:500],
                    score=1.0,
                )
            )
            self.surfaced_files.append(memory.filename)

        session_excerpt = self.session_memory.read_notes()[:600]
        if session_excerpt.strip():
            selection.surfaced.append(
                SurfacedMemory(
                    filename=self.session_memory.get_notes_path().name,
                    source="session",
                    excerpt=session_excerpt,
                    score=0.8,
                )
            )

        self.selection_history.append(selection)
        return selection

    def build_context(self, query: str, max_items: int = 5) -> str:
        selection = self.select(query, max_items=max_items)
        parts = []
        for item in selection.surfaced:
            parts.append(f"## {item.source}:{item.filename}\n{item.excerpt}")
        return "\n---\n".join(parts)

    def diagnostics(self) -> dict:
        return {
            "session_id": self.session_id,
            "surfaced_count": len(self.surfaced_files),
            "surfaced_files": self.surfaced_files[-10:],
            "selection_count": len(self.selection_history),
            "last_selection": self.selection_history[-1].to_dict() if self.selection_history else None,
        }


_GLOBAL_FABRICS: dict[str, MemoryFabric] = {}


def get_memory_fabric(session_id: Optional[str] = None) -> MemoryFabric:
    key = session_id or "default"
    if key not in _GLOBAL_FABRICS:
        _GLOBAL_FABRICS[key] = MemoryFabric(session_id)
    return _GLOBAL_FABRICS[key]
