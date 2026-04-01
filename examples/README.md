# OpenClaudeClaw Examples

Three comprehensive examples demonstrating the full power of the system:

## Example 1: Cargo Price Research (Full Reasoning Chain)

**File:** `example1_cargo_research.py`

**Demonstrates:**
- 5-step reasoning chain (Dalio process)
- Web search + fetch coordination
- Pre-execution checklist
- Confidence scoring per step
- Automatic error logging

**Tools used:** WebSearch, WebFetch, Think, Brief

**Duration:** ~15 seconds

**Run:**
```bash
python3 examples/example1_cargo_research.py
```

---

## Example 2: Multi-Agent Orchestration

**File:** `example2_multi_agent.py`

**Demonstrates:**
- Task decomposition
- Tool routing (each step → appropriate tool)
- Sequential execution
- Result synthesis
- Error tracking

**Tools used:** WebSearch, Bash, Read

**Duration:** ~10 seconds

**Run:**
```bash
python3 examples/example2_multi_agent.py
```

---

## Example 3: Self-Correction & Learning

**File:** `example3_self_correction.py`

**Demonstrates:**
- Error logging (Slip/Mistake/Lapse classification)
- Pattern detection (count ≥ 3 → promote)
- Rule promotion to permanent learning
- Behavior update mechanism

**No external tools** — Pure Python demonstration

**Duration:** ~2 seconds

**Run:**
```bash
python3 examples/example3_self_correction.py
```

---

## What These Examples Show

| Feature | Ex 1 | Ex 2 | Ex 3 |
|---------|------|------|------|
| Reasoning Chain | ✓ | Partial | — |
| Tool Coordination | ✓ | ✓ | — |
| Multi-Step Tasks | ✓ | ✓ | — |
| Error Handling | ✓ | ✓ | ✓ |
| Self-Learning | — | — | ✓ |
| Pre-Execution Check | ✓ | — | — |
| Synthesis | ✓ | ✓ | — |

## Expected Outcomes

### Example 1 Output
- Full reasoning chain printout (5 steps)
- Confidence scores per step
- Final comparison table (cargo prices)
- Success/failure summary

### Example 2 Output
- Step-by-step execution log
- Success rate calculation
- Synthesized summary

### Example 3 Output
- Error log entries (3 tax errors + 1 format skip)
- Promoted rule (tax rate → 18% for Turkey)
- Learning file content

---

**Purpose:** These examples show developers how to build production-ready agents with OpenClaudeClaw.
