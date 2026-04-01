# Demo 1: Cargo Price Research

**Scenario:** Compare Yurtiçi and Sürat cargo prices for Flech brand.

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool
from openclaudeclaw.context_builder import build_context

# Initialize runtime
runtime = HarnessRuntime()
pool = get_tool_pool()

# 1. Build context (SOUL + MEMORY + USER auto-loaded)
ctx = build_context("Research cargo prices for Flech and compare")
print(f"Context ready: {len(ctx.full_prompt)} chars")

# 2. Web search
search_result = pool.execute("WebSearch", {
    "query": "Yurtiçi cargo prices 2026",
    "count": 5
})
print(f"Yurtiçi results: {search_result.output[:300]}...")

search_result = pool.execute("WebSearch", {
    "query": "Sürat cargo prices 2026",
    "count": 5
})
print(f"Sürat results: {search_result.output[:300]}...")

# 3. Fetch web pages
if search_result.urls:
    fetch_result = pool.execute("WebFetch", {
        "url": search_result.urls[0]
    })
    print(f"Content: {fetch_result.output[:500]}...")

# 4. Add thought note
pool.execute("Think", {
    "thought": "Yurtiçi offers 20% discount on glass products. Sürat is more expensive but faster."
})

# 5. Create task
task = pool.execute("TaskCreate", {
    "description": "Select cargo company and report to user",
    "priority": "high"
})

# 6. Send brief message to user
pool.execute("Brief", {
    "message": """
**Cargo Comparison — Flech**

| Company | Price | Duration | Glass Products |
|---------|-------|----------|----------------|
| Yurtiçi | 85 TL | 2-3 days | 20% discount |
| Sürat | 95 TL | 1-2 days | Standard |

**Recommendation:** Yurtiçi cargo (discount on glass products).

Need detailed analysis?
""",
    "status": "normal"
})

# 7. Complete task
pool.execute("TaskStop", {"task_id": task.task_id})

print("\n✓ Demo completed!")
```

## Running

```bash
cd /home/ayzek/.openclaw/workspace/repos/OpenClaudeClaw
python3 demos/demo1_cargo_research.py
```

## Expected Output

```
Context ready: 2828 chars
Yurtiçi results: [5 results list]...
Sürat results: [5 results list]...
Content: [Page content]...
✓ Demo completed!
```

---

**Duration:** ~15 seconds  
**Tools used:** WebSearch(2), WebFetch(1), Think(1), TaskCreate(1), Brief(1), TaskStop(1)
