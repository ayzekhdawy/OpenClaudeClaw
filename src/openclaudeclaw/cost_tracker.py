"""
Cost Tracker — Claude Code cost-tracker.ts referansı
──────────────────────────────────────────────────
Session bazlı maliyet takibi, model usage, cache tracking.
"""

from pathlib import Path
from typing import Optional, TypedDict
from datetime import datetime
import json
import os


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
COST_DIR = WORKSPACE / ".costs"


class ModelUsage(TypedDict):
    """Model başına usage bilgisi."""
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float
    requests: int


class CostState:
    """Maliyet durumu."""
    def __init__(self):
        self.total_cost_usd: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cache_read_tokens: int = 0
        self.total_cache_creation_tokens: int = 0
        self.total_lines_added: int = 0
        self.total_lines_removed: int = 0
        self.total_api_duration_ms: int = 0
        self.total_api_duration_no_retry_ms: int = 0
        self.total_tool_duration_ms: int = 0
        self.total_web_search_requests: int = 0
        self.model_usage: dict[str, ModelUsage] = {}
        self.has_unknown_model_cost: bool = False
    
    def to_dict(self) -> dict:
        return {
            "total_cost_usd": self.total_cost_usd,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_cache_creation_tokens": self.total_cache_creation_tokens,
            "total_lines_added": self.total_lines_added,
            "total_lines_removed": self.total_lines_removed,
            "total_api_duration_ms": self.total_api_duration_ms,
            "total_api_duration_no_retry_ms": self.total_api_duration_no_retry_ms,
            "total_tool_duration_ms": self.total_tool_duration_ms,
            "total_web_search_requests": self.total_web_search_requests,
            "model_usage": self.model_usage,
            "has_unknown_model_cost": self.has_unknown_model_cost,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CostState":
        state = cls()
        state.total_cost_usd = data.get("total_cost_usd", 0.0)
        state.total_input_tokens = data.get("total_input_tokens", 0)
        state.total_output_tokens = data.get("total_output_tokens", 0)
        state.total_cache_read_tokens = data.get("total_cache_read_tokens", 0)
        state.total_cache_creation_tokens = data.get("total_cache_creation_tokens", 0)
        state.total_lines_added = data.get("total_lines_added", 0)
        state.total_lines_removed = data.get("total_lines_removed", 0)
        state.total_api_duration_ms = data.get("total_api_duration_ms", 0)
        state.total_api_duration_no_retry_ms = data.get("total_api_duration_no_retry_ms", 0)
        state.total_tool_duration_ms = data.get("total_tool_duration_ms", 0)
        state.total_web_search_requests = data.get("total_web_search_requests", 0)
        state.model_usage = data.get("model_usage", {})
        state.has_unknown_model_cost = data.get("has_unknown_model_cost", False)
        return state


class CostTracker:
    """
    Detaylı maliyet takibi.
    Claude Code'un cost-tracker.ts sistemine benzer.
    """
    
    # Model fiyatları (yaklaşık, Claude için)
    MODEL_COSTS = {
        "claude-3-5-sonnet-20241022": {
            "input_per_1k": 3.0,  # $3/1M input
            "output_per_1k": 15.0,  # $15/1M output
            "cache_read_per_1k": 0.30,  # $0.30/1M cached
            "cache_creation_per_1k": 3.0,  # $3/1M cache creation
        },
        "claude-3-5-haiku-20241022": {
            "input_per_1k": 0.80,
            "output_per_1k": 4.0,
            "cache_read_per_1k": 0.08,
            "cache_creation_per_1k": 0.80,
        },
        "minimax-m2.7": {
            "input_per_1k": 0.0,
            "output_per_1k": 0.0,
            "cache_read_per_1k": 0.0,
            "cache_creation_per_1k": 0.0,
        },
        "default": {
            "input_per_1k": 0.0,
            "output_per_1k": 0.0,
            "cache_read_per_1k": 0.0,
            "cache_creation_per_1k": 0.0,
        },
    }
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.state = CostState()
        self.cost_dir = COST_DIR
        self.cost_dir.mkdir(parents=True, exist_ok=True)
        
        # Session maliyetlerini yükle
        self._load_session_costs()
    
    def _generate_session_id(self) -> str:
        """Yeni session ID oluştur."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_session_file(self) -> Path:
        """Session maliyet dosyasını getir."""
        return self.cost_dir / f"session_{self.session_id}.json"
    
    def _load_session_costs(self):
        """Session maliyetlerini dosyadan yükle."""
        session_file = self._get_session_file()
        
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text())
                self.state = CostState.from_dict(data)
            except Exception:
                pass
    
    def _save_session_costs(self):
        """Session maliyetlerini dosyaya kaydet."""
        session_file = self._get_session_file()
        session_file.write_text(json.dumps(self.state.to_dict(), indent=2))
    
    def add_usage(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        duration_ms: int = 0,
    ):
        """Usage ekle ve maliyeti hesapla."""
        # Model maliyetini al
        costs = self.MODEL_COSTS.get(model, self.MODEL_COSTS["default"])
        
        # Maliyet hesapla
        input_cost = (input_tokens / 1000) * costs["input_per_1k"]
        output_cost = (output_tokens / 1000) * costs["output_per_1k"]
        cache_read_cost = (cache_read_tokens / 1000) * costs["cache_read_per_1k"]
        cache_creation_cost = (cache_creation_tokens / 1000) * costs["cache_creation_per_1k"]
        
        total_cost = input_cost + output_cost + cache_read_cost + cache_creation_cost
        
        # State'e ekle
        self.state.total_cost_usd += total_cost
        self.state.total_input_tokens += input_tokens
        self.state.total_output_tokens += output_tokens
        self.state.total_cache_read_tokens += cache_read_tokens
        self.state.total_cache_creation_tokens += cache_creation_tokens
        self.state.total_api_duration_ms += duration_ms
        
        # Model bazlı
        if model not in self.state.model_usage:
            self.state.model_usage[model] = ModelUsage(
                input_tokens=0,
                output_tokens=0,
                cache_read_tokens=0,
                cache_creation_tokens=0,
                cost_usd=0.0,
                requests=0,
            )
        
        usage = self.state.model_usage[model]
        usage["input_tokens"] += input_tokens
        usage["output_tokens"] += output_tokens
        usage["cache_read_tokens"] += cache_read_tokens
        usage["cache_creation_tokens"] += cache_creation_tokens
        usage["cost_usd"] += total_cost
        usage["requests"] += 1
        
        # Kaydet
        self._save_session_costs()
    
    def add_lines_changed(self, added: int = 0, removed: int = 0):
        """Değişen satır sayısını ekle."""
        self.state.total_lines_added += added
        self.state.total_lines_removed += removed
        self._save_session_costs()
    
    def add_tool_duration(self, duration_ms: int):
        """Tool çalışma süresini ekle."""
        self.state.total_tool_duration_ms += duration_ms
        self._save_session_costs()
    
    def add_web_search(self):
        """Web arama sayısını artır."""
        self.state.total_web_search_requests += 1
        self._save_session_costs()
    
    def get_total_cost(self) -> float:
        """Toplam maliyeti getir."""
        return self.state.total_cost_usd
    
    def format_cost(self) -> str:
        """Maliyeti formatlı string olarak döndür."""
        cost = self.state.total_cost_usd
        
        if cost < 0.01:
            return f"${cost * 1000:.2f}m"
        elif cost < 1:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"
    
    def format_duration(self, ms: int) -> str:
        """Süreyi formatla."""
        if ms < 1000:
            return f"{ms}ms"
        elif ms < 60000:
            return f"{ms/1000:.1f}s"
        else:
            return f"{ms/60000:.1f}m"
    
    def get_summary(self) -> str:
        """Özet string döndür."""
        parts = [
            f"Cost: {self.format_cost()}",
            f"Tokens: {self.state.total_input_tokens:,} in / {self.state.total_output_tokens:,} out",
        ]
        
        if self.state.total_cache_read_tokens > 0:
            parts.append(f"Cache: {self.state.total_cache_read_tokens:,} read")
        
        if self.state.total_lines_added > 0:
            parts.append(f"Lines: +{self.state.total_lines_added} / -{self.state.total_lines_removed}")
        
        if self.state.total_api_duration_ms > 0:
            parts.append(f"API: {self.format_duration(self.state.total_api_duration_ms)}")
        
        return " | ".join(parts)
    
    def get_model_breakdown(self) -> dict:
        """Model bazlı döküm."""
        breakdown = {}
        
        for model, usage in self.state.model_usage.items():
            breakdown[model] = {
                "requests": usage["requests"],
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "cost_usd": usage["cost_usd"],
            }
        
        return breakdown
    
    def reset(self):
        """State'i resetle."""
        self.state = CostState()
        self._save_session_costs()
    
    def get_all_sessions(self) -> list[dict]:
        """Tüm session'ları listele."""
        sessions = []
        
        for f in self.cost_dir.glob("session_*.json"):
            try:
                data = json.loads(f.read_text())
                sessions.append({
                    "session_id": f.stem.replace("session_", ""),
                    "cost_usd": data.get("total_cost_usd", 0),
                    "input_tokens": data.get("total_input_tokens", 0),
                    "output_tokens": data.get("total_output_tokens", 0),
                    "file": str(f),
                })
            except Exception:
                continue
        
        sessions.sort(key=lambda x: x["cost_usd"], reverse=True)
        return sessions


# Singleton
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


if __name__ == "__main__":
    print("=== COST TRACKER TEST ===\n")
    
    tracker = get_cost_tracker()
    
    # Test usage
    tracker.add_usage(
        model="minimax-m2.7",
        input_tokens=1000,
        output_tokens=500,
    )
    
    tracker.add_lines_changed(added=50, removed=10)
    
    print(f"Session: {tracker.session_id}")
    print(f"Summary: {tracker.get_summary()}")
    print(f"Total cost: {tracker.get_total_cost():.4f}")
    
    print("\n--- All sessions ---")
    for s in tracker.get_all_sessions()[:5]:
        print(f"  {s['session_id']}: ${s['cost_usd']:.4f}")
