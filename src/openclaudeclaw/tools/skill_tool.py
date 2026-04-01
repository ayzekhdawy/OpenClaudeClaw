"""
SkillTool — Skill Management System
──────────────────────────────────────────────────────────
Claude Code SkillTool referansı.
Skills: find, invoke, list, create, update, wizard.

Claude Code'da skill sistemi: .claude/commands/ dizini altında
her skill bir .md dosyası. Bizde: ~/.openclaw/skills/ dizini.
"""

import subprocess
import time
import json
import os
import re
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


SKILLS_DIR = Path("/home/ayzek/.openclaw/skills")
COMMANDS_DIR = Path("/home/ayzek/.openclaw/workspace/.claude/commands")


class SkillTool(BaseTool):
    """
    Skill management - Claude Code pattern.

    Commands:
    - find: Find skills matching query
    - list: List all available skills
    - invoke: Execute a skill by name
    - create: Create new skill (wizard mode)
    - update: Update existing skill
    - describe: Show skill details
    - docs: Show skill documentation

    Patterns: skill, skill yönet, komut oluştur, beceri
    """
    name = "Skill"
    category = ToolCategory.UTILITY
    patterns = ["skill", "komut", "create skill", "skill ara", "skill çağır"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        command = input_data.get("command", "list")
        name = input_data.get("name", "")
        query = input_data.get("query", "")
        args = input_data.get("args", {})

        if command == "find":
            return self._find_skills(query, start)
        elif command == "list":
            return self._list_skills(start)
        elif command == "invoke":
            return self._invoke_skill(name, args, start)
        elif command == "create":
            return self._create_skill_wizard(input_data, start)
        elif command == "update":
            return self._update_skill(name, input_data, start)
        elif command == "describe":
            return self._describe_skill(name, start)
        elif command == "docs":
            return self._skill_docs(name, start)
        else:
            return ToolResult(
                self.name, False, "",
                f"Unknown command: {command}. Use: find, list, invoke, create, update, describe, docs",
                int((time.time()-start)*1000)
            )

    def _find_skills(self, query: str, start: float) -> ToolResult:
        """Find skills matching query."""
        if not query:
            return ToolResult(self.name, False, "", "query is required", int((time.time()-start)*1000))

        query_lower = query.lower()
        results = []

        # Search in skills dir
        if SKILLS_DIR.exists():
            for skill_file in SKILLS_DIR.rglob("SKILL.md"):
                skill_name = skill_file.parent.name.replace(":", "/")
                # Read description from skill
                try:
                    content = skill_file.read_text()
                    desc_match = re.search(r'description[:\s]+([^\n]+)', content, re.IGNORECASE)
                    desc = desc_match.group(1) if desc_match else ""
                    if query_lower in skill_name.lower() or query_lower in desc.lower():
                        results.append(f"  {skill_name}: {desc[:60]}")
                except:
                    pass

        # Search in commands dir
        if COMMANDS_DIR.exists():
            for cmd_file in COMMANDS_DIR.rglob("*.md"):
                try:
                    content = cmd_file.read_text()
                    first_line = content.split("\n")[0].strip()
                    if query_lower in cmd_file.stem.lower() or query_lower in first_line.lower():
                        results.append(f"  /{cmd_file.stem}: {first_line[:60]}")
                except:
                    pass

        if not results:
            return ToolResult(
                self.name, True,
                f"No skills found matching '{query}'",
                int((time.time()-start)*1000)
            )

        return ToolResult(
            self.name, True,
            f"Skills matching '{query}' ({len(results)}):\n" + "\n".join(results),
            int((time.time()-start)*1000)
        )

    def _list_skills(self, start: float) -> ToolResult:
        """List all available skills."""
        skills = []

        # List skills dir
        if SKILLS_DIR.exists():
            for skill_dir in sorted(SKILLS_DIR.iterdir()):
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        try:
                            content = skill_file.read_text()
                            desc_match = re.search(r'description[:\s]+([^\n]+)', content, re.IGNORECASE)
                            desc = desc_match.group(1) if desc_match else ""
                            skills.append(f"  {skill_dir.name}: {desc[:50]}")
                        except:
                            skills.append(f"  {skill_dir.name}")
                    else:
                        skills.append(f"  {skill_dir.name} (no SKILL.md)")

        # List commands
        commands = []
        if COMMANDS_DIR.exists():
            for cmd_file in sorted(COMMANDS_DIR.rglob("*.md")):
                try:
                    content = cmd_file.read_text()
                    first_line = content.split("\n")[0].strip()
                    commands.append(f"  /{cmd_file.stem}: {first_line[:50]}")
                except:
                    commands.append(f"  /{cmd_file.stem}")

        output = "Skills:\n" + "\n".join(skills) if skills else "No skills found."
        output += "\n\nCommands:\n" + "\n".join(commands) if commands else "\n\nNo commands found."

        return ToolResult(
            self.name, True, output, int((time.time()-start)*1000)
        )

    def _invoke_skill(self, name: str, args: dict, start: float) -> ToolResult:
        """Invoke a skill by name."""
        if not name:
            return ToolResult(self.name, False, "", "name is required", int((time.time()-start)*1000))

        # Find skill
        skill_path = None

        # Check skills dir
        skill_dir = SKILLS_DIR / name.replace("/", ":")
        if skill_dir.exists():
            skill_path = skill_dir

        # Check commands dir
        if not skill_path and COMMANDS_DIR.exists():
            for cmd_file in COMMANDS_DIR.rglob(f"{name}.md"):
                skill_path = cmd_file
                break

        if not skill_path:
            return ToolResult(
                self.name, False, "",
                f"Skill not found: {name}",
                int((time.time()-start)*1000)
            )

        # Read skill content
        try:
            content = skill_path.read_text() if skill_path.is_file() else (skill_path / "SKILL.md").read_text()
        except Exception as e:
            return ToolResult(self.name, False, "", f"Cannot read skill: {e}", int((time.time()-start)*1000))

        return ToolResult(
            self.name, True,
            f"Skill: {name}\n\n{content[:2000]}",
            int((time.time()-start)*1000),
            metadata={"skill_path": str(skill_path)}
        )

    def _create_skill_wizard(self, input_data: dict, start: float) -> ToolResult:
        """Create new skill using wizard questions."""
        # Wizard mode - ask user questions
        name = input_data.get("name", "")
        description = input_data.get("description", "")
        category = input_data.get("category", "general")
        instructions = input_data.get("instructions", "")
        triggers = input_data.get("triggers", [])

        if not name:
            return ToolResult(
                self.name, False, "",
                "[WIZARD] Skill name is required. Provide: name, description, category, instructions, triggers",
                int((time.time()-start)*1000)
            )

        # Create skill directory
        skill_dir = SKILLS_DIR / f"user:{name}"
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Create SKILL.md
        skill_md = f"""# Skill: {name}

description: {description or f"User-created skill: {name}"}
category: {category}
triggers: {', '.join(triggers) if triggers else 'manual'}

## Instructions

{instructions or f"Describe what this skill does..."}

## Examples

```
Example 1: ...
Example 2: ...
```

## Notes

- Created: {time.strftime("%Y-%m-%d")}
- Author: İshak
"""

        (skill_dir / "SKILL.md").write_text(skill_md)

        # Create scripts directory
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        return ToolResult(
            self.name, True,
            f"[WIZARD] Skill created: {name}\nPath: {skill_dir}\n\n{triggers}",
            int((time.time()-start)*1000),
            metadata={"skill_path": str(skill_dir)}
        )

    def _update_skill(self, name: str, input_data: dict, start: float) -> ToolResult:
        """Update existing skill."""
        if not name:
            return ToolResult(self.name, False, "", "name is required", int((time.time()-start)*1000))

        # Find skill
        skill_dir = SKILLS_DIR / name.replace("/", ":")
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            return ToolResult(self.name, False, "", f"Skill not found: {name}", int((time.time()-start)*1000))

        try:
            content = skill_file.read_text()

            # Update fields
            if "description" in input_data:
                content = re.sub(
                    r'description:.*',
                    f'description: {input_data["description"]}',
                    content
                )
            if "instructions" in input_data:
                if "## Instructions" in content:
                    content = re.sub(
                        r'## Instructions.*',
                        f'## Instructions\n\n{input_data["instructions"]}',
                        content,
                        flags=re.DOTALL
                    )

            skill_file.write_text(content)

            return ToolResult(
                self.name, True,
                f"Skill updated: {name}",
                int((time.time()-start)*1000)
            )

        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))

    def _describe_skill(self, name: str, start: float) -> ToolResult:
        """Show detailed skill description."""
        if not name:
            return ToolResult(self.name, False, "", "name is required", int((time.time()-start)*1000))

        skill_dir = SKILLS_DIR / name.replace("/", ":")
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            return ToolResult(self.name, False, "", f"Skill not found: {name}", int((time.time()-start)*1000))

        try:
            content = skill_file.read_text()
            return ToolResult(
                self.name, True, content,
                int((time.time()-start)*1000)
            )
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))

    def _skill_docs(self, name: str, start: float) -> ToolResult:
        """Show skill documentation."""
        docs = """
SkillTool Documentation
═══════════════════════════

Commands:
  find <query>     - Find skills matching query
  list             - List all skills
  invoke <name>    - Execute a skill
  create           - Create new skill (wizard)
  update <name>    - Update skill
  describe <name>  - Show skill details
  docs <name>      - Show documentation

Examples:
  skill.find(query="coffee")
  skill.list()
  skill.invoke(name="research")
  skill.create(name="my-skill", description="...", category="general")

Skill Locations:
  ~/.openclaw/skills/     - User skills
  ~/.openclaw/workspace/.claude/commands/  - Commands
"""
        return ToolResult(self.name, True, docs, int((time.time()-start)*1000))
