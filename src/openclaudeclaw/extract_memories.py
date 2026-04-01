"""
Extract Memories — Background Memory Extraction
────────────────────────────────────────────
Claude Code extractMemories/prompts.ts port.

Her session sonunda son N mesajı analiz edip memory/ klasörüne kaydeder.
- Duplicate önleme
- Var olan dosyayı güncelleme
- MEMORY.md index'e pointer ekleme

Tetiklenme: 5+ mesaj birikince devreye girer.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"


# Memory type taxonomy
MEMORY_TYPES = ["user", "feedback", "project", "reference"]


MEMORY_FRONTMATTER_TEMPLATE = """---
name: {name}
description: {description}
type: {type}
---

{content}"""


MEMORY_FRONTMATTER_EXAMPLE = """```markdown
---
name: {name}
description: {one-line description — used to decide relevance in future conversations}
type: {user, feedback, project, reference}
---

Memory content here.
```"""


TYPES_SECTION_INDIVIDUAL = """
## Types of memory

There are several discrete types of memory that you can store. Each type below declares guidance for when and how to save.

<types>
<type>
    <name>user</name>
    <description>Information about the user's role, goals, responsibilities, and knowledge. Helps tailor behavior to user preferences.</description>
    <when_to_save>When you learn any details about the user's role, preferences, or knowledge</when_to_save>
    <how_to_use>When answering questions tailored to user's expertise level</how_to_use>
    <examples>
    user: I'm a data scientist investigating our logging
    assistant: [saves: user is a data scientist, focused on observability]
    </examples>
</type>

<type>
    <name>feedback</name>
    <description>Guidance from user about how to approach work — what to avoid and what to keep doing.</description>
    <when_to_save>When user corrects your approach OR confirms a non-obvious approach worked</when_to_save>
    <how_to_use>Let these memories guide behavior so user doesn't need to repeat guidance</how_to_use>
    <body_structure>Lead with rule, then **Why:** and **How to apply:** lines</body_structure>
    <examples>
    user: stop summarizing what you just did
    assistant: [saves: this user wants terse responses, no trailing summaries]
    </examples>
</type>

<type>
    <name>project</name>
    <description>Information about ongoing work, goals, initiatives, bugs, or incidents within the project.</description>
    <when_to_save>When you learn who is doing what, why, or by when</when_to_save>
    <how_to_use>Use to understand broader context and motivation behind requests</how_to_use>
    <body_structure>Lead with fact/decision, then **Why:** and **How to apply:** lines</body_structure>
    <examples>
    user: we're freezing all non-critical merges after Thursday
    assistant: [saves: merge freeze begins 2026-03-05 for mobile release]
    </examples>
</type>

<type>
    <name>reference</name>
    <description>Pointers to where information can be found in external systems.</description>
    <when_to_save>When you learn about resources in external systems and their purpose</when_to_save>
    <how_to_use>When user references an external system</how_to_use>
    <examples>
    user: check Linear project "INGEST" for pipeline bugs
    assistant: [saves: pipeline bugs tracked in Linear project "INGEST"]
    </examples>
</type>
</types>"""


WHAT_NOT_TO_SAVE_SECTION = """
## What NOT to save as memory

- **Code patterns or architecture** — derivable via grep/git/read
- **File structure** — derivable via glob/find
- **Git history** — derivable via git commands
- **Content you can read from files** — no need to memorize

Only save information that is NOT derivable from the current project state.
"""


def get_existing_memories() -> str:
    """MEMORY.md index'indeki mevcut dosyaları listele."""
    if not MEMORY_INDEX.exists():
        return ""
    
    content = MEMORY_INDEX.read_text()
    lines = content.split('\n')
    
    # Skip frontmatter
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if start == 0:
                start = i + 1
            else:
                break
    
    return '\n'.join(lines[start:]).strip()


def build_extract_prompt(
    new_message_count: int,
    existing_memories: str = "",
    skip_index: bool = False,
) -> str:
    """
    Extract memories prompt oluştur.
    
    Claude Code buildExtractAutoOnlyPrompt port.
    
    Args:
        new_message_count: Analiz edilecek son mesaj sayısı
        existing_memories: MEMORY.md index içeriği
        skip_index: True = sadece dosyaya yaz, index güncelleme
    
    Returns:
        str: Extraction agent prompt
    """
    manifest = ""
    if existing_memories:
        manifest = f"""

## Existing memory files

{existing_memories}

Check this list before writing — update an existing file rather than creating a duplicate."""

    opener = f"""You are now acting as the memory extraction subagent. Analyze the most recent ~{new_message_count} messages above and use them to update your persistent memory systems.

Available tools: Read, Grep, Glob, Bash (ls/find/cat/stat/wc/head/tail only), Edit, Write for memory directory only. rm is NOT permitted.

You have a limited turn budget. Efficient strategy:
- Turn 1: Read all files you might update in parallel
- Turn 2: Write/Edit all files in parallel
Do not interleave reads and writes.

You MUST only use content from the last ~{new_message_count} messages to update your persistent memories. Do not waste turns investigating or verifying — no grepping source files, no reading code to confirm patterns.{manifest}"""
    
    if skip_index:
        how_to_save = """
## How to save memories

Write each memory to its own file (e.g., `user_role.md`, `feedback_testing.md`) using this frontmatter format:

```markdown
---
name: {name}
description: {one-line description for future relevance}
type: {user, feedback, project, reference}
---

Memory content here.
```

- Organize memory semantically by topic, not chronologically
- Update or remove memories that are wrong or outdated
- Do not write duplicate memories. Check for existing files first."""
    else:
        how_to_save = """
## How to save memories

Saving a memory is a two-step process:

**Step 1** — write the memory to its own file (e.g., `user_role.md`, `feedback_testing.md`) using this frontmatter format:

```markdown
---
name: {name}
description: {one-line description}
type: {user, feedback, project, reference}
---

Memory content here.
```

**Step 2** — add a pointer to that file in `MEMORY.md`. `MEMORY.md` is an index, not a memory — each entry should be one line, under ~150 characters: `- [Title](file.md) — one-line hook`. Never write memory content directly into `MEMORY.md`.

- `MEMORY.md` is always loaded — lines after 200 will be truncated, keep the index concise
- Organize memory semantically by topic, not chronologically
- Update or remove memories that are wrong or outdated
- Do not write duplicate memories. Check for existing files first."""
    
    parts = [
        opener,
        "",
        "If the user explicitly asks you to remember something, save it immediately. If they ask you to forget something, find and remove the relevant entry.",
        "",
        TYPES_SECTION_INDIVIDUAL,
        WHAT_NOT_TO_SAVE_SECTION,
        "",
        how_to_save,
    ]
    
    return '\n'.join(parts)


def save_memory(
    name: str,
    description: str,
    content: str,
    memory_type: str = "project",
) -> Path:
    """
    Memory dosyası kaydet veya güncelle.
    
    Args:
        name: Memory adı (filename olarak kullanılır)
        description: Tek satırlık açıklama
        content: Memory içeriği
        memory_type: user, feedback, project, reference
    
    Returns:
        Path: Kaydedilen dosyanın path'i
    """
    # Filename oluştur
    safe_name = re.sub(r'[^\w\s-]', '', name.lower())
    safe_name = re.sub(r'[\s]+', '-', safe_name)
    filename = f"{safe_name[:50]}.md"
    filepath = MEMORY_DIR / filename
    
    # Frontmatter oluştur
    frontmatter = MEMORY_FRONTMATTER_TEMPLATE.format(
        name=name,
        description=description[:150],
        type=memory_type,
        content=content,
    )
    
    # Kaydet
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(frontmatter)
    
    return filepath


def update_memory_index(filepath: Path, name: str, description: str):
    """
    MEMORY.md index'e pointer ekle veya güncelle.
    
    Args:
        filepath: Memory dosyası path'i
        name: Memory adı
        description: Tek satırlık açıklama
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mevcut içerik
    if MEMORY_INDEX.exists():
        content = MEMORY_INDEX.read_text()
    else:
        content = ""
    
    # Pointer format: - [Name](filename.md) — description
    pointer = f"- [{name}]({filepath.name}) — {description[:100]}"
    
    # Duplicate kontrolü
    if filepath.name in content:
        # Güncelle
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if filepath.name in line:
                new_lines.append(pointer)
            else:
                new_lines.append(line)
        content = '\n'.join(new_lines)
    else:
        # Ekle
        if content.strip():
            content = content.rstrip() + '\n' + pointer + '\n'
        else:
            content = pointer + '\n'
    
    # Kaydet (200 satır limiti)
    lines = content.split('\n')
    if len(lines) > 200:
        lines = lines[:200]
    
    MEMORY_INDEX.write_text('\n'.join(lines))


def extract_and_save(
    messages: list[dict],
    min_messages: int = 5,
) -> list[Path]:
    """
    Mesajlardan memory çıkar ve kaydet.
    
    Bu fonksiyon LLM调用 gerektirdiğinden, gerçek kullanımda
    extract_memories_async() veya build_extract_prompt() kullanılır.
    
    Args:
        messages: Mesaj listesi
        min_messages: Minimum mesaj sayısı (5+ önerilir)
    
    Returns:
        list[Path]: Kaydedilen dosyalar
    """
    if len(messages) < min_messages:
        return []
    
    # Bu fonksiyonu çağırmak yerine build_extract_prompt() kullan
    # ve sonucu LLM'e gönder
    raise NotImplementedError(
        "extract_and_save requires LLM inference. "
        "Use build_extract_prompt() and send to LLM instead."
    )


# Singleton state
_extraction_state = {
    "last_run": None,
    "pending_messages": 0,
}


def should_extract(messages_count: int, threshold: int = 5) -> bool:
    """
    Memory extraction gerekip gerekmediğini kontrol et.
    
    Args:
        messages_count: Mevcut mesaj sayısı
        threshold: Kaç mesajdan sonra tetiklenecek
    
    Returns:
        bool: True = extract et
    """
    return messages_count >= threshold


def reset_extraction_state():
    """Extraction state sıfırla."""
    global _extraction_state
    _extraction_state = {
        "last_run": datetime.now().isoformat(),
        "pending_messages": 0,
    }


if __name__ == "__main__":
    print("=== Extract Memories Test ===\n")
    
    # Test build_extract_prompt
    prompt = build_extract_prompt(
        new_message_count=10,
        existing_memories="- [Test](test.md) — test memory",
        skip_index=False,
    )
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Prompt preview:\n{prompt[:500]}...")
    
    # Test existing memories
    existing = get_existing_memories()
    print(f"\nExisting memories: {len(existing)} chars")
    
    # Test save_memory
    print("\n--- Save Memory Test ---")
    filepath = save_memory(
        name="Test memory",
        description="This is a test memory",
        content="Test content for the memory file.",
        memory_type="project",
    )
    print(f"Saved: {filepath}")
    
    # Test update_memory_index
    update_memory_index(filepath, "Test memory", "This is a test memory")
    print(f"Index updated")
    
    # Show index
    if MEMORY_INDEX.exists():
        print(f"\nMEMORY.md content:\n{MEMORY_INDEX.read_text()[:300]}...")
