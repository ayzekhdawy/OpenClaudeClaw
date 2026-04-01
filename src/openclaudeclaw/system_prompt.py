"""
System Prompt Builder — OpenClaw Persona System
────────────────────────────────────────────
Claude Code prompts.ts + systemPromptSections.ts referansı.
Modular, section-based system prompt yapımı.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any
from pathlib import Path
import hashlib


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
SOUL_PATH = WORKSPACE / "SOUL.md"
MEMORY_PATH = WORKSPACE / "MEMORY.md"
USER_PATH = WORKSPACE / "USER.md"


@dataclass
class PromptSection:
    """System prompt section."""
    name: str
    content: str
    cache_break: bool = False  # Her turn'de yeniden hesapla


class SystemPromptBuilder:
    """
    Modular system prompt builder.
    Claude Code'un section-based prompts.ts sistemine benzer.
    
    Her section:
    - Bağımsız compute fn
    - Cache desteği
    - Priority-based ordering
    """
    
    def __init__(self):
        self.sections: list[PromptSection] = []
        self._cache: dict[str, str] = {}
        self._cache_enabled = True
    
    def add_section(self, name: str, content: str, cache_break: bool = False) -> "SystemPromptBuilder":
        """Section ekle."""
        self.sections.append(PromptSection(
            name=name,
            content=content,
            cache_break=cache_break,
        ))
        return self
    
    def add_computed(self, name: str, compute_fn: Callable[[], str], cache_break: bool = False) -> "SystemPromptBuilder":
        """Dinamik section ekle (compute fn ile)."""
        content = compute_fn() if self._cache_enabled else compute_fn()
        self.add_section(name, content, cache_break)
        return self
    
    def section(self, name: str) -> "SystemPromptBuilder":
        """Chain için section başlat."""
        return self
    
    def resolve(self) -> str:
        """Tüm section'ları resolve et ve birleştir."""
        lines = []
        
        for section in self.sections:
            if section.cache_break or section.name not in self._cache:
                content = section.content
                if self._cache_enabled:
                    self._cache[section.name] = content
            else:
                content = self._cache[section.name]
            
            if content:
                lines.append(content)
        
        return '\n\n'.join(lines)
    
    def resolve_sections(self) -> list[PromptSection]:
        """Section'ları resolve edilmiş olarak döndür."""
        resolved = []
        
        for section in self.sections:
            if section.cache_break or section.name not in self._cache:
                content = section.content
                if self._cache_enabled:
                    self._cache[section.name] = content
            else:
                content = self._cache[section.name]
            
            if content:
                resolved.append(PromptSection(
                    name=section.name,
                    content=content,
                    cache_break=section.cache_break,
                ))
        
        return resolved
    
    def clear_cache(self):
        """Cache'i temizle."""
        self._cache.clear()
    
    def get_cache_key(self) -> str:
        """Cache key oluştur."""
        content = '\n'.join(s.name + s.content[:50] for s in self.sections)
        return hashlib.md5(content.encode()).hexdigest()[:8]


class EsraPersonaBuilder:
    """
    Esra persona prompt builder.
    SOUL.md + USER.md + MEMORY.md'den beslenir.
    """
    
    def __init__(self):
        self.builder = SystemPromptBuilder()
        self._soul_cache: Optional[dict] = None
        self._memory_cache: Optional[dict] = None
        self._user_cache: Optional[dict] = None
    
    def load_soul(self) -> dict:
        """SOUL.md'yi yükle."""
        if self._soul_cache is not None:
            return self._soul_cache
        
        from src.harness.integrations.soul import get_soul_adapter
        adapter = get_soul_adapter()
        self._soul_cache = adapter.load()
        return self._soul_cache
    
    def load_memory(self) -> dict:
        """MEMORY.md'yi yükle."""
        if self._memory_cache is not None:
            return self._memory_cache
        
        from src.harness.integrations.memory import get_memory_adapter
        adapter = get_memory_adapter()
        self._memory_cache = adapter.load_memory()
        return self._memory_cache
    
    def load_user(self) -> dict:
        """USER.md'yi yükle."""
        if self._user_cache is not None:
            return self._user_cache
        
        from src.harness.integrations.user import get_user_adapter
        adapter = get_user_adapter()
        self._user_cache = adapter.load()
        return self._user_cache
    
    def build_identity_section(self) -> str:
        """Kimlik section'ı."""
        user = self.load_user()
        soul = self.load_soul()
        
        rules = soul.get('always', soul.get('rules', []))[:3]
        rules_text = '\n'.join(f"- {r}" for r in rules) if rules else ""
        
        return f"""# Kimlik — Esra
Sen İshak'ın otonom ajanısın. Adın: Esra.

{soul.get('intro', soul.get('description', ''))}

## Temel Kurallar
{rules_text}

## Kullanıcı
**İsim:** {user.get('name', 'İshak')}
**Lokasyon:** {user.get('location', 'İstanbul')}
**Dil:** {user.get('language', 'Türkçe')}

## İletişim Tarzı
- Kısa cümleler, dolgu yok
- Tek soru disiplini
- Pozisyon al, gerekçeyle güncelle
- Yanlışsam düzeltirim, dramatize etmem"""
    
    def build_persona_rules_section(self) -> str:
        """Persona kuralları section'ı."""
        soul = self.load_soul()
        
        never = soul.get('never', [])[:10]
        always = soul.get('always', [])[:10]
        
        never_text = '\n'.join(f"- ❌ {r}" for r in never) if never else "- (yok)"
        always_text = '\n'.join(f"- ✅ {r}" for r in always) if always else "- (yok)"
        
        return f"""## Davranış Kuralları

### ASLA YAPMA
{never_text}

### HER ZAMAN YAP
{always_text}"""
    
    def build_business_context_section(self) -> str:
        """İş context section'ı."""
        user = self.load_user()
        
        business = user.get('business', {})
        brands = business.get('brands', [])
        financials = user.get('financial', {})
        
        brand_text = '\n'.join(f"- **{b.get('name', '')}**: {b.get('description', '')}" for b in brands) if brands else "- (yok)"
        
        return f"""## İş Context

### Markalar
{brand_text}

### Finansal Durum (2026-03)
- Kredi kartı borcu: {financials.get('kk_borc', 'bilinmiyor')}
- Aylık sabit gider: {financials.get('aylik_gider', 'bilinmiyor')}
- Hedef ciro: {financials.get('hedef_ciro', 'bilinmiyor')}

### Teknik Altyapı
- Python/AI ajan geliştirme
- OpenClaw orchestrator
- Claude Code harness sistemi"""
    
    def build_critical_info_section(self) -> str:
        """Kritik bilgiler section'ı."""
        memory = self.load_memory()
        
        critical = memory.get('critical', [])[:10]
        
        if not critical:
            return ""
        
        critical_text = '\n'.join(f"- {c}" for c in critical)
        
        return f"""## Kritik Bilgiler (Hafıza)
{critical_text}"""
    
    def build_learning_rules_section(self) -> str:
        """Öğrenme kuralları section'ı."""
        memory = self.load_memory()
        
        rules = memory.get('rules', [])[:5]
        
        if not rules:
            return ""
        
        rules_text = '\n'.join(f"- {r}" for r in rules)
        
        return f"""## Öğrenme Kuralları
{rules_text}"""
    
    def build_tools_section(self) -> str:
        """Available tools section'ı."""
        from src.harness.tool_pool import get_tool_pool
        pool = get_tool_pool()
        tools = pool.list_tools()
        
        if not tools:
            return ""
        
        tool_text = '\n'.join(f"- **{t.name}**: {getattr(t, 'description', t.name) or t.name}" for t in tools[:10])
        
        return f"""## Kullanılabilir Araçlar
{tool_text}"""
    
    def build(self) -> str:
        """Full system prompt oluştur."""
        self.builder = SystemPromptBuilder()
        
        # Identity
        self.builder.add_section(
            "identity",
            self.build_identity_section(),
            cache_break=False,
        )
        
        # Persona rules
        self.builder.add_section(
            "persona_rules",
            self.build_persona_rules_section(),
            cache_break=False,
        )
        
        # Business context
        self.builder.add_section(
            "business_context",
            self.build_business_context_section(),
            cache_break=True,  # User data değişebilir
        )
        
        # Critical info
        self.builder.add_section(
            "critical_info",
            self.build_critical_info_section(),
            cache_break=True,
        )
        
        # Learning rules
        self.builder.add_section(
            "learning_rules",
            self.build_learning_rules_section(),
            cache_break=False,
        )
        
        # Tools
        self.builder.add_section(
            "tools",
            self.build_tools_section(),
            cache_break=True,
        )
        
        return self.builder.resolve()
    
    def get_sections(self) -> list[PromptSection]:
        """Section'ları resolve edilmiş olarak döndür."""
        self.build()  # Build etmeden önce sections'ları oluştur
        return self.builder.resolve_sections()


# Singleton
_persona_builder: Optional[EsraPersonaBuilder] = None


def get_persona_builder() -> EsraPersonaBuilder:
    global _persona_builder
    if _persona_builder is None:
        _persona_builder = EsraPersonaBuilder()
    return _persona_builder


def build_esra_system_prompt() -> str:
    """Esra system prompt oluştur (helper fn)."""
    return get_persona_builder().build()


if __name__ == "__main__":
    print("=== ESRA SYSTEM PROMPT TEST ===\n")
    
    builder = get_persona_builder()
    prompt = builder.build()
    
    print(f"Toplam uzunluk: {len(prompt)} karakter\n")
    
    sections = builder.get_sections()
    print("Section'lar:")
    for s in sections:
        print(f"  - {s.name}: {len(s.content)} chars")
    
    print("\n--- Full Prompt ---")
    print(prompt[:1500] + "...")
