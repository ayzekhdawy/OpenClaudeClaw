"""
Harness skill discovery/load surface
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
SKILLS_DIRS = [WORKSPACE / "skills"]


class SkillRegistry:
    def __init__(self, roots: list[Path] | None = None):
        self.roots = roots or SKILLS_DIRS

    def discover(self) -> list[dict]:
        results = []
        for root in self.roots:
            if not root.exists():
                continue
            for skill_md in root.rglob("SKILL.md"):
                skill_dir = skill_md.parent
                results.append({
                    "name": skill_dir.name,
                    "path": str(skill_md),
                    "root": str(root),
                })
        return sorted(results, key=lambda x: x["name"])

    def load(self, name: str) -> Optional[dict]:
        for item in self.discover():
            if item["name"] == name:
                path = Path(item["path"])
                return {**item, "content": path.read_text(errors="ignore")}
        return None


_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
