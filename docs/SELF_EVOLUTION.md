# Self-Evolution System

OpenClaudeClaw learns from every interaction, error, and correction.

## Core Principle

> **"Continuous self-improvement is the highest priority."**

This isn't just a feature — it's fundamental to the system's identity.

## Learning Triggers

Capture learnings when:

1. **Command or operation fails unexpectedly**
   - Tool execution error
   - Permission denied
   - Timeout or resource exhaustion

2. **User corrects the agent**
   - "No, that's wrong..."
   - "Actually, I meant..."
   - "That's not what I asked for"

3. **User requests non-existent capability**
   - Feature gap identified
   - Document for future implementation

4. **External API or tool fails**
   - Rate limiting (429)
   - Authentication failure
   - Service unavailable

5. **Knowledge is outdated or incorrect**
   - Realize information is stale
   - Discover better approach

6. **Better approach discovered**
   - Recurring task optimization
   - Pattern recognition

## Error Classification

### Slip
**Definition:** Right action, wrong execution (typo, misclick)

**Example:**
```
Intended: `git commit -m "fix auth"`
Actual:   `git commit -m "ifix auth"`  # Typo in message
```

**Response:** Fix typo, no systemic change needed.

### Mistake
**Definition:** Wrong action chosen (incorrect decision)

**Example:**
```
Task: "Research cargo prices"
Action: Called WebSearch with wrong query
Result: Irrelevant results
```

**Response:** 
- Log error
- Add rule: "For cargo research, use specific provider names"
- Update routing logic

### Lapse
**Definition:** Forgot to act (memory failure)

**Example:**
```
User: "Remember to check inventory every Monday"
Agent: Acknowledged
Next Monday: No check performed
```

**Response:**
- Log lapse
- Verify cron job exists
- Add reminder system check

## Error Logging Format

```markdown
## ERROR — [YYYY-MM-DD HH:MM]

**Type:** [Slip | Mistake | Lapse]

**Description:** What happened?

**Expected:** What should have happened?

**Root Cause:** Why did it happen?

**Prevention:** How will I prevent recurrence?

**Context:**
- Task: [task description]
- Tools used: [tool names]
- User: [user_id if relevant]
```

### Example Error Log

```markdown
## ERROR — 2026-04-01 21:30

**Type:** Mistake

**Description:** Calculated tax as 20% instead of 18% for Turkey VAT.

**Expected:** Tax = revenue * 0.18

**Root Cause:** Used default tax rate without checking country-specific rules.

**Prevention:** 
- Add rule: "Always check USER.md for country context"
- Pre-execution checklist: Verify tax rates from official sources
- Add Turkey VAT (18%) to constants

**Context:**
- Task: "Calculate Q1 tax liability"
- Tools used: Task, Think, Brief
- User: 6317788518
```

## Learning Promotion Pipeline

```
┌─────────────┐
│  Error/     │
│  Correction │
│  captured   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Log to     │
│  ERRORS.md  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Pattern    │
│  detection  │
│  (count ≥3?)│
└──────┬──────┘
       │
    ┌──┴──┐
    │ No  │ Yes
    └──┬──┘
       │        ▼
       │   ┌─────────────┐
       │   │  PROMOTE to │
       │   │  SOUL.md    │
       │   └──────┬──────┘
       │          │
       │          ▼
       │   ┌─────────────┐
       │   │  Update     │
       │   │  behavior   │
       │   └─────────────┘
       │
       ▼
┌─────────────┐
│  Monitor    │
│  for repeat │
└─────────────┘
```

## Pre-Execution Checklist

Before any significant output, verify:

```
[ ] 1. ALL SOURCES READ
    □ docx files checked (least tried format)
    □ xlsx files checked (least tried format)
    □ PDF files checked
    □ User's own notes checked

[ ] 2. DATA VERIFIED
    □ Numbers cross-checked from 2+ sources
    □ Mathematical consistency: Revenue - Cost = Profit?
    □ Units consistent (TL, %, count)
    □ Dates aligned

[ ] 3. "I KNOW" CHECK
    □ Unknowns marked: "Unknown — [source needed]"
    □ No guessing — only verified information

[ ] 4. SOURCE LIST
    □ Each data point traced to source file

[ ] 5. LOGIC CHECK
    □ Do results make sense? (e.g., 10 TL revenue, 100 TL cost?)
    □ Any inconsistencies? Report to user if found
```

## Self-Correction Script

Automated error capture:

```python
#!/usr/bin/env python3
"""
esra_autopilot.py — Automatic error logging and system check
"""

def log_error(error_type, description, expected, root_cause, prevention):
    """Log error to .learnings/ERRORS.md"""
    
    entry = f"""
## ERROR — {datetime.now().isoformat()}

**Type:** {error_type}
**Description:** {description}
**Expected:** {expected}
**Root Cause:** {root_cause}
**Prevention:** {prevention}

"""
    
    errors_file = Path(".learnings/ERRORS.md")
    errors_file.append(entry)
    
    # Check for patterns
    check_patterns(errors_file)


def check_patterns(errors_file):
    """Detect recurring patterns (3+ occurrences)"""
    
    errors = parse_errors(errors_file)
    
    for pattern, count in count_patterns(errors):
        if count >= 3:
            promote_to_soul(pattern)
            print(f"Pattern promoted: {pattern}")
```

## Weekly Review Process

Every 7 days:

```python
def weekly_review():
    """Generate weekly learning summary"""
    
    learnings = read_learnings(last_7_days=True)
    errors = read_errors(last_7_days=True)
    
    report = f"""
# Weekly Review — {date_range}

## Summary

| Metric | Count |
|--------|-------|
| Total Learnings | {len(learnings)} |
| Total Errors | {len(errors)} |
| Recurring Patterns | {count_promotions()} |

## Top Learnings
{summarize_top_learnings(learnings)}

## Recurring Errors
{list_recurring_errors(errors)}

## System Improvements
{list_promotions_to_soul()}
"""
    
    save_report(report)
    notify_user(report)
```

## Behavior Update Examples

### Example 1: Tax Rate Correction

**Error:** Used 20% tax instead of 18% (Turkey VAT)

**After 3 occurrences:**
```markdown
## PROMOTED RULE — 2026-04-01

**Rule:** Always use 18% VAT for Turkey financial calculations.

**Source:** Turkey tax code
**Trigger:** Financial calculation tasks
**Action:** Apply 0.18 multiplier, not 0.20
```

### Example 2: File Format Priority

**Error:** Skipped docx/xlsx files, only read PDF

**After 3 occurrences:**
```markdown
## PROMOTED RULE — 2026-04-01

**Rule:** Read all file formats in priority order:
1. docx (least tried, often contains latest data)
2. xlsx (financial data)
3. PDF (reports)
4. User notes (manual entries)

**Trigger:** Research tasks
**Action:** Check all formats before concluding
```

### Example 3: Uncertainty Expression

**Error:** Said "approximately 50%" without source

**After 3 occurrences:**
```markdown
## PROMOTED RULE — 2026-04-01

**Rule:** Never express uncertainty with estimates.

**Wrong:** "Approximately 50%", "Probably around..."
**Right:** "Data not found — [source needed]", "Confidence: X% because Y"

**Trigger:** Any response with uncertain information
**Action:** Mark as unknown, request source
```

## Metrics & Monitoring

Track over time:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Error rate | < 5% per session | Errors / total actions |
| Repeat error rate | 0% | Same error twice = system failure |
| Learning velocity | > 2/week | New learnings per week |
| Promotion rate | 1-2/month | Rules added to SOUL.md |

## Integration Points

### With Context Builder
- Load recent learnings into context
- Promoted rules always active

### With Policy Engine
- Auto-reject actions that violate learned rules
- Require approval for edge cases

### With Tool Pool
- Tool-specific learnings attached to tool definitions
- Performance metrics per tool

---

**Version:** 1.0.0  
**License:** MIT
