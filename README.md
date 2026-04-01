# OpenClaudeClaw

**Advanced harness system for OpenClaw** — 42 tools, state management, context builder, policy engine.

## Features

- **42 Tools** — Bash, Read, Write, Edit, Glob, Grep, LSP, REPL, Task, MCP, Plan Mode, Worktree and more
- **Harness Context** — Automatic SOUL, MEMORY, USER merging
- **Esra Runtime** — 5-step reasoning chain (Dalio process)
- **State Management** — Persistent state in `.harness/` directory
- **Policy Engine** — Tool-based permissions + approval flow
- **Cache System** — 60 second TTL for fast context analysis
- **Event Bus** — Async event handling
- **Agent Registry** — Sub-agent tracking + steering
- **Skill Registry** — Skill creation with wizard mode
- **Self-Evolution** — Automatic error logging + pattern promotion

## Installation

```bash
# Run OpenClaudeClaw installation wizard
python3 install.py
```

The installation wizard will ask you:
- Which tools do you want to install? (Core/Extended/All)
- Where should the state directory be? (default: `.harness/`)
- Should Policy Engine be enabled?
- Should Cache System be enabled?

## Quick Start

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

# Create runtime
runtime = HarnessRuntime()

# Access tool pool
pool = get_tool_pool()

# Run a tool
result = pool.execute("Bash", {"command": "echo 'Hello World'"})
print(result.output)

# Use context builder
from openclaudeclaw.context_builder import build_context
ctx = build_context("Research cargo prices for Flech")
print(ctx.full_prompt)
```

## Tool Categories

### Core Tools (8)
- `Bash` — Run shell commands
- `Read` — Read files
- `Write` — Write files
- `Edit` — Edit files
- `Glob` — Find files (pattern)
- `Grep` — Search content
- `Think` — Thought notes
- `Task` — Task management

### Extended Tools (19)
- `TodoWrite` — Todo list management
- `WebFetch` — Fetch web pages
- `WebSearch` — Web search (Brave API)
- `Brief` — Send message to user
- `SendMessage` — Send message (webhook)
- `TaskCreate/Get/Update/Stop` — Task CRUD
- `AskUserQuestion` — Multi-question UI
- `ToolSearch` — Search tools
- `Sleep` — Wait (ms)
- `Config` — Configuration read/write
- `NotebookEdit` — Jupyter notebook editor
- `ListMcpResources` — MCP server list
- `ReadMcpResource` — MCP resource reader
- `SyntheticOutput` — Template-based output

### Advanced Tools (15)
- `LSP` — Code intelligence (goto definition, references, symbols)
- `REPL` — Interactive Python shell
- `EnterPlanMode/ExitPlanMode/UpdatePlan/PlanStatus` — Planning system
- `EnterWorktree/ExitWorktree/WorktreeList` — Git worktree management
- `Skill` — Skill registry + wizard mode
- `AnswerQuestion` — Question answering
- `Agent` — Sub-agent management
- `Runtime` — Runtime status
- `AnalyzeContext` — Context analysis + cache
- `MCP` — MCP wrapper
- `Schedule` — Cron job management

## Project Structure

```
openclaudeclaw/
├── src/
│   └── openclaudeclaw/
│       ├── __init__.py
│       ├── runtime.py          # HarnessRuntime
│       ├── esra_runtime.py     # Advanced reasoning (5-step chain)
│       ├── tool_pool.py        # 42 tool registry
│       ├── context_builder.py  # Context merge
│       ├── policy_engine.py    # Permission system
│       ├── models.py           # Data models
│       ├── state.py            # State management
│       ├── event_bus.py        # Event handling
│       ├── agent_registry.py   # Sub-agent tracking
│       ├── skills.py           # Skill registry
│       ├── schedule.py         # Cron store
│       └── tools/              # 42 tool implementations
├── docs/
│   ├── ARCHITECTURE.md         # System architecture
│   ├── PHILOSOPHY.md           # Decision-making framework
│   ├── ORCHESTRATION.md        # Multi-agent patterns
│   ├── SELF_EVOLUTION.md       # Learning system
│   └── USAGE.md                # Usage guide
├── examples/
│   ├── README.md
│   ├── example1_cargo_research.py      # Reasoning chain demo
│   ├── example2_multi_agent.py         # Orchestration demo
│   └── example3_self_correction.py     # Learning demo
├── install.py                  # Installation wizard
├── README.md
├── LICENSE
└── requirements.txt
```

## License

MIT License — See `LICENSE` file for details.

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## Support

- GitHub Issues: [Report bug or request feature]
- Discord: [OpenClaw community]
- Documentation: `docs/` directory

---

**Developer:** Ayzekdiolar  
**Version:** 1.0.0  
**Last Updated:** 2026-04-01
