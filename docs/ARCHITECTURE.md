# OpenClaudeClaw Architecture

## Overview

OpenClaudeClaw is an advanced harness system for OpenClaw, inspired by Claude Code's architecture but written entirely for Python/OpenClaw ecosystem.

## Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaudeClaw                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Runtime   │  │ Tool Pool   │  │   Context   │        │
│  │  (Harness)  │  │  (42 tools) │  │   Builder   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                 │
│  ┌──────┴────────────────┴────────────────┴──────┐        │
│  │              Integration Layer                │        │
│  └──────┬────────────────┬────────────────┬──────┘        │
│         │                │                │                 │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐        │
│  │   Policy    │  │    State    │  │    Event    │        │
│  │   Engine    │  │  Manager    │  │    Bus      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 1. HarnessRuntime

The central orchestrator that manages:
- Session lifecycle
- Tool execution coordination
- Context building
- State persistence

```python
runtime = HarnessRuntime()
ctx = runtime.build_context("Research task")
result = runtime.execute_tool("WebSearch", {"query": "..."})
```

## 2. Tool Pool (42 Tools)

### Core Tools (8)
Basic file/system operations:
- `Bash` — Shell command execution
- `Read/Write/Edit` — File operations
- `Glob/Grep` — Search operations
- `Think` — Thought notes
- `Task` — Task management

### Extended Tools (19)
Productivity & integration:
- `TodoWrite` — Task lists
- `WebFetch/WebSearch` — Web operations
- `Brief/SendMessage` — User communication
- `TaskCreate/Get/Update/Stop` — CRUD
- `AskUserQuestion` — Multi-question UI
- `Config/Sleep/ToolSearch` — Utilities
- `NotebookEdit` — Jupyter support
- `MCP Resources` — MCP integration
- `SyntheticOutput` — Template output

### Advanced Tools (15)
Specialized operations:
- `LSP` — Code intelligence (AST-based)
- `REPL` — Interactive Python
- `Plan Mode (4)` — Planning system
- `Worktree (3)` — Git worktree management
- `Skill` — Skill registry + wizard
- `Agent/Runtime/AnalyzeContext` — System tools
- `MCP/Schedule` — Integration

## 3. Context Builder

Automatically merges multiple context sources:

```
┌────────────────────────────────────────┐
│         build_context(query)           │
└───────────────┬────────────────────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───┴───┐  ┌────┴────┐  ┌──┴──┐
│ SOUL  │  │ MEMORY  │  │ USER│
│(persona│  │(critical│  │(id  │
│ rules) │  │  info) │  │ +   │
│        │  │        │  │biz) │
└───┬───┘  └────┬────┘  └──┬──┘
    │           │           │
    └───────────┼───────────┘
                │
        ┌───────┴───────┐
        │  full_prompt  │
        │  (~3000 chars)│
        └───────────────┘
```

**Cache:** 60-second TTL for repeated queries.

## 4. Policy Engine

Tool-level permission system:

```json
{
  "auto_approve": ["Read", "Glob", "Think"],
  "require_approval": ["Bash", "Write", "Edit"],
  "deny": []
}
```

**Approval Flow:**
1. Tool called → Check policy
2. Auto-approve? → Execute immediately
3. Require approval? → Pause + request user confirmation
4. Denied? → Return error

## 5. State Management

Persistent state in `.harness/` directory:

| File | Purpose |
|------|---------|
| `tasks.json` | Task state |
| `plan_state.json` | Plan mode state |
| `worktree_state.json` | Git worktree state |
| `repl_state.json` | REPL session state |
| `todo_state.json` | Todo list state |
| `permissions.json` | Policy configuration |
| `cache_config.json` | Cache settings |

## 6. Event Bus

Async event handling for:
- Tool completion events
- State change notifications
- Cross-component communication

```python
event_bus.subscribe("tool.completed", handler)
event_bus.emit("tool.completed", {"tool": "Bash", "success": True})
```

## 7. Agent Registry

Sub-agent tracking and steering:

- Track active sub-agents
- Monitor resource usage
- Steer agent behavior
- Kill runaway agents

## Performance Characteristics

| Operation | Expected Time |
|-----------|---------------|
| Import | ~0.6s |
| Pool initialization | ~0.6s |
| Tool execution (simple) | ~0.0-0.1s |
| Tool execution (complex) | ~0.5-0.7s |
| Context build (cached) | ~0ms |
| Context build (fresh) | ~0.2s |

## Design Principles

1. **Modularity** — Each tool is independent
2. **Composability** — Tools can be chained
3. **Persistence** — State survives restarts
4. **Safety** — Policy engine prevents dangerous operations
5. **Performance** — Caching reduces redundant work
6. **Extensibility** — Easy to add new tools

## Installation Modes

The installation wizard offers selective installation:

- **Core Only** — 8 tools, minimal footprint
- **Core + Extended** — 27 tools, productivity focus
- **Full Install** — 42 tools, complete system

Each mode includes:
- Harness Runtime
- Context Builder
- State Management
- Policy Engine
- Cache System

---

**Version:** 1.0.0  
**License:** MIT
