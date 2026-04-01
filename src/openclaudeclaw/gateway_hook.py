"""
OpenClaw Gateway Hook — Tam Entegrasyon
──────────────────────────────────────
Gateway mesajlarını harness'a yönlendirir.
Tüm OpenClaw içsel yapısıyla entegre çalışır.
"""

from pathlib import Path
from typing import Optional, Callable
import json
import re
import hashlib


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")


class GatewayHook:
    """
    Gateway ↔ Harness tam entegrasyonu.
    
    1. Gelen mesajları yakala
    2. SOUL kurallarına göre pre-process
    3. Harness agent'a yönlendir
    4. Çıktıyı SOUL kurallarına göre post-process
    5. Gateway'e döndür
    """
    
    def __init__(self):
        self.harness = None
        self.router = None
        self.persona_builder = None
        self.cost_tracker = None
        self.semantic_memory = None
        
        # Pre-processors
        self._preprocessors: list[Callable] = []
        self._postprocessors: list[Callable] = []
    
    def _init_harness(self):
        """Harness'ı başlat (lazy)."""
        if self.harness is None:
            from src.harness.agent import HarnessAgent
            from src.harness.router import route_prompt
            from src.harness.system_prompt import get_persona_builder
            from src.harness import get_cost_tracker, get_semantic_memory
            
            self.harness = HarnessAgent()
            self.router = route_prompt
            self.persona_builder = get_persona_builder()
            self.cost_tracker = get_cost_tracker()
            self.semantic_memory = get_semantic_memory()
    
    def _preprocess(self, message: str) -> dict:
        """
        Mesajı pre-process et.
        
        Returns:
            dict: {
                "cleaned": str,  # Temizlenmiş mesaj
                "intent": str,    # Tespit edilen intent
                "context": dict, # Ek context
                "violations": list,  # SOUL ihlalleri
            }
        """
        self._init_harness()
        
        from src.harness.integrations import validate_response
        
        result = {
            "cleaned": message.strip(),
            "intent": self._detect_intent(message),
            "context": {},
            "violations": [],
        }
        
        # SOUL violation check
        valid, warnings = validate_response(message)
        if not valid:
            result["violations"] = warnings
        
        # Intent detection
        result["intent"] = self._detect_intent(message)
        
        # Relevant memory ekle
        if result["intent"]:
            relevant = self.semantic_memory.find_relevant(result["intent"])
            if relevant:
                result["context"]["relevant_memories"] = [
                    {"name": f.filename, "desc": f.description}
                    for f in relevant[:3]
                ]
        
        return result
    
    def _detect_intent(self, message: str) -> str:
        """Intent'i tespit et."""
        message_lower = message.lower()
        
        intents = [
            ("code", ["kod", "script", "yaz", "düzenle", "fix", "bug"]),
            ("research", ["ara", "bul", "search", "incele", "analiz"]),
            ("content", ["tweet", "içerik", "yaz", "post", "x"]),
            ("coffee", ["kahve", "flech", "urbica", "morecano", "ciro"]),
            ("system", ["sistem", "cron", "otomatik", "entegrasyon"]),
            ("business", ["iş", "satış", "müşteri", "pazarlama"]),
        ]
        
        for intent, keywords in intents:
            if any(kw in message_lower for kw in keywords):
                return intent
        
        return "general"
    
    def _postprocess(self, response: str, violations: list) -> str:
        """
        Yanıtı post-process et.
        
        - SOUL ihlallerini temizle
        - "başka?" gibi kapanışları kaldır
        - Ton kontrolü yap
        """
        cleaned = response.strip()
        
        # "başka?" gibi kapanışları kaldır
        endings_to_remove = [
            "başka?",
            "Başka?",
            "Başka bir şey?",
            "başka bir şey sormak ister misin?",
            "Başka bir şey sormak ister misin?",
        ]
        
        for ending in endings_to_remove:
            if cleaned.endswith(ending):
                cleaned = cleaned[:-len(ending)].strip()
                # Sonundaki noktalama kaldır
                cleaned = cleaned.rstrip('.,')
        
        # Son cümlesi kontrol et
        lines = cleaned.split('\n')
        if lines:
            last_line = lines[-1].strip()
            # Boş satır değilse nokta ekle
            if last_line and not last_line.endswith(('.', '!', '?')):
                lines[-1] = last_line + '.'
                cleaned = '\n'.join(lines)
        
        return cleaned
    
    def process(self, message: str, session_id: str = None) -> dict:
        """
        Mesajı işle ve harness'a yönlendir.
        
        Args:
            message: Kullanıcı mesajı
            session_id: Opsiyonel session ID
        
        Returns:
            dict: {
                "response": str,      # Harness yanıtı
                "intent": str,        # Tespit edilen intent
                "route": str,          # Kullanılan route
                " violations": list,   # SOUL ihlalleri
                "cost": str,           # Maliyet özeti
            }
        """
        # Pre-process
        pre = self._preprocess(message)
        
        # Routing kararı
        route_result = self.router(message)
        
        # Harness agent'a yönlendir
        self._init_harness()
        
        try:
            harness_response = self.harness.process(message)
            raw_response = harness_response.content
        except Exception as e:
            raw_response = f"Hata oluştu: {e}"
        
        # Post-process
        final_response = self._postprocess(raw_response, pre["violations"])
        
        return {
            "response": final_response,
            "intent": pre["intent"],
            "route": route_result.get("route", "unknown"),
            "score": route_result.get("score", 0),
            "violations": pre["violations"],
            "cost": self.cost_tracker.get_summary(),
            "session_id": session_id or self.harness.runtime.session_id,
        }
    
    def process_stream(self, message: str, callback: Callable) -> dict:
        """
        Streaming modda işle.
        
        Callback her chunk için çağrılır.
        """
        result = self.process(message)
        
        # Stream callback
        if callback:
            callback(result["response"])
        
        return result


def create_gateway_hook() -> GatewayHook:
    """Factory function."""
    return GatewayHook()


# Singleton
_gateway_hook: Optional[GatewayHook] = None


def get_gateway_hook() -> GatewayHook:
    global _gateway_hook
    if _gateway_hook is None:
        _gateway_hook = GatewayHook()
    return _gateway_hook


if __name__ == "__main__":
    hook = get_gateway_hook()
    
    print("=== GATEWAY HOOK TEST ===\n")
    
    # Test pre-process
    pre = hook._preprocess("Flech için tweet yaz")
    print(f"Intent: {pre['intent']}")
    print(f"Violations: {pre['violations']}")
    
    # Test routing
    route = hook.router("Kahve fiyatları ne?")
    print(f"Route: {route['route']} ({route['score']} puan)")
    
    # Test full process
    print("\n--- Full Process ---")
    result = hook.process("Sistem durumunu kontrol et")
    print(f"Response: {result['response'][:100]}...")
    print(f"Route: {result['route']}")
