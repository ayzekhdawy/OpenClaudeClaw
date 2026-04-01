"""
Harness Agent Loop — OpenClaw Main Agent
────────────────────────────────────────
Harness tabanlı ana agent döngüsü.
OpenClaw'un tüm içsel yapılarını entegre eder.

Bu agent şunu yapar:
1. SOUL.md → Persona kuralları
2. MEMORY.md → Hafıza + görev context
3. USER.md → İshak profili
4. Workspace → Dosya analizi
5. Tool Pool → Otomatik tool seçimi
6. Routing → Doğru yönlendirme
7. Extract Memories → Session sonunda memory kaydetme
8. Compact → Context dolunca özetleme
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))

from src.harness.tool_pool import get_tool_pool
from src.harness.runtime import HarnessRuntime
from src.harness.context_manager import get_workspace_context
from src.harness.integrations import (
    get_soul_adapter,
    get_memory_adapter,
    get_user_adapter,
)
from src.harness.context_builder import build_context, validate_and_sanitize
from src.harness.router import route_prompt
from src.harness.session_memory import get_session_memory
from src.harness.memory_fabric import get_memory_fabric

# Extract Memories integration
from src.harness.extract_memories import (
    build_extract_prompt,
    get_existing_memories,
    should_extract,
    reset_extraction_state,
)

# Compact integration
from src.harness.compact import (
    should_compact,
    get_compact_prompt,
    COMPACT_THRESHOLD_TOKENS,
)


@dataclass
class AgentResponse:
    """Agent'ın yanıtı."""
    content: str
    route: str
    tools_used: list[str]
    context_used: list[str]
    warnings: list[str]
    session_id: str
    compact_triggered: bool = False
    memory_extracted: bool = False


class HarnessAgent:
    """
    OpenClaw Harness Agent.
    Tüm içsel yapıları entegre eder.
    
    Hooks:
    - after_turn: Turn sonunda çalışır
    - on_compact: Context dolunca çalışır
    - on_session_end: Session sonunda çalışır
    """
    
    def __init__(self):
        self.soul = get_soul_adapter()
        self.memory = get_memory_adapter()
        self.user = get_user_adapter()
        self.pool = get_tool_pool()
        self.runtime = HarnessRuntime()
        self.session_memory = get_session_memory(self.runtime.session_id)
        self.memory_fabric = get_memory_fabric(self.runtime.session_id)
        self.session_memory.create_notes(f"Harness Session {self.runtime.session_id}")
        
        # Turn/message tracking
        self.messages: list[dict] = []
        self.turn_count = 0
        
        # Hooks
        self.after_turn_hook: Optional[Callable] = None
        self.on_compact_hook: Optional[Callable] = None
        self.on_session_end_hook: Optional[Callable] = None
    
    def process(self, message: str) -> AgentResponse:
        """
        Mesajı işle.
        
        1. Routing kararı al
        2. Context oluştur
        3. SOUL kurallarını uygula
        4. Response üret
        5. Validate et
        6. Hooks çalıştır
        """
        warnings = []
        
        # Track message
        self.turn_count += 1
        self.messages.append({
            "role": "user",
            "content": message,
            "turn": self.turn_count,
            "timestamp": time.time(),
        })
        
        # 1. Route
        route_result = route_prompt(message)
        route = route_result.get("route", "ollama")
        
        # 2. Build context
        context = build_context(task=message)
        surfaced_memory_context = self.memory_fabric.build_context(message)

        # 2.5 Unified model decision
        self.runtime.decide_model(message)
        
        # 3. Analyze with tool pool
        tool_suggestions = self.pool.search(message.lower())
        
        # 4. Check SOUL violations
        violation = self.soul.check_violation(message)
        if violation:
            warnings.append(violation)
        
        # 5. Get user preferences
        user_name = self.user.get_user_name()
        comm_style = self.user.get_communication_style()
        
        # 6. Execute relevant tools
        tools_used = []
        tool_results = []
        
        for suggestion in tool_suggestions[:2]:
            tool_name = suggestion.name
            result = self.runtime.execute_tool(tool_name, {"input": message})
            if result.success:
                tools_used.append(tool_name)
                tool_results.append(result.output)
        
        # 7. Build response
        content = self._generate_response(
            message=message,
            route=route,
            context=context,
            tool_results=tool_results,
            user_name=user_name,
        )
        
        # 8. Validate response
        content, response_warnings = validate_and_sanitize(content)
        warnings.extend(response_warnings)
        
        # Track assistant message
        self.messages.append({
            "role": "assistant",
            "content": content,
            "turn": self.turn_count,
            "timestamp": time.time(),
        })
        
        # 9. Update runtime
        self.runtime.add_message("user", message)
        self.runtime.add_message("assistant", content)
        self._sync_session_notes(message, content, route, tools_used)
        if surfaced_memory_context:
            self.session_memory.update_notes("Files and Functions", surfaced_memory_context[:1500])
        
        # 10. Check for compact
        compact_triggered = False
        if should_compact(self.runtime.token_count):
            compact_triggered = True
            if self.on_compact_hook:
                self.on_compact_hook(self.messages)
        
        # 11. Check for memory extraction
        memory_extracted = False
        if should_extract(len(self.messages)):
            memory_extracted = True
            if self.on_session_end_hook:
                self.on_session_end_hook(self.messages)
        
        # 12. After turn hook
        if self.after_turn_hook:
            self.after_turn_hook(self.messages[-2:], self.turn_count)
        
        return AgentResponse(
            content=content,
            route=route,
            tools_used=tools_used,
            context_used=["soul", "memory", "user", "workspace"],
            warnings=warnings,
            session_id=self.runtime.session_id,
            compact_triggered=compact_triggered,
            memory_extracted=memory_extracted,
        )

    def _sync_session_notes(self, message: str, content: str, route: str, tools_used: list[str]):
        """Minimum session memory integration."""
        try:
            current = f"Route: {route}\nLast user message: {message[:300]}\nLast response: {content[:300]}"
            self.session_memory.update_notes("Current State", current)
            self.session_memory.update_notes("Task specification", message[:1200])
            self.session_memory.update_notes("Worklog", f"Turn {self.turn_count}: route={route}, tools={', '.join(tools_used) or 'none'}\n")
        except Exception:
            pass
    
    def extract_memories_async(self) -> dict:
        """
        Memory extraction tetikle.
        
        Returns:
            dict with:
                - prompt: str (LLM'e gönderilecek prompt)
                - message_count: int (kullanılan mesaj sayısı)
                - existing_memories: str (mevcut MEMORY.md içeriği)
        """
        existing = get_existing_memories()
        prompt = build_extract_prompt(
            new_message_count=len(self.messages),
            existing_memories=existing,
            skip_index=False,
        )
        
        return {
            "prompt": prompt,
            "message_count": len(self.messages),
            "existing_memories": existing,
            "ready": True,
        }
    
    def get_compact_trigger(self) -> dict:
        """
        Compact gerekli mi kontrol et.
        
        Returns:
            dict with compact status and prompt if needed
        """
        token_count = self.runtime.token_count
        needed = should_compact(token_count)
        
        result = {
            "needed": needed,
            "token_count": token_count,
            "threshold": COMPACT_THRESHOLD_TOKENS,
            "message_count": len(self.messages),
            "prompt": None,
        }
        
        if needed:
            result["prompt"] = get_compact_prompt()
        
        return result
    
    def run_compact(self) -> dict:
        """
        Manuel compact tetikle.
        
        Returns:
            dict with summary and injection prompt
        """
        return self.runtime.compact_and_continue(self.messages)
    
    def get_extract_prompt(self) -> str:
        """Memory extraction prompt döndür."""
        existing = get_existing_memories()
        return build_extract_prompt(
            new_message_count=len(self.messages),
            existing_memories=existing,
            skip_index=False,
        )
    
    def end_session(self) -> dict:
        """
        Session'ı sonlandır.
        
        Memory extraction otomatik çalışır.
        """
        result = {
            "session_id": self.runtime.session_id,
            "turn_count": self.turn_count,
            "message_count": len(self.messages),
            "extraction_ready": should_extract(len(self.messages)),
        }
        
        if result["extraction_ready"]:
            result["extraction_prompt"] = self.get_extract_prompt()
        
        # Reset state
        reset_extraction_state()
        
        return result
    
    def _generate_response(
        self,
        message: str,
        route: str,
        context,
        tool_results: list[str],
        user_name: str,
    ) -> str:
        """
        Response üret.
        
        Gerçek implementasyonda LLM çağrısı olur.
        Şimdilik simple simulation.
        """
        # Route-based response
        if route == "code":
            return f"Anladım, kod yazıyorum. {len(tool_results)} tool kullandım."
        elif route == "searxng":
            return f"Araştırıyorum... {len(tool_results)} sonuç buldum."
        elif route == "esra":
            return f"{user_name}, mesajını aldım. İşliyorum."
        else:
            return f"Merhaba {user_name}, nasıl yardımcı olabilirim?"
    
    def get_status(self) -> dict:
        """Agent durumunu döndür."""
        return {
            "session_id": self.runtime.session_id,
            "turn_count": self.turn_count,
            "message_count": len(self.messages),
            "token_count": self.runtime.token_count,
            "model_decision": self.runtime.last_model_decision,
            "runtime_diagnostics": self.runtime.get_diagnostics(),
            "tools_available": len(self.pool.list_tools()),
            "soul_rules": len(self.soul.load().get('never', [])),
            "memory_entries": len(self.memory.load_memory().get('critical', [])),
            "user_name": self.user.get_user_name(),
            "compact_needed": should_compact(self.runtime.token_count),
            "extraction_ready": should_extract(len(self.messages)),
            "session_notes_path": str(self.session_memory.get_notes_path()),
        }
    
    def set_after_turn_hook(self, hook: Callable):
        """Turn sonrası hook ayarla."""
        self.after_turn_hook = hook
    
    def set_on_compact_hook(self, hook: Callable):
        """Compact hook ayarla."""
        self.on_compact_hook = hook
    
    def set_on_session_end_hook(self, hook: Callable):
        """Session sonu hook ayarla."""
        self.on_session_end_hook = hook


def create_agent() -> HarnessAgent:
    """Agent factory."""
    return HarnessAgent()


if __name__ == "__main__":
    print("=== HARNESS AGENT TEST ===\n")
    
    agent = create_agent()
    
    # Status
    print("Agent Status:")
    status = agent.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    # Test messages
    print("\n--- Message Tests ---")
    
    tests = [
        "Flech için içerik hazırla",
        "Python script yaz",
        "Github'da bir repo ara",
        "think about recursion",
    ]
    
    for msg in tests:
        print(f"\nInput: {msg}")
        resp = agent.process(msg)
        print(f"  Route: {resp.route}")
        print(f"  Tools: {resp.tools_used}")
        print(f"  Response: {resp.content}")
        print(f"  Compact: {resp.compact_triggered}")
        print(f"  Memory Extracted: {resp.memory_extracted}")
        if resp.warnings:
            print(f"  Warnings: {resp.warnings}")
    
    # Test extract
    print("\n--- Extract Memories ---")
    if should_extract(len(agent.messages)):
        prompt = agent.get_extract_prompt()
        print(f"Prompt length: {len(prompt)} chars")
    
    # Test compact
    print("\n--- Compact Check ---")
    compact = agent.get_compact_trigger()
    print(f"Compact needed: {compact['needed']}")
    print(f"Token count: {compact['token_count']}")
    print(f"Threshold: {compact['threshold']}")
    
    # End session
    print("\n--- End Session ---")
    result = agent.end_session()
    print(f"Session ended: {result['session_id']}")
    print(f"Turns: {result['turn_count']}")
    print(f"Extraction ready: {result['extraction_ready']}")
