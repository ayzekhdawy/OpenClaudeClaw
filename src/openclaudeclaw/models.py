"""
Harness Models — Data structures for tool system
──────────────────────────────────────────────
Clean-room implementation, not copied from any source.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum


class ToolCategory(Enum):
    """Tool categories matching Claude Code patterns."""
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    SEARCH = "search"
    EXECUTE = "execute"
    GIT = "git"
    INTEGRATION = "integration"
    UTILITY = "utility"
    MEMORY = "memory"
    AGENT = "agent"
    NATURAL = "natural"


class BaseTool:
    """Base class for all tools. Single source of truth."""
    name: str = ""
    description: str = ""
    category: ToolCategory = ToolCategory.EXECUTE
    patterns: list[str] = []
    readonly: bool = False

    def __init__(self):
        self.spec = ToolSpec(
            name=self.name,
            description=self.description,
            category=self.category,
            patterns=self.patterns,
            readonly=self.readonly,
        )

    def execute(self, input_data: dict, context: dict | None = None) -> "ToolResult":
        raise NotImplementedError


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    success: bool
    output: str
    error: Optional[str] = None
    duration_ms: int = 0
    cost_usd: float = 0.0
    approval_state: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ToolUse:
    """A tool use in a session."""
    tool_name: str
    input_data: dict
    result: Optional[ToolResult] = None
    tool_use_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CostSummary:
    """Cost tracking summary."""
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    api_duration_ms: int = 0
    wall_duration_ms: int = 0
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add(self, cost_usd: float, input_tokens: int, output_tokens: int, duration_ms: int):
        """Add costs from a single API call."""
        self.total_cost_usd += cost_usd
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.api_duration_ms += duration_ms
    
    def format(self) -> str:
        """Format cost summary for display."""
        return (
            f"Total cost: ${self.total_cost_usd:.4f}\n"
            f"Input tokens: {self.total_input_tokens:,}\n"
            f"Output tokens: {self.total_output_tokens:,}\n"
            f"API duration: {self.api_duration_ms/1000:.1f}s\n"
            f"Wall duration: {self.wall_duration_ms/1000:.1f}s"
        )


@dataclass
class SessionManifest:
    """Manifest of a session's tools and capabilities."""
    session_id: str
    tools: list[str]
    context_files: int = 0
    workspace_size_mb: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "tools": self.tools,
            "context_files": self.context_files,
            "workspace_size_mb": self.workspace_size_mb,
            "created_at": self.created_at,
        }


@dataclass
class WorkspaceAnalysis:
    """Analysis of the workspace."""
    root: str
    total_files: int = 0
    code_files: int = 0
    test_files: int = 0
    total_size_mb: float = 0.0
    languages: dict[str, int] = field(default_factory=dict)
    git_dirty: bool = False
    last_commit: Optional[str] = None
    
    def summary(self) -> str:
        return (
            f"Files: {self.total_files} "
            f"(code: {self.code_files}, test: {self.test_files})\n"
            f"Size: {self.total_size_mb:.1f}MB\n"
            f"Languages: {', '.join(f'{k}:{v}' for k,v in self.languages.items())}\n"
            f"Git: {'dirty' if self.git_dirty else 'clean'}"
        )


@dataclass
class CommandSpec:
    """Specification for a command."""
    name: str
    description: str
    category: ToolCategory
    patterns: list[str] = field(default_factory=list)
    requires_approval: bool = False
    readonly: bool = False


@dataclass
class ToolSpec:
    """Specification for a tool."""
    name: str
    description: str
    category: ToolCategory
    patterns: list[str] = field(default_factory=list)
    readonly: bool = False
    enabled: bool = True
