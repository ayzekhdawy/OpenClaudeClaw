# Example 1: Cargo Price Research (Full Workflow)

**Scenario:** Flech brand needs cargo price comparison for glass products.

## Complete Implementation

```python
#!/usr/bin/env python3
"""
Example 1: Cargo Price Research
──────────────────────────────────────────────────────────
Demonstrates: WebSearch, WebFetch, Think, Task, Brief, Reasoning Chain
"""

from openclaudeclaw import HarnessRuntime
from openclaudeclaw.esra_runtime import create_esra_runtime
from openclaudeclaw.context_builder import build_context


def main():
    print("=" * 60)
    print("EXAMPLE 1: Cargo Price Research")
    print("=" * 60)
    
    # Initialize runtime
    runtime = create_esra_runtime()
    
    # Task description
    task = "Research cargo prices for glass products (Flech brand). Compare Yurtiçi and Sürat kargo."
    
    print(f"\nTask: {task}\n")
    
    # Execute with full reasoning chain
    result = runtime.execute_with_reasoning(task)
    
    # Print reasoning chain
    print("\n" + "=" * 60)
    print("REASONING CHAIN")
    print("=" * 60)
    
    for step in result.reasoning_chain:
        print(f"\n[Step {step.step}: {step.name}] (confidence: {step.confidence:.0%})")
        print(step.output[:500] + "..." if len(step.output) > 500 else step.output)
    
    # Print final result
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(result.output)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Success: {result.success}")
    print(f"Reasoning steps: {len(result.reasoning_chain)}")
    print(f"Errors logged: {result.errors_logged}")
    print(f"Learnings created: {result.learnings_created}")


if __name__ == "__main__":
    main()
```

## Expected Output

```
============================================================
EXAMPLE 1: Cargo Price Research
============================================================

Task: Research cargo prices for glass products (Flech brand). Compare Yurtiçi and Sürat kargo.

============================================================
REASONING CHAIN
============================================================

[Step 1: DEFINE] (confidence: 90%)
GOAL: Compare cargo prices for glass products between Yurtiçi and Sürat
SUCCESS_CRITERIA:
- Price per kg for both providers
- Delivery time comparison
- Glass product handling policies
- Discount offers

[Step 2: DECOMPOSE] (confidence: 85%)
STEP 1: Search Yurtiçi kargo prices → WebSearch
STEP 2: Search Sürat kargo prices → WebSearch
STEP 3: Fetch detailed pricing pages → WebFetch
STEP 4: Create comparison table → Think
STEP 5: Send brief to user → Brief

[Step 3: RESEARCH] (confidence: 80%)
Yurtiçi kargo fiyatları 2026 cam ürünler...
Sürat kargo fiyatları 2026 özel ürünler...

[Step 4: SYNTHESIZE] (confidence: 85%)
ACTION PLAN:
1. Yurtiçi: 85 TL, 2-3 days, 20% glass discount
2. Sürat: 95 TL, 1-2 days, standard rate
Recommendation: Yurtiçi (price advantage)

[Step 5: VALIDATE] (confidence: 95%)
VALIDATION CHECKLIST:
[✓] All sources read
[✓] Data verified from 2+ sources
[✓] Mathematical consistency checked
[✓] Units consistent
[✓] Unknowns marked appropriately
[✓] Logic check passed

PLAN READY FOR EXECUTION: YES

============================================================
FINAL RESULT
============================================================

**Cargo Comparison — Flech**

| Company | Price | Duration | Glass Products |
|---------|-------|----------|----------------|
| Yurtiçi | 85 TL | 2-3 days | 20% discount |
| Sürat | 95 TL | 1-2 days | Standard |

**Recommendation:** Yurtiçi cargo (discount on glass products).

============================================================
SUMMARY
============================================================
Success: True
Reasoning steps: 5
Errors logged: 0
Learnings created: 0
```

## Key Learnings

This example demonstrates:

1. **5-Step Reasoning Chain** — Full Dalio process
2. **Tool Coordination** — WebSearch → WebFetch → Think → Brief
3. **Pre-Execution Checklist** — Validation before action
4. **Confidence Scoring** — Each step has confidence level
5. **Error Logging** — Automatic capture if failures occur

## Running the Example

```bash
cd OpenClaudeClaw
python3 examples/example1_cargo_research.py
```

---

**Duration:** ~15 seconds  
**Tools used:** WebSearch(2), WebFetch(2), Think(3), Brief(1)  
**Reasoning steps:** 5  
**Expected success rate:** 95%+
