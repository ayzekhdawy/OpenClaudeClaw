"""
Semantic Memory v2 — LLM Side-Query Implementation
───────────────────────────────────────────────────
Claude Code findRelevantMemories.ts pattern'i.

1. memory/ klasörünü tara → frontmatter + ilk 5 satır
2. LLM'e gönder → alakalı dosyaları seç
3. Seçilenleri tam oku → context'e ekle
4. Max 5 dosya, alreadySurfaced filtresi
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import hashlib


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"


@dataclass
class MemoryFile:
    """Bir memory dosyası."""
    path: Path
    filename: str
    description: str  # Frontmatter + ilk 5 satır
    content: str = ""  # Tam içerik (lazily loaded)
    frontmatter: dict = field(default_factory=dict)
    mtime: float = 0
    size: int = 0
    
    @property
    def age_days(self) -> float:
        return (datetime.now().timestamp() - self.mtime) / 86400


@dataclass 
class MemoryScanner:
    """Memory dosyalarını tarar."""
    root: Path = MEMORY_DIR
    
    def scan(self) -> list[MemoryFile]:
        """Tüm memory dosyalarını tara."""
        files = []
        
        if not self.root.exists():
            return files
        
        for md_file in self.root.rglob("*.md"):
            # Skip hidden and archive
            # Path.parts always starts with '/', check actual directory names
            relative = md_file.relative_to(self.root if self.root.exists() else md_file.parent)
            parts = relative.parts
            if any(p.startswith('.') for p in parts):
                continue
            if 'archive' in parts:
                continue
            
            try:
                stat = md_file.stat()
                
                # Frontmatter + ilk satırları oku (description için)
                content = md_file.read_text(errors='ignore')
                description = self._extract_description(content)
                frontmatter = self._parse_frontmatter(content)
                
                files.append(MemoryFile(
                    path=md_file,
                    filename=md_file.name,
                    description=description,
                    content="",  # Lazy load
                    frontmatter=frontmatter,
                    mtime=stat.st_mtime,
                    size=stat.st_size,
                ))
            except Exception:
                continue
        
        return files
    
    def _extract_description(self, content: str) -> str:
        """Frontmatter + ilk 5 satırı çıkar."""
        lines = content.split('\n')
        
        # Frontmatter atla
        start = 0
        if lines and lines[0].strip() == '---':
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    start = i + 1
                    break
        
        # İlk 5 satır
        relevant = lines[start:start+5]
        return ' '.join(l.strip() for l in relevant if l.strip())
    
    def _parse_frontmatter(self, content: str) -> dict:
        """Frontmatter'i parse et."""
        frontmatter = {}
        lines = content.split('\n')
        
        if not (lines and lines[0].strip() == '---'):
            return frontmatter
        
        for line in lines[1:]:
            if line.strip() == '---':
                break
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
        
        return frontmatter


class LLMSideQuery:
    """
    Memory seçimi için LLM side-query.
    Claude Code findRelevantMemories.ts pattern'i.
    """
    
    SYSTEM_PROMPT = """Sen bir memory asistanısın.

Kullanıcı query'si için hangi memory dosyalarının alakalı olduğunu seç.

Kurallar:
- Sadece JSON array döndür: ["filename1.md", "filename2.md", ...]
- Max 5 dosya seç
- Çok alakalı olanları önce listele
- Eğer hiç alakalı dosya yoksa boş array döndür: []
- Sadece dosya adlarını döndür, açıklama ekleme

Memory dosyaları:
{memories}

Query: {query}"""
    
    def __init__(self):
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Ollama'nın çalışıp çalışmadığını kontrol et."""
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:11434/api/tags",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    def query(self, query: str, memories: list[MemoryFile], model: str = "minimax-m2.7:cloud") -> list[str]:
        """
        LLM'e memory seçimi sor.
        
        Args:
            query: Kullanıcı query'si
            memories: Taranmış memory dosyaları
            model: Kullanılacak model
        
        Returns:
            list[str]: Seçilen dosya adları
        """
        if not memories:
            return []
        
        # Memory listesi oluştur
        memory_list = []
        for m in memories[:20]:  # Max 20 dosya gönder
            memory_list.append(f"- {m.filename}: {m.description[:100]}")
        
        memories_text = '\n'.join(memory_list)
        
        prompt = self.SYSTEM_PROMPT.format(
            memories=memories_text,
            query=query
        )
        
        # Ollama'a gönder
        if self.ollama_available:
            try:
                return self._query_ollama(prompt, model)
            except Exception as e:
                print(f"LLM query hatası: {e}")
        
        # Fallback: keyword matching
        return self._fallback_keyword(query, memories)
    
    def _query_ollama(self, prompt: str, model: str) -> list[str]:
        """Ollama'a gönder."""
        import urllib.request
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 100,
            }
        }
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            response = result.get("response", "").strip()
            
            # JSON parse
            try:
                #```json ... ``` içinden çıkar
                match = re.search(r'\[.*\]', response, re.DOTALL)
                if match:
                    filenames = json.loads(match.group())
                    return filenames[:5]
            except Exception:
                pass
            
            return []
    
    def _fallback_keyword(self, query: str, memories: list[MemoryFile]) -> list[str]:
        """Fallback: keyword matching."""
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 3]
        
        scored = []
        for m in memories:
            score = 0
            desc_lower = m.description.lower()
            
            for word in query_words:
                if word in desc_lower:
                    score += 3
                if word in m.filename.lower():
                    score += 2
            
            if score > 0:
                scored.append((score, m.filename))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:5]]


class SemanticMemory:
    """
    Semantic memory sistemi — LLM Side-Query ile.
    
    Claude Code memdir/ + findRelevantMemories.ts pattern'i.
    """
    
    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or MEMORY_DIR
        self.scanner = MemoryScanner(self.memory_dir)
        self.llm_query = LLMSideQuery()
        self._cache: dict[str, list[MemoryFile]] = {}
        self._content_cache: dict[str, str] = {}
    
    def find_relevant(
        self,
        query: str,
        recent_tools: list[str] = None,
        use_llm: bool = True,
    ) -> list[MemoryFile]:
        """
        Query için alakalı memory dosyalarını bul.
        
        Args:
            query: Kullanıcı query'si
            recent_tools: Son kullanılan tool'lar (duplicate önleme)
            use_llm: LLM side-query kullan (False = keyword fallback)
        
        Returns:
            list[MemoryFile]: Alakalı dosyalar
        """
        files = self.scanner.scan()
        
        if not files:
            return []
        
        # LLM side-query
        if use_llm and self.llm_query.ollama_available:
            selected_names = self.llm_query.query(query, files)
            
            # AlreadySurfaced filtreleme
            if recent_tools:
                selected_names = self._filter_already_surfaced(
                    selected_names, recent_tools
                )
            
            # Seçilen dosyaları döndür
            selected = []
            for name in selected_names[:5]:
                for f in files:
                    if f.filename == name:
                        selected.append(f)
                        break
            
            if selected:
                return selected
        
        # Fallback: keyword matching
        return self._keyword_match(query, files, recent_tools)
    
    def _filter_already_surfaced(
        self,
        filenames: list[str],
        recent_tools: list[str],
    ) -> list[str]:
        """alreadySurfaced filtreleme."""
        filtered = []
        
        for name in filenames:
            # Son 5 tool'da görülmüş mü?
            tool_key = name.replace('.md', '').lower()
            seen = any(tool_key in tool.lower() for tool in recent_tools[-5:])
            
            if not seen:
                filtered.append(name)
        
        return filtered
    
    def _load_content(self, f: MemoryFile) -> str:
        """Lazily load file content into cache."""
        key = str(f.path)
        if key in self._content_cache:
            return self._content_cache[key]
        try:
            self._content_cache[key] = f.path.read_text(errors='ignore')
        except Exception:
            self._content_cache[key] = ""
        return self._content_cache[key]
    
    def _keyword_match(
        self,
        query: str,
        files: list[MemoryFile],
        recent_tools: list[str] = None,
    ) -> list[MemoryFile]:
        """Keyword-based matching (fallback)."""
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        scored = []
        
        for f in files:
            score = 0
            desc_lower = f.description.lower()
            path_lower = str(f.path).lower()
            frontmatter_text = ' '.join(f.frontmatter.values()).lower() if f.frontmatter else ''
            
            # Quick check: description + path
            for word in query_words:
                if word in desc_lower:
                    score += 3
                if word in path_lower:
                    score += 2
                if word in frontmatter_text:
                    score += 2
            
            # Always check content for all queries (not just when keyword found)
            # This ensures single-word queries like "Ishak" work
            content = self._load_content(f)
            if content:
                content_lower = content.lower()
                for word in query_words:
                    if word in content_lower:
                        score += 1
                        # Bonus if in first 200 chars (likely relevant)
                        if word in content_lower[:200]:
                            score += 1
            
            # Gençlik bonusu
            if f.age_days < 3:
                score *= 1.5
            elif f.age_days < 7:
                score *= 1.2
            
            if score > 0:
                scored.append((score, f))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:5]]
    
    def get_context_for_task(
        self,
        task: str,
        max_files: int = 5,
        use_llm: bool = True,
    ) -> str:
        """
        Task için relevant memory context'i oluştur.
        Seçilen dosyaları tam okur.
        """
        relevant = self.find_relevant(task, use_llm=use_llm)
        
        if not relevant:
            return ""
        
        context_parts = []
        
        for f in relevant[:max_files]:
            # Lazy load content
            key = str(f.path)
            if key not in self._content_cache:
                try:
                    self._content_cache[key] = f.path.read_text()
                except Exception:
                    continue

            content = self._content_cache[key]
            
            context_parts.append(f"""## {f.filename}

{content[:1500]}""")
        
        if not context_parts:
            return ""
        
        return '\n---\n'.join(context_parts)
    
    def get_content(self, filename: str) -> Optional[str]:
        """Belirli bir dosyanın içeriğini getir."""
        for f in self.scanner.scan():
            if f.filename == filename:
                key = str(f.path)
                if key not in self._content_cache:
                    try:
                        self._content_cache[key] = f.path.read_text()
                    except Exception:
                        return None
                return self._content_cache[key]
        return None
    
    def get_stats(self) -> dict:
        """İstatistikler."""
        files = self.scanner.scan()
        
        now = datetime.now().timestamp()
        
        by_type = {"recent": 0, "older": 0}
        total_size = 0
        
        for f in files:
            age_days = (now - f.mtime) / 86400
            
            if age_days < 7:
                by_type["recent"] += 1
            else:
                by_type["older"] += 1
            
            total_size += f.size
        
        return {
            "total": len(files),
            "recent_7d": by_type["recent"],
            "older": by_type["older"],
            "by_type": by_type,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        }
    
    def clear_cache(self):
        """Cache'i temizle."""
        self._cache.clear()
        self._content_cache.clear()


# Singleton
_semantic_memory: Optional[SemanticMemory] = None


def get_semantic_memory() -> SemanticMemory:
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory()
    return _semantic_memory


if __name__ == "__main__":
    print("=== SEMANTIC MEMORY v2 TEST ===\n")
    
    sm = get_semantic_memory()
    
    # Stats
    stats = sm.get_stats()
    print(f"Files: {stats['total']}")
    print(f"Recent (7d): {stats['recent_7d']}")
    print(f"LLM Available: {sm.llm_query.ollama_available}")
    print()
    
    # Test query
    query = "Flech kahve içerik planı"
    print(f"Query: '{query}'")
    print()
    
    relevant = sm.find_relevant(query, use_llm=True)
    print(f"Relevant files: {len(relevant)}")
    for f in relevant:
        print(f"  - {f.filename}: {f.description[:60]}...")
    
    print()
    
    # Context
    context = sm.get_context_for_task(query, use_llm=True)
    print(f"Context length: {len(context)} chars")
