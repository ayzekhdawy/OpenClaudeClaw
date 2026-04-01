# Demo 2: Plan Mode + LSP Usage

**Scenario:** Start a new Python project, create a plan, analyze code.

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

runtime = HarnessRuntime()
pool = get_tool_pool()

print("=== Demo 2: Plan Mode + LSP ===\n")

# 1. Enter plan mode
plan = pool.execute("EnterPlanMode", {
    "mode": "plan",
    "description": "Create Python project skeleton"
})
print(f"Plan mode: {plan.output}")

# 2. List existing Python files
glob_result = pool.execute("Glob", {"pattern": "*.py"})
print(f"\nPython files: {len(glob_result.output.splitlines())} files")

# 3. LSP symbol analysis
lsp_result = pool.execute("LSP", {
    "operation": "documentSymbol",
    "file_path": "src/openclaudeclaw/tool_pool.py"
})
symbols = [line.strip() for line in lsp_result.output.split('\n') if line.startswith('[')]
print(f"\nTool pool symbols: {len(symbols)} symbols")
for sym in symbols[:5]:
    print(f"  • {sym}")

# 4. Create tasks
tasks = [
    ("Create project skeleton", "high"),
    ("Write tools", "high"),
    ("Write tests", "medium"),
    ("Documentation", "low"),
]

for desc, priority in tasks:
    task = pool.execute("TaskCreate", {
        "description": desc,
        "priority": priority
    })
    print(f"Task created: {desc} ({priority})")

# 5. Show plan status
status = pool.execute("PlanStatus", {})
print(f"\n{status.output}")

# 6. Update todo list
pool.execute("TodoWrite", {
    "todos": [
        {"content": "Project skeleton", "status": "completed"},
        {"content": "Write tools", "status": "in_progress"},
        {"content": "Write tests", "status": "pending"},
        {"content": "Documentation", "status": "pending"},
    ]
})

# 7. Add thought note
pool.execute("Think", {
    "thought": "LSP analysis successful. 32 symbols found. Tool pool structure compatible with Claude Code."
})

# 8. Exit plan mode (discard)
exit_plan = pool.execute("ExitPlanMode", {"action": "discard"})
print(f"\nPlan mode: {exit_plan.output}")

print("\n✓ Demo 2 completed!")
```

## Running

```bash
cd /home/ayzek/.openclaw/workspace/repos/OpenClaudeClaw
python3 demos/demo2_plan_lsp.py
```

## Expected Output

```
=== Demo 2: Plan Mode + LSP ===

Plan mode: [PLAN MODE] Plan mode active...

Python files: 45 files

Tool pool symbols: 32 symbols
  • [class] ToolPool @ line 380
  • [def] __init__ @ line 387
  ...

Task created: Create project skeleton (high)
Task created: Write tools (high)
...

[PLAN] 4 tasks, 1 plan active...

Plan mode: [PLAN MODE] Plan mode closed.

✓ Demo 2 completed!
```

---

**Duration:** ~5 seconds  
**Tools used:** EnterPlanMode(1), Glob(1), LSP(1), TaskCreate(4), PlanStatus(1), TodoWrite(1), Think(1), ExitPlanMode(1)
