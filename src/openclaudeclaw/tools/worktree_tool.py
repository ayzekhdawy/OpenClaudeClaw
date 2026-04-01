"""
WorktreeTool — Git Worktree Management
──────────────────────────────────────────────────
Claude Code EnterWorktreeTool / ExitWorktreeTool referansı.
Git worktree oluşturur ve yönetir.
"""

import subprocess
import time
import json
import re
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


_WORKTREE_STATE = Path("/home/ayzek/.openclaw/workspace/.harness/worktree_state.json")


class EnterWorktreeTool(BaseTool):
    """
    Create and enter a git worktree - Claude Code pattern.

    Input:
    - name: Optional worktree name (auto-generated if not provided)
    - branch: Optional branch name

    Patterns: worktree, git branch, branch oluştur, isolated git
    """
    name = "EnterWorktree"
    category = ToolCategory.EXECUTE
    patterns = ["worktree", "git branch", "branch oluştur", "yeni branch"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        name = input_data.get("name", "")
        branch = input_data.get("branch", "")
        path = input_data.get("path", "")

        return self._create_worktree(name, branch, path, start)

    def _create_worktree(self, name: str, branch: str, path: str, start: float) -> ToolResult:
        """Create a git worktree."""
        workspace = Path("/home/ayzek/.openclaw/workspace")

        # Check if git repo
        git_dir = workspace / ".git"
        if not git_dir.exists():
            return ToolResult(
                self.name, False, "",
                "Not a git repository",
                int((time.time()-start)*1000)
            )

        # Generate name if not provided
        if not name:
            import uuid
            name = f"wt-{uuid.uuid4().hex[:8]}"

        # Worktree path
        if not path:
            worktrees_dir = workspace / ".worktrees"
            worktrees_dir.mkdir(exist_ok=True)
            worktree_path = worktrees_dir / name
        else:
            worktree_path = Path(path)

        # Create branch if needed
        if branch:
            # Check if branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # Create branch
                subprocess.run(
                    ["git", "branch", branch],
                    cwd=workspace,
                    capture_output=True
                )

        # Build git worktree command
        cmd = ["git", "worktree", "add"]
        if branch:
            cmd += ["-b", branch]
        cmd.append(str(worktree_path))
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return ToolResult(
                self.name, False, "",
                f"Worktree create failed: {result.stderr}",
                int((time.time()-start)*1000)
            )

        # Save state
        state = {
            "active": True,
            "worktree_path": str(worktree_path),
            "name": name,
            "branch": branch or "HEAD",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        _WORKTREE_STATE.parent.mkdir(parents=True, exist_ok=True)
        _WORKTREE_STATE.write_text(json.dumps(state))

        return ToolResult(
            self.name, True,
            f"Worktree created: {worktree_path}\nBranch: {branch or 'HEAD'}\n\nUse 'ExitWorktree' to leave.",
            duration_ms=int((time.time()-start)*1000),
            metadata={"path": str(worktree_path), "name": name}
        )


class ExitWorktreeTool(BaseTool):
    """
    Exit current worktree - Claude Code pattern.

    Patterns: exit worktree, worktree bitir, branch bitir
    """
    name = "ExitWorktree"
    category = ToolCategory.EXECUTE
    patterns = ["exit worktree", "worktree bitir", "branch bitir"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        if not _WORKTREE_STATE.exists():
            return ToolResult(
                self.name, False, "",
                "Not in a worktree session",
                int((time.time()-start)*1000)
            )

        state = json.loads(_WORKTREE_STATE.read_text())
        worktree_path = state.get("worktree_path", "")

        # Remove worktree
        workspace = Path("/home/ayzek/.openclaw/workspace")
        result = subprocess.run(
            ["git", "worktree", "remove", worktree_path, "--force"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Also prune
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        _WORKTREE_STATE.unlink(missing_ok=True)

        return ToolResult(
            self.name, True,
            f"Worktree removed: {worktree_path}",
            duration_ms=int((time.time()-start)*1000)
        )


class WorktreeListTool(BaseTool):
    """
    List all worktrees - Claude Code pattern.

    Patterns: list worktrees, worktree list, worktree durumu
    """
    name = "WorktreeList"
    category = ToolCategory.READ
    patterns = ["list worktrees", "worktree list", "worktree durumu"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        workspace = Path("/home/ayzek/.openclaw/workspace")

        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return ToolResult(
                self.name, False, "",
                f"git worktree list failed: {result.stderr}",
                int((time.time()-start)*1000)
            )

        output = result.stdout.strip() if result.stdout.strip() else "No worktrees found."

        return ToolResult(
            self.name, True,
            f"Git Worktrees:\n{output}",
            duration_ms=int((time.time()-start)*1000)
        )
