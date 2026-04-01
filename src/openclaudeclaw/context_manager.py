"""
Context Manager — Workspace analysis and context building
────────────────────────────────────────────────────────
Clean-room implementation inspired by Claude Code's context system.
Analyzes workspace, tracks context, manages session state.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from .models import WorkspaceAnalysis, SessionManifest


WORKSPACE_ROOT = Path("/home/ayzek/.openclaw/workspace")


@dataclass
class WorkspaceContext:
    """Workspace context for a session."""
    root: Path
    manifest: Optional[SessionManifest] = None
    analysis: Optional[WorkspaceAnalysis] = None
    
    def to_dict(self) -> dict:
        return {
            "root": str(self.root),
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "analysis": {
                "total_files": self.analysis.total_files if self.analysis else 0,
                "code_files": self.analysis.code_files if self.analysis else 0,
                "size_mb": self.analysis.total_size_mb if self.analysis else 0,
            } if self.analysis else None,
        }


def analyze_workspace(root: Path = WORKSPACE_ROOT) -> WorkspaceAnalysis:
    """
    Analyze workspace structure.
    Inspired by Claude Code's workspace analysis.
    """
    analysis = WorkspaceAnalysis(root=str(root))
    
    # Count files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.json', '.yaml', '.yml', '.sh', '.bash'}
    
    total_files = 0
    code_files = 0
    test_files = 0
    languages = {}
    total_size = 0
    
    try:
        for path in root.rglob('*'):
            if path.is_file() and not any(
                p in str(path) for p in ['.git', '__pycache__', 'node_modules', '.venv', '.cache']
            ):
                total_files += 1
                total_size += path.stat().st_size
                
                ext = path.suffix
                if ext in code_extensions:
                    code_files += 1
                    
                    # Language detection
                    lang_map = {
                        '.py': 'Python',
                        '.js': 'JavaScript',
                        '.ts': 'TypeScript',
                        '.jsx': 'JavaScript',
                        '.tsx': 'TypeScript',
                        '.md': 'Markdown',
                        '.json': 'JSON',
                        '.yaml': 'YAML',
                        '.yml': 'YAML',
                        '.sh': 'Shell',
                        '.bash': 'Shell',
                    }
                    lang = lang_map.get(ext, 'Other')
                    languages[lang] = languages.get(lang, 0) + 1
                
                if 'test' in path.name.lower():
                    test_files += 1
    except PermissionError:
        pass
    
    analysis.total_files = total_files
    analysis.code_files = code_files
    analysis.test_files = test_files
    analysis.total_size_mb = total_size / (1024 * 1024)
    analysis.languages = languages
    
    # Git status
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5
        )
        analysis.git_dirty = len(result.stdout.strip()) > 0
        
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5
        )
        analysis.last_commit = result.stdout.strip()
    except:
        pass
    
    return analysis


def build_session_manifest(session_id: str, tools: list[str]) -> SessionManifest:
    """Build a session manifest."""
    analysis = analyze_workspace()
    
    return SessionManifest(
        session_id=session_id,
        tools=tools,
        context_files=analysis.code_files,
        workspace_size_mb=analysis.total_size_mb,
    )


def get_workspace_context(root: Path = WORKSPACE_ROOT) -> WorkspaceContext:
    """Get workspace context for current session."""
    context = WorkspaceContext(root=root)
    context.analysis = analyze_workspace(root)
    return context


def format_context_prompt(context: WorkspaceContext) -> str:
    """Format workspace context for system prompt."""
    if not context.analysis:
        return ""
    
    lines = [
        "# Workspace Context",
        f"Root: {context.root}",
        f"Files: {context.analysis.total_files} (code: {context.analysis.code_files})",
        f"Size: {context.analysis.total_size_mb:.1f}MB",
    ]
    
    if context.analysis.languages:
        lines.append("Languages:")
        for lang, count in sorted(context.analysis.languages.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"  {lang}: {count}")
    
    if context.analysis.git_dirty:
        lines.append("Git: dirty")
    else:
        lines.append("Git: clean")
    
    return '\n'.join(lines)
