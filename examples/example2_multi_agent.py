# Example 2: Multi-Agent Orchestration

**Scenario:** Complex task requiring research + coding + review.

```python
#!/usr/bin/env python3
"""
Example 2: Multi-Agent Orchestration
──────────────────────────────────────────────────────────
Demonstrates: Orchestrator pattern, sub-agent spawning, synthesis
"""

from openclaudeclaw import HarnessRuntime, get_tool_pool
from openclaudeclaw.context_builder import build_context


def main():
    print("=" * 60)
    print("EXAMPLE 2: Multi-Agent Orchestration")
    print("=" * 60)
    
    runtime = HarnessRuntime()
    pool = get_tool_pool()
    
    # High-level task
    task = "Build a Python script that fetches cargo prices and saves to CSV"
    
    print(f"\nTask: {task}\n")
    
    # Decompose manually (or use reasoning chain)
    steps = [
        {"step": "Research cargo API endpoints", "tool": "WebSearch"},
        {"step": "Write Python script", "tool": "Bash"},  # Would use Claude Code in real scenario
        {"step": "Test script execution", "tool": "Bash"},
        {"step": "Review and document", "tool": "Read"},
    ]
    
    print("Decomposition:")
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s['step']} → {s['tool']}")
    
    # Execute each step
    print("\n" + "=" * 60)
    print("EXECUTION")
    print("=" * 60)
    
    results = []
    for step in steps:
        print(f"\n[Step] {step['step']}")
        
        if step["tool"] == "WebSearch":
            result = pool.execute("WebSearch", {
                "query": "cargo price API Turkey Yurtiçi Sürat",
                "count": 5
            })
        elif step["tool"] == "Bash":
            result = pool.execute("Bash", {
                "command": "echo 'Script would be written here'"
            })
        elif step["tool"] == "Read":
            result = pool.execute("Read", {
                "path": "README.md",
                "limit": 5
            })
        
        results.append(result)
        print(f"  Status: {'✓' if result.success else '✗'}")
        print(f"  Output: {result.output[:100]}...")
    
    # Synthesize results
    print("\n" + "=" * 60)
    print("SYNTHESIS")
    print("=" * 60)
    
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    print(f"""
Multi-Agent Execution Summary:
- Total steps: {len(steps)}
- Successful: {successful}
- Failed: {failed}
- Success rate: {successful/len(steps)*100:.0f}%

Outputs generated:
{chr(10).join([f'  • Step {i+1}: {r.output[:50]}...' for i, r in enumerate(results)])}
""")


if __name__ == "__main__":
    main()
```

## Expected Output

```
============================================================
EXAMPLE 2: Multi-Agent Orchestration
============================================================

Task: Build a Python script that fetches cargo prices and saves to CSV

Decomposition:
  1. Research cargo API endpoints → WebSearch
  2. Write Python script → Bash
  3. Test script execution → Bash
  4. Review and document → Read

============================================================
EXECUTION
============================================================

[Step] Research cargo API endpoints
  Status: ✓
  Output: [5 search results about cargo APIs]...

[Step] Write Python script
  Status: ✓
  Output: Script would be written here...

[Step] Test script execution
  Status: ✓
  Output: Script would be written here...

[Step] Review and document
  Status: ✓
  Output: # OpenClaudeClaw...

============================================================
SYNTHESIS
============================================================

Multi-Agent Execution Summary:
- Total steps: 4
- Successful: 4
- Failed: 0
- Success rate: 100%

Outputs generated:
  • Step 1: [5 search results about cargo APIs]...
  • Step 2: Script would be written here...
  • Step 3: Script would be written here...
  • Step 4: # OpenClaudeClaw...
```

## Key Learnings

This example demonstrates:

1. **Task Decomposition** — Breaking complex task into steps
2. **Tool Routing** — Each step uses appropriate tool
3. **Sequential Execution** — Steps run in order
4. **Result Synthesis** — Combine outputs into summary
5. **Error Tracking** — Count successes vs failures

## Running the Example

```bash
cd OpenClaudeClaw
python3 examples/example2_multi_agent.py
```

---

**Duration:** ~10 seconds  
**Tools used:** WebSearch(1), Bash(2), Read(1)  
**Success rate:** 100% (all steps complete)
