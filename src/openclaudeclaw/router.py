"""
Harness Router — Routing + Tool System Entegrasyonu
───────────────────────────────────────────────────
OpenClaw Router v2 + Claude Code Harness Patterns

Bu modül router'ı harness tool system ile birleştirir.
Harness'in tool yeteneklerini routing kararlarına entegre eder.
"""

import sys
from pathlib import Path

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))

from scripts.router import route_prompt, ROUTING_RULES
from src.harness.bridge import HarnessBridge


class HarnessRouter:
    """
    Routing + Tool System Entegrasyonu.
    
    Routing kararı verdikten sonra harness tool'larını kullanarak
    işlemi gerçekleştirir.
    """
    
    def __init__(self):
        self.bridge = HarnessBridge()
        self.router = None  # Routing sonucu
    
    def route_and_execute(self, prompt: str) -> dict:
        """
        Prompt'u route et ve harness ile çalıştır.
        
        1. Routing kararı al
        2. Uygun tool'ları belirle
        3. Tool'ları çalıştır
        4. Sonucu döndür
        """
        # 1. Routing kararı
        route_result = route_prompt(prompt, explain=False)
        self.router = route_result
        
        # 2. Harness analyze
        tool_suggestions = self.bridge.analyze(prompt)
        
        # 3. Execute (eğer uygunsa)
        executed = []
        
        if tool_suggestions["suggestions"]:
            for suggestion in tool_suggestions["suggestions"][:2]:  # Max 2 tool
                tool_name = suggestion["tool"]
                
                # Built-in tool mapping
                if tool_name == "Think" and "think" in prompt.lower():
                    result = self.bridge.execute("Think", {"thought": prompt})
                    executed.append({
                        "tool": tool_name,
                        **result
                    })
        
        return {
            "route": route_result,
            "tools": tool_suggestions["suggestions"],
            "executed": executed,
        }
    
    def get_context_for_route(self, route: str) -> str:
        """Route için uygun context'i döndür."""
        if route in ["code", "gitnexus"]:
            # Workspace context gerekli
            return self.bridge.get_context()
        elif route in ["searxng", "research"]:
            # Intel folder context
            intel_path = WORKSPACE / "intel"
            if intel_path.exists():
                return f"Intel folder: {list(intel_path.glob('*.md'))[:5]}"
        elif route in ["esra", "ollama"]:
            # Minimal context
            return ""
        
        return ""
    
    def suggest_next_action(self, route_result: dict) -> str:
        """Routing sonucuna göre sonraki aksiyonu öner."""
        route = route_result.get("route", "ollama")
        score = route_result.get("score", 10)
        
        if score >= 100:
            return "GitHub URL tespit edildi → otomatik clone + analyze"
        elif route == "code":
            return "Claude Code ile kod yazma/düzeltme başlat"
        elif route == "searxng":
            return "SEARXNG araştırması başlat"
        elif route == "esra":
            return "Esra context ile yanıt hazırla"
        else:
            return "Ollama ile devam et"


def route_harness(prompt: str) -> dict:
    """Convenience function."""
    router = HarnessRouter()
    return router.route_and_execute(prompt)


if __name__ == "__main__":
    # Test
    print("=== HARNESS ROUTER TEST ===\n")
    
    router = HarnessRouter()
    
    test_prompts = [
        "github.com/instructkr/claude-code",
        "Python script yaz",
        "Flech markası için içerik hazırla",
        "think about recursion",
    ]
    
    for prompt in test_prompts:
        result = router.route_and_execute(prompt)
        print(f"Prompt: {prompt[:40]}...")
        print(f"  Route: {result['route']['route']} ({result['route']['score']})")
        print(f"  Tools: {[t['tool'] for t in result['tools']]}")
        print()
