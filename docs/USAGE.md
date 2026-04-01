# OpenClaudeClaw Documentation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ayzekhdawy/OpenClaudeClaw.git
cd OpenClaudeClaw
```

2. Run the installation wizard:
```bash
python3 install.py
```

3. The wizard will ask you:
   - Which tool packages do you want to install? (Core/Extended/Advanced/All)
   - Where should the state directory be?
   - Should Policy Engine be enabled?
   - Should Cache System be enabled?

## Quick Start

### Basic Usage

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

# Create runtime
runtime = HarnessRuntime()

# Access tool pool
pool = get_tool_pool()

# Run a bash command
result = pool.execute("Bash", {"command": "ls -la"})
print(result.output)

# Read a file
result = pool.execute("Read", {"path": "README.md"})
print(result.output[:500])
```

### Context Builder

```python
from openclaudeclaw.context_builder import build_context

# Build context for a task
ctx = build_context("Research cargo prices for Flech")

# Get full prompt
print(ctx.full_prompt)

# Access components
print(ctx.persona)      # SOUL.md content
print(ctx.user)         # USER.md content
print(ctx.memory)       # MEMORY.md content
print(ctx.task_context) # Task-specific context
```

### Task Management

```python
# Create a new task
task = pool.execute("TaskCreate", {
    "description": "Compare cargo prices",
    "priority": "high"
})

# Update task
pool.execute("TaskUpdate", {
    "task_id": task.task_id,
    "status": "in_progress"
})

# Complete task
pool.execute("TaskStop", {"task_id": task.task_id})
```

### Plan Mode

```python
# Enter plan mode
pool.execute("EnterPlanMode", {
    "mode": "plan",
    "description": "Cargo research plan"
})

# Check plan status
result = pool.execute("PlanStatus", {})
print(result.output)

# Exit plan mode
pool.execute("ExitPlanMode", {"action": "discard"})
```

### LSP (Code Intelligence)

```python
# Get symbol list
result = pool.execute("LSP", {
    "operation": "documentSymbol",
    "file_path": "src/openclaudeclaw/tool_pool.py"
})
print(result.output)

# Go to definition
result = pool.execute("LSP", {
    "operation": "goToDefinition",
    "file_path": "src/openclaudeclaw/tool_pool.py",
    "line": 42,
    "character": 10
})
```

### REPL (Interactive Python)

```python
# Start REPL
pool.execute("REPL", {"command": "start"})

# Run code
result = pool.execute("REPL", {
    "command": "eval",
    "code": "import json; print(json.dumps({'status': 'ok'}))"
})
print(result.output)

# Stop REPL
pool.execute("REPL", {"command": "stop"})
```

## Tool Reference

### Core Tools (8)

| Tool | Description | Input |
|------|-------------|-------|
| `Bash` | Run shell command | `{"command": "ls -la", "cwd": "/path", "timeout": 30}` |
| `Read` | Read file | `{"path": "file.txt", "offset": 0, "limit": 100}` |
| `Write` | Write file | `{"path": "file.txt", "content": "..."}` |
| `Edit` | Edit file | `{"path": "file.txt", "old_text": "...", "new_text": "..."}` |
| `Glob` | Find files (pattern) | `{"pattern": "*.py"}` |
| `Grep` | Search content | `{"pattern": "class ", "path": "src/"}` |
| `Think` | Thought note | `{"thought": "For this task..."}` |
| `Task` | Task management | `{"description": "...", "priority": "high"}` |

### Extended Tools (19)

| Tool | Description |
|------|-------------|
| `TodoWrite` | Todo list management |
| `WebFetch` | Fetch web page |
| `WebSearch` | Web search (Brave API) |
| `Brief` | Send message to user |
| `SendMessage` | Send message (webhook) |
| `TaskCreate` | Create new task |
| `TaskGet` | Get task |
| `TaskUpdate` | Update task |
| `TaskStop` | Stop task |
| `AskUserQuestion` | Multi-question UI |
| `ToolSearch` | Search tools |
| `Sleep` | Wait (ms) |
| `Config` | Configuration read/write |
| `NotebookEdit` | Jupyter notebook editor |
| `ListMcpResources` | MCP server list |
| `ReadMcpResource` | MCP resource reader |
| `SyntheticOutput` | Template-based output |

### Advanced Tools (15)

| Tool | Description |
|------|-------------|
| `LSP` | Code intelligence (AST-based) |
| `REPL` | Interactive Python shell |
| `EnterPlanMode` | Enter plan mode |
| `ExitPlanMode` | Exit plan mode |
| `UpdatePlan` | Update plan |
| `PlanStatus` | Plan status |
| `EnterWorktree` | Create/open Git worktree |
| `ExitWorktree` | Exit worktree |
| `WorktreeList` | Worktree list |
| `Skill` | Skill registry + wizard |
| `AnswerQuestion` | Answer question |
| `Agent` | Sub-agent management |
| `Runtime` | Runtime status |
| `AnalyzeContext` | Context analysis + cache |
| `MCP` | MCP wrapper |
| `Schedule` | Cron job management |

## Configuration

### Environment Variables

Defined in `.openclaudeclaw.env`:

```bash
OPENCLAUDECLAW_VERSION=1.0.0
STATE_DIR=.harness
POLICY_ENGINE=true
CACHE_ENABLED=true
CACHE_TTL=60
LOG_LEVEL=INFO
```

### Policy Engine

`.harness/permissions.json` — Tool-based permissions:

```json
{
  "auto_approve": ["Read", "Glob", "Think", "TodoWrite"],
  "require_approval": ["Bash", "Write", "Edit", "WebFetch"],
  "deny": []
}
```

### Cache System

`.harness/cache_config.json`:

```json
{
  "enabled": true,
  "ttl_seconds": 60,
  "max_entries": 100
}
```

## State Management

State files are stored in `.harness/` directory:

- `tasks.json` — Task state
- `plan_state.json` — Plan mode state
- `worktree_state.json` — Worktree state
- `repl_state.json` — REPL state
- `todo_state.json` — Todo state
- `permissions.json` — Policy permissions
- `cache_config.json` — Cache settings

## Testing

```bash
# Run all tests
pytest tests/

# Single tool test
python3 -c "
from openclaudeclaw import get_tool_pool
pool = get_tool_pool()
r = pool.execute('Bash', {'command': 'echo 1'})
print('OK' if r.success else 'FAIL')
"
```

## FAQ

**Q: How does it integrate with OpenClaw?**
A: OpenClaudeClaw runs on top of OpenClaw. Add harness path to `openclaw.json` configuration.

**Q: Is it the same as Claude Code?**
A: It's inspired by Claude Code but written entirely for Python/OpenClaw.

**Q: Are all 42 tools necessary?**
A: No. The installation wizard lets you select only what you need.

**Q: What does the cache do?**
A: Caches context analysis for 60 seconds. Same query returns in 0ms.

---

**Developer:** Ayzekdiolar  
**Version:** 1.0.0  
**License:** MIT
