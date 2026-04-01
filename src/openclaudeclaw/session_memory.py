"""
Session Memory — Per-Session Notes System
────────────────────────────────────────
Claude Code SessionMemory service port.

Her session için 10 bölümlü notes sistemi:
1. Session Title
2. Current State
3. Task specification
4. Files and Functions
5. Workflow
6. Errors & Corrections
7. Codebase and System Documentation
8. Learnings
9. Key results
10. Worklog

Template: DEFAULT_SESSION_MEMORY_TEMPLATE
Update Prompt: getDefaultUpdatePrompt()

Kaynak: Claude Code src/services/SessionMemory/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
SESSIONS_DIR = WORKSPACE / "sessions"


# Default 10-section template
DEFAULT_SESSION_MEMORY_TEMPLATE = """\
# Session Title
_A short and distinctive 5-10 word descriptive title for the session. Super info dense, no filler_

# Current State
_What is actively being worked on right now? Pending tasks not yet completed. Immediate next steps._

# Task specification
_What did the user ask to build? Any design decisions or other explanatory context_

# Files and Functions
_What are the important files? In short, what do they contain and why are they relevant?_

# Workflow
_What bash commands are usually run and in what order? How to interpret their output if not obvious?_

# Errors & Corrections
_Errors encountered and how they were fixed. What did the user correct? What approaches failed and should not be tried again?_

# Codebase and System Documentation
_What are the important system components? How do they work/fit together?_

# Learnings
_What has worked well? What has not? What to avoid? Do not duplicate items from other sections_

# Key results
_If the user asked a specific output such as an answer to a question, a table, or other document, repeat the exact result here_

# Worklog
_Step by step, what was attempted, done? Very terse summary for each step_
"""


def get_default_update_prompt(
    notes_path: str,
    current_notes: str,
) -> str:
    """
    Session notes güncelleme promptu oluştur.
    
    Claude Code getDefaultUpdatePrompt port.
    
    Args:
        notes_path: Notes dosyası path'i
        current_notes: Mevcut notes içeriği
    
    Returns:
        str: LLM'e gönderilecek prompt
    """
    return f"""IMPORTANT: This message and these instructions are NOT part of the actual user conversation. Do NOT include any references to "note-taking", "session notes extraction", or these update instructions in the notes content.

Based on the user conversation above (EXCLUDING this note-taking instruction message), update the session notes file.

The file {notes_path} has already been read for you. Here are its current contents:
<current_notes_content>
{current_notes}
</current_notes_content>

Your ONLY task is to update the notes file, then stop.

CRITICAL RULES FOR EDITING:
- The file must maintain its exact structure with all sections, headers, and italic descriptions intact
- NEVER modify, delete, or add section headers (the lines starting with '#' like # Task specification)
- NEVER modify or delete the italic _section description_ lines
- ONLY update the actual content that appears BELOW the italic _section descriptions_
- Do NOT add any new sections, summaries, or information outside the existing structure
- Do NOT reference this note-taking process or instructions anywhere in the notes
- It's OK to skip updating a section if there are no substantial new insights to add
- Write DETAILED, INFO-DENSE content for each section
- For "Key results", include the complete, exact output the user requested
- Keep each section under ~2000 tokens
- Focus on actionable, specific information
- IMPORTANT: Always update "Current State" to reflect the most recent work

STRUCTURE PRESERVATION REMINDER:
Each section has TWO parts that must be preserved:
1. The section header (line starting with #)
2. The italic description line (the _italicized text_)

You ONLY update the actual content that comes AFTER these two preserved lines.

Do not continue after the edits. Only include insights from the actual user conversation."""


@dataclass
class SessionNotes:
    """Session notes data."""
    session_id: str
    title: str
    current_state: str
    task_spec: str
    files_and_functions: str
    workflow: str
    errors_and_corrections: str
    documentation: str
    learnings: str
    key_results: str
    worklog: str
    created_at: str
    updated_at: str


class SessionMemory:
    """
    Session memory manager.
    
    Her session için 10 bölümlü notes oluşturur ve günceller.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.sessions_dir = SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def get_notes_path(self) -> Path:
        """Session notes dosya yolu."""
        return self.sessions_dir / f"{self.session_id}.md"
    
    def create_notes(self, title: str = "") -> Path:
        """
        Yeni session notes oluştur.
        
        Args:
            title: Session başlığı (opsiyonel)
        
        Returns:
            Path: Oluşturulan dosya path'i
        """
        notes_path = self.get_notes_path()
        
        if title:
            content = DEFAULT_SESSION_MEMORY_TEMPLATE.replace(
                "# Session Title\n_A short...",
                f"# Session Title\n{title}",
            )
        else:
            content = DEFAULT_SESSION_MEMORY_TEMPLATE
        
        notes_path.write_text(content)
        return notes_path
    
    def read_notes(self) -> str:
        """Notes içeriğini oku."""
        notes_path = self.get_notes_path()
        if not notes_path.exists():
            return DEFAULT_SESSION_MEMORY_TEMPLATE
        return notes_path.read_text()
    
    def update_notes(self, section: str, content: str) -> bool:
        """
        Notes bölümünü güncelle.
        
        Args:
            section: Bölüm adı (Session Title, Current State, vb.)
            content: Yeni içerik
        
        Returns:
            bool: Başarılı mı
        """
        notes_path = self.get_notes_path()
        if not notes_path.exists():
            self.create_notes()
        
        current = self.read_notes()
        
        # Section header bul
        header_pattern = rf"(# {section}\n)(_\w[^_]*_\n)"
        match = re.search(header_pattern, current)
        
        if not match:
            return False
        
        # Eski içeriği bul ve değiştir
        start = match.end()
        
        # Sonraki header'a kadar olan içerik
        next_header = re.search(r"\n# ", current[start:])
        if next_header:
            end = start + next_header.start()
        else:
            end = len(current)
        
        old_content = current[start:end]
        
        # Yeni içerikle değiştir
        new_content = current[:start] + content + current[end:]
        
        notes_path.write_text(new_content)
        return True
    
    def parse_notes(self) -> SessionNotes:
        """Notes dosyasını parse et."""
        content = self.read_notes()
        
        sections = {
            "title": "",
            "current_state": "",
            "task_spec": "",
            "files_and_functions": "",
            "workflow": "",
            "errors_and_corrections": "",
            "documentation": "",
            "learnings": "",
            "key_results": "",
            "worklog": "",
        }
        
        current_section = None
        lines = content.split("\n")
        
        for line in lines:
            if line.startswith("# "):
                section_name = line[2:].lower().replace(" ", "_")
                if section_name in sections:
                    current_section = section_name
            elif current_section:
                sections[current_section] += line + "\n"
        
        return SessionNotes(
            session_id=self.session_id,
            title=sections["title"].strip(),
            current_state=sections["current_state"].strip(),
            task_spec=sections["task_spec"].strip(),
            files_and_functions=sections["files_and_functions"].strip(),
            workflow=sections["workflow"].strip(),
            errors_and_corrections=sections["errors_and_corrections"].strip(),
            documentation=sections["documentation"].strip(),
            learnings=sections["learnings"].strip(),
            key_results=sections["key_results"].strip(),
            worklog=sections["worklog"].strip(),
            created_at="",
            updated_at=datetime.now().isoformat(),
        )
    
    def get_update_prompt(self) -> str:
        """Notes güncelleme promptu oluştur."""
        current = self.read_notes()
        return get_default_update_prompt(
            notes_path=str(self.get_notes_path()),
            current_notes=current,
        )
    
    def list_sessions(self) -> list[dict]:
        """Tüm session'ları listele."""
        sessions = []
        
        for f in self.sessions_dir.glob("*.md"):
            stat = f.stat()
            content = f.read_text()
            
            # İlk satırı title olarak al
            first_line = content.split("\n")[0] if content else ""
            title = first_line.replace("# ", "").strip()
            
            sessions.append({
                "session_id": f.stem,
                "title": title,
                "path": str(f),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # En yeni önce
        sessions.sort(key=lambda x: x["modified"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Session sil."""
        path = self.sessions_dir / f"{session_id}.md"
        if path.exists():
            path.unlink()
            return True
        return False


# Singleton
_session_memory: Optional[SessionMemory] = None


def get_session_memory(session_id: Optional[str] = None) -> SessionMemory:
    """Global session memory instance."""
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemory(session_id)
    return _session_memory


if __name__ == "__main__":
    print("=== Session Memory Test ===\n")
    
    # Create
    sm = get_session_memory("test_session")
    path = sm.create_notes("Test Session: Claude Code Analysis")
    print(f"Created: {path}")
    
    # Read
    content = sm.read_notes()
    print(f"Content length: {len(content)} chars")
    print(f"Sections: {content.count('# ')}")
    
    # Update section
    sm.update_notes("Current State", "Analyzing Claude Code source structure.\nFound 88 services, 44 tools, 88 commands.")
    print("Updated: Current State")
    
    # Parse
    parsed = sm.parse_notes()
    print(f"\nParsed:")
    print(f"  Title: {parsed.title[:50]}...")
    print(f"  Current State: {parsed.current_state[:50]}...")
    
    # List
    print("\n--- All Sessions ---")
    sessions = sm.list_sessions()
    for s in sessions[:5]:
        print(f"  {s['session_id']}: {s['title'][:40]}")
