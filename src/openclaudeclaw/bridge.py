"""
Harness Bridge — OpenClaw ↔ Harness Entegrasyonu
─────────────────────────────────────────────────
Mevcut OpenClaw sistemini harness mimarisiyle birleştirir.

Kullanım:
    from src.harness.bridge import harness_bridge
    
    result = harness_bridge.analyze("Ne yapmam gerekiyor?")
    print(result)
"""

import sys
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))

from src.harness.tool_pool import get_tool_pool, ToolPool
from src.harness.runtime import HarnessRuntime
from src.harness.context_manager import get_workspace_context, format_context_prompt


class HarnessBridge:
    """
    OpenClaw ile Harness arasındaki köprü.
    Mevcut sistemle uyumlu çalışır.
    """
    
    def __init__(self):
        self.pool = get_tool_pool()
        self.runtime: Optional[HarnessRuntime] = None
    
    def start_session(self, session_id: Optional[str] = None) -> HarnessRuntime:
        """Yeni bir harness session başlat."""
        self.runtime = HarnessRuntime(session_id)
        return self.runtime
    
    def get_context(self) -> str:
        """Workspace context'ini döndür."""
        context = get_workspace_context()
        return format_context_prompt(context)
    
    def execute(self, tool_name: str, input_data: dict) -> dict:
        """Tool çalıştır ve sonucu döndür."""
        if not self.runtime:
            self.start_session()
        
        result = self.runtime.execute_tool(tool_name, input_data)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
        }
    
    def analyze(self, prompt: str) -> dict:
        """Prompt'ı analiz et, tool öner."""
        tools = self.pool.list_tools()
        
        prompt_lower = prompt.lower()
        suggestions = []
        
        for tool in tools:
            # Pattern matching
            for pattern in tool.patterns:
                if pattern.lower() in prompt_lower:
                    suggestions.append({
                        "tool": tool.name,
                        "category": tool.category.value,
                        "pattern": pattern,
                        "readonly": tool.readonly,
                    })
                    break
        
        return {
            "prompt": prompt,
            "suggestions": suggestions,
            "tool_count": len(tools),
        }
    
    def get_tool_info(self, name: str) -> Optional[dict]:
        """Tool bilgisi getir."""
        tool = self.pool.get(name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category.value,
            "patterns": tool.patterns,
            "readonly": tool.readonly,
        }
    
    def list_by_category(self) -> dict:
        """Tool'ları kategoriye göre listele."""
        tools = self.pool.list_tools()
        by_category = {}
        
        for tool in tools:
            cat = tool.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "name": tool.name,
                "readonly": tool.readonly,
            })
        
        return by_category


# Global bridge instance
_bridge: Optional[HarnessBridge] = None


def get_bridge() -> HarnessBridge:
    """Global bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = HarnessBridge()
    return _bridge


# Convenience functions
def analyze(prompt: str) -> dict:
    """Prompt analiz et."""
    return get_bridge().analyze(prompt)


def execute(tool_name: str, input_data: dict) -> dict:
    """Tool çalıştır."""
    return get_bridge().execute(tool_name, input_data)


def context() -> str:
    """Workspace context getir."""
    return get_bridge().get_context()


if __name__ == "__main__":
    # Test
    print("=== HARNESS BRIDGE TEST ===")
    
    bridge = get_bridge()
    
    # Context
    print("\n1. Workspace Context:")
    print(bridge.get_context()[:200] + "...")
    
    # Analyze
    print("\n2. Analyze 'read a file':")
    result = bridge.analyze("read a file")
    print(f"   Suggestions: {len(result['suggestions'])}")
    for s in result['suggestions']:
        print(f"   - [{s['category']}] {s['tool']}")
    
    # List by category
    print("\n3. Tools by category:")
    cats = bridge.list_by_category()
    for cat, tools in cats.items():
        print(f"   {cat}: {', '.join(t['name'] for t in tools)}")
    
    print("\n=== TEST COMPLETE ===")
