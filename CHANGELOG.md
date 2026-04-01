# Release v1.0.0 — Initial Release

**Date:** 2026-04-01  
**Developer:** Ayzekdiolar

## New Features

### 42 Tools
- **Core (8):** Bash, Read, Write, Edit, Glob, Grep, Think, Task
- **Extended (19):** TodoWrite, WebFetch, WebSearch, Brief, SendMessage, Task CRUD, AskUserQuestion, ToolSearch, Sleep, Config, NotebookEdit, MCP Resources, SyntheticOutput
- **Advanced (15):** LSP, REPL, Plan Mode (4 tools), Worktree (3 tools), Skill, AnswerQuestion, Agent, Runtime, AnalyzeContext, MCP, Schedule

### Harness System
- **Context Builder:** Automatic SOUL + MEMORY + USER merging
- **State Management:** Persistent state in `.harness/` directory
- **Policy Engine:** Tool-based permissions + approval flow
- **Cache:** 60 second TTL for fast context analysis
- **Event Bus:** Async event handling
- **Agent Registry:** Sub-agent tracking + steering
- **Skill Registry:** Skill creation with wizard mode

### Installation Wizard
- Selective installation (Core/Extended/Advanced/All)
- Automatic state directory configuration
- Policy engine configuration
- Cache system settings

### Documentation
- README.md — Overview
- docs/USAGE.md — Detailed usage guide
- demos/ — 3 example workflows (cargo research, plan mode, REPL)
- tests/test_all.py — Test suite

## Technical Details

- **Python:** 3.10+
- **Dependencies:** openclaudeclaw, pathlib, jsonschema, pyyaml
- **License:** MIT
- **Size:** ~200 KB (source)

## Installation

```bash
git clone https://github.com/ayzekhdawy/OpenClaudeClaw.git
cd OpenClaudeClaw
python3 install.py
```

## Demo

```bash
python3 demos/demo1_cargo_research.py
python3 demos/demo2_plan_lsp.py
python3 demos/demo3_repl.py
```

## Testing

```bash
python3 tests/test_all.py
```

---

**Note:** This project is inspired by Claude Code but written entirely for Python/OpenClaw.
