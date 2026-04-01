"""
Source Analyzer — Claude Code Source Map Benzeri Yapı
────────────────────────────────────────────────────
Mevcut OpenClaw kod tabanını analiz eder.
Claude Code'un source-map extraction mantığından ilham alındı.

Kullanım:
    python3 -m src.harness.source_analyzer <path>
"""

import ast
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Symbol:
    """Bir kod sembolu."""
    name: str
    type: str  # function, class, method, constant
    line: int
    end_line: int
    file: str
    docstring: Optional[str] = None


@dataclass
class FileAnalysis:
    """Bir dosyanın analizi."""
    path: str
    size_kb: float
    symbols: list[Symbol]
    imports: list[str]
    exports: list[str]


class SourceAnalyzer:
    """
    Python kaynak kodu analizörü.
    Claude Code'un source-map mantığına benzer.
    """
    
    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[str, FileAnalysis] = {}
    
    def analyze_file(self, path: Path) -> Optional[FileAnalysis]:
        """Bir Python dosyasını analiz et."""
        try:
            content = path.read_text()
            tree = ast.parse(content)
            
            symbols = []
            imports = []
            exports = []
            
            for node in ast.walk(tree):
                # Fonksiyonlar
                if isinstance(node, ast.FunctionDef):
                    symbols.append(Symbol(
                        name=node.name,
                        type="function",
                        line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        file=str(path),
                        docstring=ast.get_docstring(node),
                    ))
                
                # Sınıflar
                elif isinstance(node, ast.ClassDef):
                    symbols.append(Symbol(
                        name=node.name,
                        type="class",
                        line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        file=str(path),
                        docstring=ast.get_docstring(node),
                    ))
                
                # Import'lar
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Module exports (top-level defines)
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            exports.append(target.id)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                    exports.append(node.name)
            
            return FileAnalysis(
                path=str(path),
                size_kb=len(content) / 1024,
                symbols=symbols,
                imports=imports,
                exports=exports,
            )
        
        except Exception as e:
            return None
    
    def analyze_workspace(self, patterns: list[str] = None) -> dict:
        """
        Tüm workspace'i analiz et.
        
        Returns:
            dict: {files: [], symbols: [], relationships: []}
        """
        patterns = patterns or ["*.py"]
        
        all_files = []
        all_symbols = []
        all_relationships = []
        
        for pattern in patterns:
            for path in self.root.rglob(pattern):
                if any(p in str(path) for p in ['__pycache__', '.git', 'node_modules']):
                    continue
                
                analysis = self.analyze_file(path)
                if analysis:
                    all_files.append({
                        "path": analysis.path,
                        "size_kb": analysis.size_kb,
                        "symbol_count": len(analysis.symbols),
                    })
                    
                    for symbol in analysis.symbols:
                        all_symbols.append({
                            "name": symbol.name,
                            "type": symbol.type,
                            "file": symbol.file,
                            "line": symbol.line,
                        })
        
        return {
            "files": all_files,
            "symbols": all_symbols,
            "total_files": len(all_files),
            "total_symbols": len(all_symbols),
        }
    
    def find_symbol(self, name: str) -> list[Symbol]:
        """Bir sembolü tüm dosyalarda ara."""
        results = []
        
        for path in self.root.rglob("*.py"):
            if any(p in str(path) for p in ['__pycache__', '.git']):
                continue
            
            analysis = self.analyze_file(path)
            if not analysis:
                continue
            
            for symbol in analysis.symbols:
                if symbol.name == name:
                    results.append(symbol)
        
        return results
    
    def export_json(self, output_path: Path):
        """Analizi JSON olarak kaydet."""
        analysis = self.analyze_workspace()
        output_path.write_text(json.dumps(analysis, indent=2))
        return analysis


if __name__ == "__main__":
    import sys
    
    root = Path("/home/ayzek/.openclaw/workspace")
    analyzer = SourceAnalyzer(root)
    
    print("=== SOURCE ANALYZER ===\n")
    
    # Quick analysis
    result = analyzer.analyze_workspace(["*.py"])
    
    print(f"Total files: {result['total_files']}")
    print(f"Total symbols: {result['total_symbols']}")
    
    # Top files by symbol count
    by_symbols = sorted(result['files'], key=lambda x: x['symbol_count'], reverse=True)[:10]
    
    print("\nTop 10 files by symbol count:")
    for f in by_symbols:
        print(f"  {f['symbol_count']:3d} {f['path'].split('/')[-1]}")
    
    # Save full analysis
    output = root / "memory" / "daily" / "source_analysis.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    analyzer.export_json(output)
    print(f"\nFull analysis saved to: {output}")
