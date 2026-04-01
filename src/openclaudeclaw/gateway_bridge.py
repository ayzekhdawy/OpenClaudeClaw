"""
Gateway Bridge — OpenClaw Gateway ↔ Harness Entegrasyonu
───────────────────────────────────────────────────────
OpenClaw gateway'ine harness agent'ı entegre eder.

Bu hook, gateway'e gelen mesajları harness agent'a yönlendirir.
"""

import sys
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))

from src.harness.agent import HarnessAgent, create_agent
from src.harness.context_builder import build_context


# Global agent instance
_agent: Optional[HarnessAgent] = None


def get_agent() -> HarnessAgent:
    """Global harness agent."""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def process_message(message: str, context: dict = None) -> dict:
    """
    Gateway'den gelen mesajı işle.
    
    Args:
        message: Kullanıcı mesajı
        context: Ek context (user_id, chat_id, vs.)
    
    Returns:
        dict: {
            "content": str - Yanıt,
            "route": str - Kullanılan route,
            "tools": list - Kullanılan tool'lar,
            "context": list - Kullanılan context'ler
        }
    """
    agent = get_agent()
    
    # Process with harness agent
    response = agent.process(message)
    
    return {
        "content": response.content,
        "route": response.route,
        "tools": response.tools_used,
        "context": response.context_used,
        "warnings": response.warnings,
        "session_id": response.session_id,
    }


def get_system_status() -> dict:
    """Sistem durumunu döndür."""
    agent = get_agent()
    return agent.get_status()


def get_full_context(task: str = "") -> str:
    """Tam context prompt'u döndür."""
    ctx = build_context(task=task)
    return ctx.full_prompt


# Gateway hook function
async def on_message(message: str, metadata: dict = None) -> str:
    """
    Gateway message hook.
    
    Bu fonksiyon gateway tarafından çağrılır.
    """
    result = process_message(message, metadata)
    
    # Check for warnings
    if result.get("warnings"):
        # Log warnings but don't expose to user
        pass
    
    return result["content"]


# For testing
if __name__ == "__main__":
    print("=== GATEWAY BRIDGE TEST ===\n")
    
    # Test message processing
    tests = [
        "Merhaba",
        "Flech için tweet hazırla",
        "Python script yaz",
    ]
    
    for msg in tests:
        print(f">>> {msg}")
        result = process_message(msg)
        print(f"    Route: {result['route']}")
        print(f"    Tools: {result['tools']}")
        print(f"    Response: {result['content']}")
        print()
    
    # System status
    print("=== System Status ===")
    status = get_system_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
