"""
Harness Runtime — Main orchestration layer
────────────────────────────────────────────────────────
Clean-room implementation inspired by Claude Code's runtime patterns.
Coordinates tools, context, and session management.
"""

import uuid
import time
from datetime import datetime
from typing import Optional, Any

from .models import (
    ToolResult, 
    ToolUse, 
    CostSummary, 
    SessionManifest,
)
from .tool_pool import get_tool_pool, ToolPool
from .context_manager import get_workspace_context, WorkspaceContext
from .context_builder import analyze_context
from .policy_engine import get_policy_engine
from .unified_runtime import get_unified_runtime

# Compact integration
from .compact import (
    should_compact,
    get_compact_prompt,
    format_compact_summary,
    get_token_warning_level,
    COMPACT_THRESHOLD_TOKENS,
    COMPACT_WARNING_TOKENS,
)


class HarnessRuntime:
    """
    Main harness runtime. Inspired by Claude Code's session management.
    Coordinates tool execution, context, and cost tracking.
    Includes compact integration for long conversations.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.pool = get_tool_pool()
        self.context = get_workspace_context()
        self.cost = CostSummary()
        self.tool_uses: list[ToolUse] = []
        self.start_time = time.time()
        self.unified = get_unified_runtime(self.session_id)
        self.policy = get_policy_engine()
        self.last_model_decision = None
        self.last_policy_decision = None
        
        # Compact state
        self.token_count = 0
        self.message_count = 0
        self.compact_triggered = False
        self.messages: list[dict] = []
        
        # Build manifest
        tool_names = [t.name for t in self.pool.list_tools()]
        self.manifest = SessionManifest(
            session_id=self.session_id,
            tools=tool_names,
            context_files=self.context.analysis.code_files if self.context.analysis else 0,
            workspace_size_mb=self.context.analysis.total_size_mb if self.context.analysis else 0,
        )
    
    def execute_tool(self, tool_name: str, input_data: dict) -> ToolResult:
        """Execute a tool and track usage."""
        input_data = {**input_data, "session_id": self.session_id}
        use = ToolUse(
            tool_name=tool_name,
            input_data=input_data,
            tool_use_id=str(uuid.uuid4())[:8],
        )
        
        start = time.time()
        result = self.pool.execute(tool_name, input_data)
        duration = int((time.time() - start) * 1000)
        
        result.duration_ms = duration
        use.result = result
        self.tool_uses.append(use)
        
        return result
    
    def execute_sequence(self, operations: list[dict]) -> list[ToolResult]:
        """Execute a sequence of tool operations."""
        results = []
        for op in operations:
            tool_name = op.get("tool")
            input_data = op.get("input", {})
            results.append(self.execute_tool(tool_name, input_data))
        return results

    def orchestrate(self, plan: list[dict], stop_on_error: bool = True) -> dict:
        """Structured orchestration surface for multi-step tool plans."""
        results = []
        for idx, step in enumerate(plan, 1):
            result = self.execute_tool(step.get("tool", ""), step.get("input", {}))
            results.append({
                "step": idx,
                "tool": step.get("tool"),
                "success": result.success,
                "output": result.output,
                "error": result.error,
            })
            if stop_on_error and not result.success:
                break
        return {"steps": results, "completed": all(r["success"] for r in results)}

    def analyze_context(self, task: str = "") -> dict:
        return analyze_context(task)

    def decide_model(self, task: str = "") -> dict | None:
        policy = self.policy.evaluate(
            task=task,
            token_count=self.token_count,
            route_hint=None,
        )
        self.last_policy_decision = policy.to_dict()
        decision = self.unified.decide_model(task, token_count=self.token_count)
        self.last_model_decision = decision.to_dict()
        return self.last_model_decision

    def get_diagnostics(self, task: str = "") -> dict:
        return self.unified.diagnostics(
            task,
            token_count=self.token_count,
            recent_tools=[use.tool_name for use in self.tool_uses[-10:]],
        ).to_dict()

    def execute_task(self, task: str, *, prompt: Optional[str] = None, route_hint: Optional[str] = None) -> dict:
        result = self.unified.execute(task, prompt=prompt, token_count=self.token_count, route_hint=route_hint)
        return result.to_dict()
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.message_count = len(self.messages)
        
        # Estimate token count (rough: 4 chars per token)
        self.token_count = sum(len(m.get("content", "")) // 4 for m in self.messages)
    
    def check_compact(self) -> dict:
        """
        Check if compaction is needed.
        
        Returns:
            dict with keys:
                - needed: bool
                - level: 'ok' | 'warning' | 'critical'
                - threshold: int
                - current: int
                - prompt: str (compact prompt if needed)
        """
        level = get_token_warning_level(self.token_count)
        
        result = {
            "needed": should_compact(self.token_count),
            "level": level,
            "threshold": COMPACT_THRESHOLD_TOKENS,
            "current": self.token_count,
            "warning_threshold": COMPACT_WARNING_TOKENS,
            "prompt": None,
        }
        
        if result["needed"]:
            result["prompt"] = get_compact_prompt()
            self.compact_triggered = True
        
        return result
    
    def compact_and_continue(self, conversation_history: list[dict]) -> dict:
        """
        Compact the conversation history.
        
        Args:
            conversation_history: List of messages
            
        Returns:
            dict with:
                - summary: str (formatted compact summary)
                - prompt: str (to inject into context)
                - original_count: int (original message count)
                - compacted: bool
        """
        # Build raw summary from conversation
        raw_summary = self._build_raw_summary(conversation_history)
        
        # Format
        formatted = format_compact_summary(raw_summary)
        
        # Create injection prompt
        injection = get_compact_prompt() + "\n\n" + formatted
        
        return {
            "summary": formatted,
            "prompt": injection,
            "original_count": len(conversation_history),
            "compacted": True,
            "token_saved": self.token_count - len(formatted) // 4,
        }
    
    def _build_raw_summary(self, messages: list[dict]) -> str:
        """Build raw summary text from messages."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{role}]: {content[:500]}")
        
        return "\n\n".join(lines)
    
    def run_turn(self, prompt: str) -> dict:
        """
        Run a single turn. Returns result with context.
        Inspired by Claude Code's turn loop.
        """
        turn_start = time.time()
        
        # Add user message
        self.add_message("user", prompt)
        
        # Check compact
        compact_info = self.check_compact()
        
        # Decide model before tool routing
        self.decide_model(prompt)

        # Route prompt to tools (simplified routing)
        operations = self._route_to_tools(prompt)
        
        # Execute
        results = self.execute_sequence(operations)
        
        # Build response
        turn_duration = int((time.time() - turn_start) * 1000)
        
        return {
            "session_id": self.session_id,
            "prompt": prompt,
            "operations": len(operations),
            "results": [r.__dict__ for r in results],
            "duration_ms": turn_duration,
            "manifest": self.manifest.to_dict(),
            "compact": compact_info,
            "token_count": self.token_count,
            "message_count": self.message_count,
            "model_decision": self.last_model_decision,
            "execution": self.unified.last_execution,
            "diagnostics": self.get_diagnostics(prompt),
        }
    
    def _route_to_tools(self, prompt: str) -> list[dict]:
        """Simple routing from prompt to tool operations."""
        operations = []
        prompt_lower = prompt.lower()
        
        # Bash
        if any(k in prompt_lower for k in ['bash', 'çalıştır', 'run ', 'command']):
            operations.append({
                "tool": "Bash",
                "input": {"command": prompt}
            })
        
        # Read
        if any(k in prompt_lower for k in ['read', 'oku', 'dosya']):
            operations.append({
                "tool": "Read",
                "input": {"path": prompt.split()[-1]}
            })
        
        # Think
        if any(k in prompt_lower for k in ['think', 'düşün', 'analiz']):
            operations.append({
                "tool": "Think",
                "input": {"thought": prompt}
            })
        
        return operations
    
    def get_summary(self) -> str:
        """Get runtime summary."""
        self.cost.wall_duration_ms = int((time.time() - self.start_time) * 1000)
        
        lines = [
            f"Session: {self.session_id}",
            f"Duration: {self.cost.wall_duration_ms/1000:.1f}s",
            f"Tool uses: {len(self.tool_uses)}",
            f"Messages: {self.message_count}",
            f"Tokens (est): {self.token_count:,}",
            f"Compact triggered: {self.compact_triggered}",
            f"Cost: ${self.cost.total_cost_usd:.4f}",
            "",
            self.cost.format(),
        ]
        
        return '\n'.join(lines)
    
    def to_dict(self) -> dict:
        """Export session as dict."""
        return {
            "session_id": self.session_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "manifest": self.manifest.to_dict(),
            "tool_uses": [u.__dict__ for u in self.tool_uses],
            "message_count": self.message_count,
            "token_count": self.token_count,
            "compact_triggered": self.compact_triggered,
            "last_model_decision": self.last_model_decision,
            "last_policy_decision": self.last_policy_decision,
            "diagnostics": self.get_diagnostics(),
            "cost": {
                "total_cost_usd": self.cost.total_cost_usd,
                "total_input_tokens": self.cost.total_input_tokens,
                "total_output_tokens": self.cost.total_output_tokens,
            },
        }


# Factory function
def create_runtime(session_id: Optional[str] = None) -> HarnessRuntime:
    """Create a new harness runtime."""
    return HarnessRuntime(session_id)


# Convenience function
def run_turn(prompt: str) -> dict:
    """Run a single turn with a new runtime."""
    runtime = create_runtime()
    return runtime.run_turn(prompt)
