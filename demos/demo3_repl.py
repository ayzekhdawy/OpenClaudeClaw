# Demo 3: REPL + Code Execution

**Scenario:** Interactive Python shell for data processing.

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool
import json

runtime = HarnessRuntime()
pool = get_tool_pool()

print("=== Demo 3: REPL + Code Execution ===\n")

# 1. Start REPL
start = pool.execute("REPL", {"command": "start"})
print(f"REPL: {start.output}")

# 2. Run data processing code
code1 = """
import json
data = {
    "brands": ["Urbica", "Flech", "Morecano"],
    "revenue": [73000, 45000, 12000],
    "month": "March 2026"
}
print(json.dumps(data, indent=2, ensure_ascii=False))
"""

result = pool.execute("REPL", {
    "command": "eval",
    "code": code1
})
print(f"\nData processing result:\n{result.output}")

# 3. Run calculations
code2 = """
revenue = [73000, 45000, 12000]
total = sum(revenue)
average = total / len(revenue)
growth = ((revenue[0] - revenue[1]) / revenue[1]) * 100
print(f"Total revenue: {total:,.0f} TL")
print(f"Average: {average:,.0f} TL")
print(f"Urbica-Flech growth: %{growth:.1f}")
"""

result = pool.execute("REPL", {
    "command": "eval",
    "code": code2
})
print(f"\nCalculation:\n{result.output}")

# 4. Error handling
code3 = """
# Intentional error
x = 1 / 0
"""

result = pool.execute("REPL", {
    "command": "eval",
    "code": code3
})
print(f"\nError case:\nSuccess: {result.success}\nError: {result.error or result.output}")

# 5. Show REPL history
history = pool.execute("REPL", {"command": "history"})
print(f"\n{history.output}")

# 6. Stop REPL
stop = pool.execute("REPL", {"command": "stop"})
print(f"\nREPL: {stop.output}")

print("\n✓ Demo 3 completed!")
```

## Running

```bash
cd /home/ayzek/.openclaw/workspace/repos/OpenClaudeClaw
python3 demos/demo3_repl.py
```

## Expected Output

```
=== Demo 3: REPL + Code Execution ===

REPL: [REPL] Python REPL started...

Data processing result:
{
  "brands": ["Urbica", "Flech", "Morecano"],
  "revenue": [73000, 45000, 12000],
  "month": "March 2026"
}

Calculation:
Total revenue: 130,000 TL
Average: 43,333 TL
Urbica-Flech growth: %62.2

Error case:
Success: False
Error: [ERROR] ... ZeroDivisionError ...

[REPL Session]
Started: 2026-04-01 21:00:00
Executions: 3
Last output: ...

REPL: [REPL] Stopped. 3 executions.

✓ Demo 3 completed!
```

---

**Duration:** ~3 seconds  
**Tools used:** REPL(5: start, eval x3, history, stop)
