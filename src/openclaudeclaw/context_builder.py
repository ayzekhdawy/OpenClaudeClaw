"""
Harness Context Builder — OpenClaw Full Context
──────────────────────────────────────────────
Tüm OpenClaw içsel yapılarını harness context'inde birleştirir.

Kullanım:
    from src.harness.context_builder import build_context
    
    context = build_context("Flech için içerik hazırla")
    print(context.full_prompt)
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))

from src.harness.integrations import (
    get_soul_adapter,
    get_memory_adapter,
    get_user_adapter,
)
from src.harness.context_manager import get_workspace_context, format_context_prompt


@dataclass
class HarnessContext:
    """
    OpenClaw harness context'i.
    Tüm içsel yapıları birleştirir.
    """
    persona: str           # SOUL.md persona
    user: str              # USER.md profili
    memory: str            # MEMORY.md kritik bilgiler
    workspace: str          # Workspace analizi
    task_context: str      # Göreve özel memory
    system_prompt: str     # Birleşik system prompt
    
    @property
    def full_prompt(self) -> str:
        """Tüm context'i tek prompt olarak döndür."""
        parts = [
            "# SYSTEM CONTEXT",
            "",
            self.persona,
            "",
            self.user,
            "",
            self.memory,
            "",
            "# WORKSPACE",
            self.workspace,
        ]
        
        if self.task_context:
            parts.extend(["", "# TASK CONTEXT", self.task_context])
        
        return '\n\n'.join(parts)


def build_context(
    task: str = "",
    include_persona: bool = True,
    include_user: bool = True,
    include_memory: bool = True,
    include_workspace: bool = True,
) -> HarnessContext:
    """
    Harness için tam context oluşturur.
    
    Args:
        task: Görev açıklaması (task-specific context için)
        include_*: Hangi bileşenleri dahil et
    
    Returns:
        HarnessContext nesnesi
    """
    parts = {}
    
    # 1. SOUL — Persona
    if include_persona:
        soul = get_soul_adapter()
        parts['persona'] = soul.get_persona_prompt()
    else:
        parts['persona'] = ""
    
    # 2. USER — İshak profili
    if include_user:
        user = get_user_adapter()
        parts['user'] = user.get_full_context()
    else:
        parts['user'] = ""
    
    # 3. MEMORY — Hafıza
    if include_memory:
        memory = get_memory_adapter()
        parts['memory'] = memory.get_critical_info()
    else:
        parts['memory'] = ""
    
    # 4. Workspace context
    if include_workspace:
        ws_context = get_workspace_context()
        parts['workspace'] = format_context_prompt(ws_context)
    else:
        parts['workspace'] = ""
    
    # 5. Task-specific context
    if task:
        memory = get_memory_adapter()
        parts['task_context'] = memory.get_context_for_task(task)
    else:
        parts['task_context'] = ""
    
    # Build system prompt
    system_parts = [
        parts['persona'],
        parts['user'],
        parts['memory'],
        parts['workspace'],
    ]
    if parts['task_context']:
        system_parts.append(parts['task_context'])
    
    system_prompt = '\n\n'.join(filter(None, system_parts))
    
    return HarnessContext(
        persona=parts['persona'],
        user=parts['user'],
        memory=parts['memory'],
        workspace=parts['workspace'],
        task_context=parts['task_context'],
        system_prompt=system_prompt,
    )


def validate_and_sanitize(response: str) -> tuple[str, list[str]]:
    """
    Response'ı SOUL kurallarına göre validate ed.
    
    Returns:
        (sanitized_response, warnings)
    """
    from src.harness.integrations import validate_response
    
    valid, warning = validate_response(response)
    
    warnings = []
    if warning:
        warnings.append(warning)
    
    # Basic sanitization
    sanitized = response
    
    # Remove common filler
    filler = ['Tamam, ', 'Peki, ', 'Anladım, ']
    for f in filler:
        if sanitized.startswith(f):
            sanitized = sanitized[len(f):]
    
    return sanitized, warnings


_CONTEXT_CACHE: dict = {}
_CACHE_MAX_AGE = 60  # seconds


def analyze_context(task: str = "") -> dict:
    """Claude Code benzeri analyzeContext görünürlüğü. 60sn cache ile."""
    import time
    key = task or ""
    now = time.time()
    if key in _CONTEXT_CACHE:
        cached_time, cached_result = _CONTEXT_CACHE[key]
        if now - cached_time < _CACHE_MAX_AGE:
            return cached_result

    # Lazy import to avoid circular dependency
    from src.harness.semantic_memory import get_semantic_memory

    ws = get_workspace_context()
    memory = get_semantic_memory()
    relevant = memory.find_relevant(task, use_llm=False) if task else []

    known_tools = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Think", "Task", "MCP", "Schedule", "Agent", "AnalyzeContext", "Skill", "Runtime"]
    suggestions = [t for t in known_tools if task and t.lower() in task.lower()] if task else known_tools[:5]

    risk = "low"
    if any(name in suggestions for name in ["Bash", "Write", "Edit"]):
        risk = "medium"
    if "Bash" in suggestions and any(word in task.lower() for word in ["delete", "remove", "drop", "kill"]):
        risk = "high"

    # Build context only when needed (expensive)
    try:
        ctx = build_context(task=task)
        sys_prompt_len = len(ctx.system_prompt)
        task_ctx_len = len(ctx.task_context or "")
    except Exception:
        sys_prompt_len = 0
        task_ctx_len = 0

    result = {
        "task": task,
        "workspace": ws.to_dict(),
        "system_prompt_length": sys_prompt_len,
        "task_context_length": task_ctx_len,
        "tool_suggestions": suggestions,
        "relevant_memories": [f.filename for f in relevant],
        "risk": risk,
    }

    _CONTEXT_CACHE[key] = (now, result)
    return result


if __name__ == "__main__":
    print("=== CONTEXT BUILDER TEST ===\n")
    
    # Full context
    ctx = build_context("Flech için tweet hazırla")
    
    print("Persona (first 200 chars):")
    print(ctx.persona[:200] + "...")
    print()
    
    print("User (first 200 chars):")
    print(ctx.user[:200] + "...")
    print()
    
    print("Memory (first 200 chars):")
    print(ctx.memory[:200] + "...")
    print()
    
    print("Workspace (first 200 chars):")
    print(ctx.workspace[:200] + "...")
    print()
    
    print("Full prompt length:", len(ctx.full_prompt), "chars")
    print()
    
    # Task-specific
    print("=== TASK CONTEXT TEST ===")
    ctx2 = build_context("kahve satış")
    print("Task:", ctx2.task_context[:300] if ctx2.task_context else "(empty)")
