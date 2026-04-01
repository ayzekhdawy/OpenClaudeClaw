"""
Query Engine — Orchestration Layer
──────────────────────────────────
Claude Code'un QueryEngine.ts'sine benzer orchestration.
Tüm harness bileşenlerini koordine eder.
"""

from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import uuid


class QueryEngine:
    """
    Ana orchestration engine.
    Tüm bileşenleri koordine eder.
    """
    
    def __init__(self):
        self.session_id = self._generate_session_id()
        self.start_time = datetime.now()
        self.turn_count = 0
        self.history: list[dict] = []
        
        # Components (lazy loaded)
        self._cost_tracker = None
        self._semantic_memory = None
        self._mcp_pool = None
        self._tool_pool = None
        self._context_builder = None
    
    def _generate_session_id(self) -> str:
        return str(uuid.uuid4())[:8]
    
    @property
    def cost_tracker(self):
        if self._cost_tracker is None:
            from .cost_tracker import get_cost_tracker
            self._cost_tracker = get_cost_tracker()
        return self._cost_tracker
    
    @property
    def semantic_memory(self):
        if self._semantic_memory is None:
            from .semantic_memory import get_semantic_memory
            self._semantic_memory = get_semantic_memory()
        return self._semantic_memory
    
    @property
    def mcp_pool(self):
        if self._mcp_pool is None:
            from .mcp_pool import get_mcp_pool
            self._mcp_pool = get_mcp_pool()
        return self._mcp_pool
    
    @property
    def tool_pool(self):
        if self._tool_pool is None:
            from .tool_pool import get_tool_pool
            self._tool_pool = get_tool_pool()
        return self._tool_pool
    
    @property
    def context_builder(self):
        if self._context_builder is None:
            from .context_manager import get_context_manager
            self._context_builder = get_context_manager()
        return self._context_builder
    
    async def execute(
        self,
        prompt: str,
        context: dict = None,
        tools: list = None,
        model: str = None,
        max_turns: int = 10,
        callback: Callable = None,
    ) -> dict:
        """
        Prompt'ı işle, tool çağrılarını yönet.
        
        Args:
            prompt: Kullanıcı mesajı
            context: Ek context
            tools: Kullanılabilir tool'lar
            model: Model seçimi
            max_turns: Max tool call döngüsü
            callback: Progress callback'i
        
        Returns:
            dict: {response, tool_calls, cost, session_id}
        """
        self.turn_count += 1
        
        # Build full context
        full_context = self._build_context(prompt, context or {})
        
        # Get available tools
        available_tools = tools or self._get_default_tools()
        
        # Add MCP tools if available
        if self.mcp_pool.tools:
            available_tools = available_tools + self._format_mcp_tools()
        
        # Call the runtime
        from .runtime import HarnessRuntime
        
        runtime = HarnessRuntime()
        
        result = await runtime.execute(
            prompt=prompt,
            context=full_context,
            tools=available_tools,
            model=model,
            max_turns=max_turns,
            callback=callback,
        )
        
        # Track cost
        if result.get("usage"):
            self.cost_tracker.add_usage(
                model=model or "default",
                **result["usage"],
            )
        
        # Save to history
        self.history.append({
            "turn": self.turn_count,
            "prompt": prompt,
            "response": result.get("response", ""),
            "tool_calls": len(result.get("tool_calls", [])),
            "timestamp": datetime.now().isoformat(),
        })
        
        return result
    
    def _build_context(self, prompt: str, extra: dict) -> dict:
        """Context building orchestration."""
        context = {
            "session_id": self.session_id,
            "turn": self.turn_count,
            "start_time": self.start_time.isoformat(),
            "semantic_memory_context": self.semantic_memory.get_context_for_task(prompt),
            "cost_summary": self.cost_tracker.get_summary(),
            "recent_memories": self._get_recent_memory_context(),
        }
        
        context.update(extra)
        
        return context
    
    def _get_default_tools(self) -> list[dict]:
        """Default tool listesi."""
        return self.tool_pool.get_tools_for_prompt()
    
    def _format_mcp_tools(self) -> list[dict]:
        """MCP tools'u prompt formatına çevir."""
        mcp_tools = []
        
        for tool in self.mcp_pool.tools.values():
            mcp_tools.append({
                "name": f"mcp_{tool.server_name}_{tool.name}",
                "description": tool.description,
                "input_schema": tool.input_schema,
            })
        
        return mcp_tools
    
    def _get_recent_memory_context(self) -> str:
        """Son memory context'ini al."""
        try:
            recent = self.semantic_memory.get_recent(days=3, limit=5)
            if not recent:
                return ""
            
            lines = ["\n\n## Recent Memories\n"]
            for f in recent:
                lines.append(f"- {f.filename}: {f.description[:50]}...")
            
            return '\n'.join(lines)
        except Exception:
            return ""
    
    def get_session_summary(self) -> dict:
        """Session özetini döndür."""
        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "cost": self.cost_tracker.get_summary(),
            "cost_breakdown": self.cost_tracker.get_model_breakdown(),
            "memory_stats": self.semantic_memory.get_stats(),
            "mcp_servers": self.mcp_pool.list_servers(),
            "mcp_tool_count": len(self.mcp_pool.tools),
        }
    
    def get_history(self) -> list[dict]:
        """Konuşma geçmişini döndür."""
        return self.history
    
    def reset(self):
        """Session'u resetle."""
        self.session_id = self._generate_session_id()
        self.start_time = datetime.now()
        self.turn_count = 0
        self.history = []
        self.cost_tracker.reset()


# Singleton
_query_engine: Optional[QueryEngine] = None


def get_query_engine() -> QueryEngine:
    global _query_engine
    if _query_engine is None:
        _query_engine = QueryEngine()
    return _query_engine
