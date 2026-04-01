# OpenClaudeClaw — Project Summary

## What Is This?

Advanced harness system for OpenClaw. Inspired by Claude Code but written entirely for Python/OpenClaw.

## Features

- **42 Tools** — Core, Extended, Advanced categories
- **Harness Context** — Automatic SOUL + MEMORY + USER merging
- **State Management** — Persistent state (`.harness/` directory)
- **Policy Engine** — Tool-based permissions
- **Cache** — 60s TTL
- **Event Bus** — Async event handling
- **Agent Registry** — Sub-agent tracking

## Structure

```
OpenClaudeClaw/
├── src/openclaudeclaw/    # Main package (45 modules)
│   ├── tools/             # 42 tool implementations
│   ├── runtime.py         # HarnessRuntime
│   ├── tool_pool.py       # Tool registry
│   ├── context_builder.py # Context merge
│   └── ...
├── install.py             # Installation wizard
├── demos/                 # 3 example workflows
├── tests/                 # Test suite
├── docs/                  # Documentation
├── README.md
├── LICENSE                # MIT
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/ayzekhdawy/OpenClaudeClaw.git
cd OpenClaudeClaw
python3 install.py
```

## Demo

```bash
python3 demos/demo1_cargo_research.py  # Cargo research
python3 demos/demo2_plan_lsp.py        # Plan mode + LSP
python3 demos/demo3_repl.py            # REPL execution
```

## Testing

```bash
python3 tests/test_all.py
```

## Statistics

- **Total files:** 68
- **Python modules:** 45 (src/) + 16 (tools/)
- **Tool count:** 42
- **Documentation:** 3 MD files
- **Demo:** 3 files
- **Test:** 1 suite

## License

MIT — Ayzekdiolar (2026)

---

**Note:** No personal information included. Ready for general use.
