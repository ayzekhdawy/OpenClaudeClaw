"""
Grep Tool — OpenClaw File Search
─────────────────────────────────
Dosyalarda regex/string arama.
Claude Code GrepTool referansı.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable
import fnmatch


@dataclass
class GrepMatch:
    """Bir grep sonucu."""
    path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: list[str] = None
    context_after: list[str] = None
    
    def __post_init__(self):
        if self.context_before is None:
            self.context_before = []
        if self.context_after is None:
            self.context_after = []


class GrepTool:
    """
    Grep tool — dosyalarda arama.
    
    Özellikler:
    - Regex desteği
    - Glob pattern (filename filter)
    - Context lines (before/after)
    - Case sensitive/insensitive
    - Word boundary
    """
    
    def __init__(self, root: Optional[Path] = None):
        self.root = root or Path.cwd()
        self.results: list[GrepMatch] = []
        self.total_matches = 0
        self.total_files = 0
    
    def grep(
        self,
        pattern: str,
        paths: Optional[list[str]] = None,
        regex: bool = True,
        case_sensitive: bool = False,
        word_boundary: bool = False,
        glob: Optional[str] = None,
        context_before: int = 0,
        context_after: int = 0,
        max_results: int = 1000,
        file_limit: int = 100,
    ) -> list[GrepMatch]:
        """
        Grep işlemi yap.
        
        Args:
            pattern: Aranacak pattern
            paths: Aranacak dosya/klasör yolları (None = root)
            regex: Regex kullan (False = literal string)
            case_sensitive: Case sensitive mi?
            word_boundary: Kelime sınırı kullan
            glob: Dosya glob pattern (örn: "*.py")
            context_before: Eşleşmeden önce kaç satır
            context_after: Eşleşmeden sonra kaç satır
            max_results: Maksimum sonuç
            file_limit: Maksimum aranacak dosya sayısı
        
        Returns:
            list[GrepMatch]: Sonuçlar
        """
        self.results = []
        self.total_matches = 0
        self.total_files = 0
        
        # Pattern hazırla
        if word_boundary:
            pattern = r'\b' + re.escape(pattern) + r'\b'
        elif not regex:
            pattern = re.escape(pattern)
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Geçersiz regex: {e}")
        
        # Paths belirle
        if paths:
            search_paths = [Path(p) for p in paths]
        else:
            search_paths = [self.root]
        
        # Her path'i tara
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            if search_path.is_file():
                self._grep_file(
                    search_path, compiled, glob,
                    context_before, context_after, max_results
                )
            else:
                self._grep_directory(
                    search_path, compiled, glob,
                    context_before, context_after, max_results, file_limit
                )
        
        return self.results
    
    def _grep_file(
        self,
        filepath: Path,
        compiled: re.Pattern,
        glob: Optional[str],
        context_before: int,
        context_after: int,
        max_results: int,
    ):
        """Bir dosyada grep yap."""
        # Glob kontrolü
        if glob and not fnmatch.fnmatch(filepath.name, glob):
            return
        
        # Sadece text dosyaları
        if not self._is_text_file(filepath):
            return
        
        try:
            lines = filepath.read_text(errors='ignore').splitlines()
        except Exception:
            return
        
        file_matches = 0
        
        for i, line in enumerate(lines, 1):
            matches = list(compiled.finditer(line))
            
            if matches:
                self.total_files += 1
                
                for match in matches:
                    # Context satırları
                    before = lines[max(0, i-1-context_before):i-1]
                    after = lines[i:min(len(lines), i+context_after)]
                    
                    self.results.append(GrepMatch(
                        path=str(filepath),
                        line_number=i,
                        line_content=line,
                        match_start=match.start(),
                        match_end=match.end(),
                        context_before=before,
                        context_after=after,
                    ))
                    file_matches += 1
                    self.total_matches += 1
                    
                    if len(self.results) >= max_results:
                        return
    
    def _grep_directory(
        self,
        directory: Path,
        compiled: re.Pattern,
        glob: Optional[str],
        context_before: int,
        context_after: int,
        max_results: int,
        file_limit: int,
    ):
        """Bir klasörde grep yap (recursive)."""
        # yaygın ignore dizinleri
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.cache', '.pytest_cache', 'dist', 'build', '.tox', '.mypy_cache'}
        
        files_searched = 0
        
        for filepath in directory.rglob('*'):
            if len(self.results) >= max_results:
                break
            
            if not filepath.is_file():
                continue
            
            # Ignore dizin kontrolü
            if any(part in ignore_dirs for part in filepath.parts):
                continue
            
            files_searched += 1
            if files_searched > file_limit:
                break
            
            self._grep_file(
                filepath, compiled, glob,
                context_before, context_after, max_results
            )
    
    def _is_text_file(self, filepath: Path) -> bool:
        """Text dosya mı kontrol et."""
        # Extension kontrolü
        text_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.txt', '.json',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.xml',
            '.html', '.css', '.scss', '.sass', '.less', '.sh', '.bash',
            '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.sql', '.csv',
            '.log', '.env', '.gitignore', '.dockerignore', '.editorconfig',
            '.rst', '.tex', '.r', '.lua', '.php', '.rb', '.go', '.rs',
            '.swift', '.kt', '.java', '.c', '.cpp', '.h', '.hpp', '.cs',
        }
        
        if filepath.suffix.lower() in text_extensions:
            return True
        
        # Binary kontrolü
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(512)
                # Null byte = binary
                if b'\x00' in chunk:
                    return False
                # Çok fazla yüksek ASCII = binary
                high_chars = sum(1 for b in chunk if 127 < b < 256)
                if high_chars > 32:
                    return False
        except Exception:
            return False
        
        return True
    
    def format_results(self, show_path: bool = True, show_line: bool = True) -> str:
        """Sonuçları formatla."""
        if not self.results:
            return "Sonuç bulunamadı."
        
        lines = []
        
        # Özet
        lines.append(f"📁 {self.total_files} dosya | 🔍 {self.total_matches} eşleşme\n")
        
        # Sonuçlar
        current_file = None
        
        for match in self.results:
            # Dosya değiştiğinde başlık ekle
            if show_path and match.path != current_file:
                current_file = match.path
                lines.append(f"\n📄 {match.path}")
            
            # Satır içeriği
            if show_line:
                # Highlight
                highlighted = (
                    match.line_content[:match.match_start]
                    + "»" + match.line_content[match.match_start:match.match_end] + "«"
                    + match.line_content[match.match_end:]
                )
                lines.append(f"  {match.line_number}: {highlighted}")
            else:
                lines.append(f"  {match.line_number}: {match.line_content.strip()}")
        
        return '\n'.join(lines)


# Singleton
_grep_tool: Optional[GrepTool] = None


def get_grep_tool() -> GrepTool:
    global _grep_tool
    if _grep_tool is None:
        _grep_tool = GrepTool(Path.home() / ".openclaw" / "workspace")
    return _grep_tool


if __name__ == "__main__":
    tool = get_grep_tool()
    
    print("=== GREP TOOL TEST ===\n")
    
    # Test search
    results = tool.grep(
        "class.*Task",
        paths=["/home/ayzek/.openclaw/workspace/src"],
        regex=True,
        context_before=1,
        context_after=1,
    )
    
    print(f"Results: {tool.total_matches} matches in {tool.total_files} files\n")
    print(tool.format_results())
