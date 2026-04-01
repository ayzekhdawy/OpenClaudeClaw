# OpenClaudeClaw

**Advanced Harness System for OpenClaw**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Tools: 42](https://img.shields.io/badge/tools-42-green.svg)](docs/USAGE.md)

OpenClaudeClaw is a production-ready harness system for OpenClaw, providing 42 tools, advanced reasoning capabilities, and comprehensive multi-agent orchestration patterns.

---

## What It Provides

- **42 Production Tools** — File operations, web search, LSP code intelligence, REPL, Git worktrees, MCP integration
- **5-Step Reasoning Chain** — Dalio-based decision framework (Define → Decompose → Research → Synthesize → Validate → Execute)
- **Multi-Agent Orchestration** — Coordinate coding agents, research agents, and workflow executors
- **Self-Evolution System** — Automatic error logging, pattern detection, behavioral updates
- **Context Management** — Intelligent merging of persona, memory, and user context
- **Policy Engine** — Tool-level permissions with approval workflows
- **State Persistence** — Survives restarts via `.harness/` directory

---

## Installation

```bash
git clone https://github.com/ayzekhdawy/OpenClaudeClaw.git
cd OpenClaudeClaw
python3 install.py
```

The interactive wizard guides you through:
- Tool selection (Core only / Core+Extended / Full 42-tool install)
- State directory configuration
- Policy engine setup
- Cache system preferences

---

## Quick Start

### Basic Usage

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

# Initialize runtime
runtime = HarnessRuntime()
pool = get_tool_pool()

# Execute a tool
result = pool.execute("Bash", {"command": "ls -la"})
print(result.output)
```

### Advanced Reasoning (5-Step Chain)

```python
from openclaudeclaw.advanced_reasoning import AdvancedReasoningRuntime

runtime = AdvancedReasoningRuntime()
result = runtime.execute_with_reasoning(
    "Research cargo prices for glass products in Turkey"
)

# Access full reasoning chain
for step in result.reasoning_chain:
    print(f"[{step.name}] {step.output}")
```

### Context Building

```python
from openclaudeclaw.context_builder import build_context

ctx = build_context("Analyze Q1 financial data")
print(ctx.full_prompt)  # Merged SOUL + MEMORY + USER context
```

---

## Tool Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Core** | 8 | Bash, Read, Write, Edit, Glob, Grep, Think, Task |
| **Extended** | 19 | WebSearch, WebFetch, TodoWrite, Brief, Task CRUD, MCP Resources |
| **Advanced** | 15 | LSP, REPL, Plan Mode (4), Worktree (3), Skill Registry |

**Full tool list:** [`docs/USAGE.md`](docs/USAGE.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture, component diagrams, performance characteristics |
| [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) | Decision-making framework (Dalio, Laloux, Kilani integration) |
| [`docs/ORCHESTRATION.md`](docs/ORCHESTRATION.md) | Multi-agent patterns, task routing, failure handling |
| [`docs/SELF_EVOLUTION.md`](docs/SELF_EVOLUTION.md) | Error classification, learning pipeline, behavior updates |
| [`docs/USAGE.md`](docs/USAGE.md) | Complete tool reference with examples |

---

## Examples

Three comprehensive examples demonstrate real-world usage:

### Example 1: Cargo Price Research
Full 5-step reasoning chain with web search coordination.

```bash
python3 examples/example1_cargo_research.py
```

### Example 2: Multi-Agent Orchestration
Decompose complex tasks, route to appropriate agents, synthesize results.

```bash
python3 examples/example2_multi_agent.py
```

### Example 3: Self-Correction & Learning
Error logging, pattern detection, automatic rule promotion.

```bash
python3 examples/example3_self_correction.py
```

**Examples overview:** [`examples/README.md`](examples/README.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   OpenClaudeClaw                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   Runtime    │  │  Tool Pool   │  │    Context    │ │
│  │  (Harness)   │  │  (42 tools)  │  │    Builder    │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
│         │                 │                  │          │
│  ┌──────┴─────────────────┴──────────────────┴──────┐  │
│  │              Integration Layer                    │  │
│  └──────┬─────────────────┬──────────────────┬──────┘  │
│         │                 │                  │          │
│  ┌──────┴──────┐  ┌───────┴───────┐  ┌──────┴──────┐  │
│  │   Policy    │  │     State     │  │    Event    │  │
│  │   Engine    │  │   Manager     │  │    Bus      │  │
│  └─────────────┘  └───────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Deep dive:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Performance Characteristics

| Operation | Expected Latency |
|-----------|------------------|
| Import | ~0.6s |
| Tool pool initialization | ~0.6s |
| Simple tool execution | ~0.0–0.1s |
| Complex tool execution | ~0.5–0.7s |
| Context build (cached) | ~0ms |
| Context build (fresh) | ~0.2s |

---

## Requirements

- Python 3.10+
- OpenClaw environment
- Network access (for WebSearch, WebFetch, MCP tools)

**Dependencies:** See `requirements.txt`

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-tool`)
3. Implement your changes with tests
4. Run the test suite (`python3 tests/test_all.py`)
5. Commit your changes (`git commit -m 'Add new tool: X'`)
6. Push to the branch (`git push origin feature/new-tool`)
7. Open a Pull Request

**Contribution guidelines:** Please ensure your code follows existing patterns and includes appropriate documentation.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Support

- **Issues:** [GitHub Issues](https://github.com/ayzekhdawy/OpenClaudeClaw/issues)
- **Community:** [OpenClaw Discord](https://discord.gg/clawd)
- **Documentation:** See `docs/` directory

---

**Version:** 1.0.0  
**Release Date:** 2026-04-01  
**Developer:** Ayzekdiolar
