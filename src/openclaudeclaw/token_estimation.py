"""
Token Estimation Service
────────────────────────────────────────────────────────
Claude Code tokenEstimation.ts port.

Token sayısı ve maliyet tahmini.
"""

from __future__ import annotations

import re
from typing import Optional


# Claude Code constants
CHARS_PER_TOKEN = 4  # Rough estimate
WORDS_PER_TOKEN = 0.75  # Rough estimate

# Model context windows
CONTEXT_WINDOWS = {
    "claude-opus-4-5": 200000,
    "claude-sonnet-4-7": 200000,
    "claude-opus-3-5": 180000,
    "claude-sonnet-3-5": 155000,
    "claude-opus-3": 180000,
    "claude-sonnet-3": 155000,
    "claude-3-5-sonnet-latest": 155000,
    "claude-3-opus-latest": 180000,
    "claude-3-sonnet-latest": 155000,
    "claude-3-haiku-latest": 140000,
    # Ollama models
    "llama3": 8192,
    "mistral": 8192,
    "mixtral": 32768,
    "qwen2.5": 32768,
    "minimax-m2.7": 32000,
}

# Cost per million tokens (approximate)
COSTS_PER_MILLION = {
    "claude-opus-4-5": 15.0,
    "claude-sonnet-4-7": 3.0,
    "claude-opus-3-5": 15.0,
    "claude-sonnet-3-5": 3.0,
    "claude-opus-3": 15.0,
    "claude-sonnet-3": 3.0,
    "claude-3-5-sonnet-latest": 3.0,
    "claude-3-opus-latest": 15.0,
    "claude-3-sonnet-latest": 3.0,
    "claude-3-haiku-latest": 0.25,
    # Ollama (local, no cost)
    "llama3": 0.0,
    "mistral": 0.0,
    "mixtral": 0.0,
    "qwen2.5": 0.0,
    "minimax-m2.7": 0.0,
}


def rough_token_count_estimation(text: str) -> int:
    """
    Metnin yaklaşık token sayısını hesapla.
    
    Claude Code roughTokenCountEstimation port.
    
    Args:
        text: Hesaplanacak metin
    
    Returns:
        int: Tahmini token sayısı
    """
    if not text:
        return 0
    
    # Claude Code'un kullandığı basit hesaplama
    # Genellikle 4 karakter ≈ 1 token
    return len(text) // CHARS_PER_TOKEN


def token_count_from_words(text: str) -> int:
    """
    Kelime sayısından token tahmini.
    
    Args:
        text: Hesaplanacak metin
    
    Returns:
        int: Tahmini token sayısı
    """
    if not text:
        return 0
    
    words = len(text.split())
    return int(words / WORDS_PER_TOKEN)


def estimate_tokens_from_messages(messages: list[dict]) -> int:
    """
    Mesaj listesinden toplam token tahmini.
    
    Args:
        messages: [{"role": "user", "content": "..."}, ...]
    
    Returns:
        int: Toplam tahmini token
    """
    total = 0
    
    for msg in messages:
        content = msg.get("content", "")
        total += rough_token_count_estimation(content)
        
        # Role overhead (yaklaşık)
        total += 4
    
    # Message overhead
    total += 3 * len(messages)
    
    return total


def get_context_window(model: str) -> int:
    """
    Model'in context window'unu al.
    
    Args:
        model: Model adı
    
    Returns:
        int: Context window (token)
    """
    # Exact match
    if model in CONTEXT_WINDOWS:
        return CONTEXT_WINDOWS[model]
    
    # Partial match
    model_lower = model.lower()
    for key, value in CONTEXT_WINDOWS.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return value
    
    # Default
    return 128000


def get_cost_per_million(model: str) -> float:
    """
    Model'in milyon başına maliyetini al.
    
    Args:
        model: Model adı
    
    Returns:
        float: Milyon başına USD
    """
    # Exact match
    if model in COSTS_PER_MILLION:
        return COSTS_PER_MILLION[model]
    
    # Partial match
    model_lower = model.lower()
    for key, value in COSTS_PER_MILLION.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return value
    
    # Default (assume Claude 3.5 Sonnet pricing)
    return 3.0


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:
    """
    Tahmini maliyeti hesapla.
    
    Args:
        input_tokens: Giriş token sayısı
        output_tokens: Çıkış token sayısı
        model: Model adı
    
    Returns:
        float: USD cinsinden tahmini maliyet
    """
    cost_per_million = get_cost_per_million(model)
    
    # Claude API: input ve output aynı fiyat (çoğu model için)
    total_tokens = input_tokens + output_tokens
    cost = (total_tokens / 1_000_000) * cost_per_million
    
    return cost


def calculate_cache_cost(
    cache_creation_tokens: int,
    cache_read_tokens: int,
    model: str,
) -> tuple[float, float]:
    """
    Cache maliyetini hesapla.
    
    Claude Code calculateCacheCost port.
    
    Args:
        cache_creation_tokens: Cache oluşturma token
        cache_read_tokens: Cache okuma token
        model: Model adı
    
    Returns:
        tuple: (cache_creation_cost, cache_read_savings)
    """
    cost_per_million = get_cost_per_million(model)
    
    # Cache creation pahalı
    cache_creation_cost = (cache_creation_tokens / 1_000_000) * cost_per_million * 5  # 5x normal
    
    # Cache read ucuz
    cache_read_savings = (cache_read_tokens / 1_000_000) * cost_per_million * 0.1  # 90% indirim
    
    return cache_creation_cost, cache_read_savings


def format_token_count(tokens: int) -> str:
    """
    Token sayısını okunabilir formata çevir.
    
    Args:
        tokens: Token sayısı
    
    Returns:
        str: Formatlı string
    """
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1_000_000:
        return f"{tokens/1000:.1f}K"
    else:
        return f"{tokens/1_000_000:.2f}M"


def format_cost(cost_usd: float) -> str:
    """
    Maliyeti okunabilir formata çevir.
    
    Args:
        cost_usd: USD cinsinden maliyet
    
    Returns:
        str: Formatlı string
    """
    if cost_usd < 0.01:
        return f"${cost_usd*100:.2f}¢"
    elif cost_usd < 1:
        return f"${cost_usd:.4f}"
    else:
        return f"${cost_usd:.2f}"


def get_usage_percentage(
    token_count: int,
    model: str,
) -> float:
    """
    Context kullanım yüzdesini hesapla.
    
    Args:
        token_count: Mevcut token sayısı
        model: Model adı
    
    Returns:
        float: Yüzde (0-100)
    """
    context_window = get_context_window(model)
    return (token_count / context_window) * 100


def estimate_cache_impact(
    prompt_tokens: int,
    cache_hit_rate: float,
) -> tuple[int, int]:
    """
    Cache'in token tasarrufunu tahmin et.
    
    Args:
        prompt_tokens: Toplam prompt token
        cache_hit_rate: Cache hit oranı (0-1)
    
    Returns:
        tuple: (cached_tokens, non_cached_tokens)
    """
    cached_tokens = int(prompt_tokens * cache_hit_rate)
    non_cached_tokens = prompt_tokens - cached_tokens
    
    return cached_tokens, non_cached_tokens


class TokenEstimator:
    """
    Token tahminleyici sınıfı.
    
    Stateful - mesaj geçmişi tutar.
    """
    
    def __init__(self, model: str = "minimax-m2.7"):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_creation = 0
        self.total_cache_read = 0
    
    def add_input(self, text: str) -> int:
        """Input metni ekle, token sayısını döndür."""
        tokens = rough_token_count_estimation(text)
        self.total_input_tokens += tokens
        return tokens
    
    def add_output(self, text: str) -> int:
        """Output metni ekle, token sayısını döndür."""
        tokens = rough_token_count_estimation(text)
        self.total_output_tokens += tokens
        return tokens
    
    def add_cache_creation(self, tokens: int):
        """Cache creation token ekle."""
        self.total_cache_creation += tokens
    
    def add_cache_read(self, tokens: int):
        """Cache read token ekle."""
        self.total_cache_read += tokens
    
    def get_total_tokens(self) -> int:
        """Toplam token sayısı."""
        return self.total_input_tokens + self.total_output_tokens
    
    def get_cost(self) -> float:
        """Tahmini maliyet."""
        return estimate_cost(
            self.total_input_tokens,
            self.total_output_tokens,
            self.model,
        )
    
    def get_cache_cost(self) -> tuple[float, float]:
        """Cache maliyeti."""
        return calculate_cache_cost(
            self.total_cache_creation,
            self.total_cache_read,
            self.model,
        )
    
    def get_usage_percentage(self) -> float:
        """Context kullanım yüzdesi."""
        return get_usage_percentage(
            self.total_input_tokens,
            self.model,
        )
    
    def get_summary(self) -> dict:
        """Özet bilgi."""
        return {
            "model": self.model,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.get_total_tokens(),
            "cost_usd": self.get_cost(),
            "cache_creation_tokens": self.total_cache_creation,
            "cache_read_tokens": self.total_cache_read,
            "usage_percent": self.get_usage_percentage(),
            "context_window": get_context_window(self.model),
        }


if __name__ == "__main__":
    print("=== Token Estimation Test ===\n")
    
    # Test functions
    text = "Bu bir test metnidir. Token sayısını hesaplayalım."
    tokens = rough_token_count_estimation(text)
    print(f"Text: {text}")
    print(f"Tokens: {tokens}")
    
    # Messages
    messages = [
        {"role": "user", "content": "Flech için tweet yaz"},
        {"role": "assistant", "content": "İşte tweet: ..."},
    ]
    total = estimate_tokens_from_messages(messages)
    print(f"\nMessages: {len(messages)}")
    print(f"Total tokens: {total}")
    
    # Cost
    cost = estimate_cost(1000, 500, "minimax-m2.7")
    print(f"\nCost (1K in, 500 out): ${cost:.6f}")
    
    # Context window
    print(f"\nContext windows:")
    for model in ["claude-opus-4-5", "minimax-m2.7", "llama3"]:
        ctx = get_context_window(model)
        print(f"  {model}: {ctx:,} tokens")
    
    # TokenEstimator
    print("\n--- TokenEstimator ---")
    est = TokenEstimator("minimax-m2.7")
    est.add_input("Test input " * 100)
    est.add_output("Test output " * 50)
    summary = est.get_summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")
