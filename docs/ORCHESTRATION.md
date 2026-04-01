# Multi-Agent Orchestration

OpenClaudeClaw supports sophisticated multi-agent patterns for complex tasks.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 Orchestrator Agent                      │
│  (Main agent: reasoning, coordination, synthesis)       │
└───────────────┬─────────────────┬───────────────────────┘
                │                 │
        ┌───────┴───────┐ ┌──────┴───────┐
        │               │ │                │
   ┌────▼────┐    ┌────▼────┐      ┌─────▼─────┐
   │ Coding  │    │Research │      │ Workflow  │
   │  Agent  │    │  Agent  │      │  Executor │
   │(Claude  │    │ (SEARXNG│      │   (n8n)   │
   │  Code)  │    │ + web)  │      │           │
   └─────────┘    └─────────┘      └───────────┘
```

## Agent Types

### 1. Orchestrator (Main Agent)
**Role:** Deep reasoning, coordination, synthesis

**Responsibilities:**
- Decompose complex tasks
- Route sub-tasks to appropriate agents
- Collect and synthesize results
- Handle failures and retries
- Report final outcome to user

**When to use:**
- Multi-step tasks requiring coordination
- Tasks needing deep reasoning (5-step chain)
- When context is getting large

### 2. Coding Agent (Claude Code / MCP-based)
**Role:** All code writing, editing, debugging, git operations

**Capabilities:**
- File read/write/edit
- Shell command execution
- Git operations
- Code review

**Invocation pattern:**
```python
result = orchestrator.spawn(
    runtime="acp",
    agent_id="claude-code",
    task="Fix bug in auth.py: bcrypt hash comparison fails",
    files=["src/auth.py", "tests/test_auth.py"],
    expected_output="Working auth module with passing tests"
)
```

**Best practices:**
- Never invoke with vague instructions like "fix the code"
- Always specify what's wrong and what correct looks like
- Verify file state after completion

### 3. Research Agent (Web Search + Fetch)
**Role:** Information gathering from web sources

**Capabilities:**
- Web search (Brave API)
- Page fetching and extraction
- Multi-source verification
- Source citation

**Workflow:**
```
Query → Search → Fetch multiple sources → Cross-verify → Summarize → Cite
```

**Example:**
```python
research = orchestrator.spawn(
    task="Research cargo prices for glass products in Turkey",
    tools=["WebSearch", "WebFetch"],
    output_format="Comparison table with sources"
)
```

### 4. Workflow Executor (n8n / Deterministic)
**Role:** Repeatable business workflows

**Use cases:**
- Cargo price comparisons
- Scheduled reports
- CRM-style data lookups
- Data transformations

**Communication:** HTTP POST with structured JSON

**Example:**
```python
result = n8n.execute(
    workflow="cargo-compare",
    payload={
        "weight": "5kg",
        "dimensions": "30x20x15cm",
        "destination": "Istanbul",
        "providers": ["yurtici", "surat"]
    }
)
# Returns: Structured JSON with price comparison
```

### 5. Local Inference (Ollama)
**Role:** Fast, cost-free local processing

**Use cases:**
- First-pass drafts
- Text classification/tagging
- Summarizing internal docs
- Low-stakes tasks

**Do NOT use for:**
- Final customer-facing content
- Code review
- Business-critical decisions

## Task Routing Decision Tree

```
Is the task deterministic and repeatable?
  → YES → Workflow Executor (n8n)
  → NO → Continue

Does it require code writing/editing?
  → YES → Coding Agent (Claude Code)
  → NO → Continue

Does it require deep reasoning or structured analysis?
  → YES → Orchestrator (5-step chain) or Research Agent
  → NO → Continue

Is it a draft or classification that doesn't need precision?
  → YES → Local Inference (Ollama)
  → NO → Main model (Claude/Claude Sonnet)
```

## Orchestration Patterns

### Pattern 1: Sequential Pipeline

```
Task → Decompose → [Step 1 → Step 2 → Step 3] → Synthesize → Result
```

**Example:** Research + Write Report
```python
# Step 1: Research
research = spawn_research("Market trends 2026")

# Step 2: Analyze
analysis = spawn_analysis(research.results)

# Step 3: Write
report = spawn_writer(analysis.insights)

# Synthesize
deliver(report)
```

### Pattern 2: Parallel Research

```
        ┌─→ Agent A (Source A) ─┐
Task ──→├─→ Agent B (Source B) ─┼→ Synthesize → Result
        └─→ Agent C (Source C) ─┘
```

**Example:** Multi-source verification
```python
sources = ["source_a", "source_b", "source_c"]
results = parallel_spawn([
    {"task": f"Extract data from {s}", "agent": "research"} 
    for s in sources
])
synthesis = synthesize(results)
```

### Pattern 3: Review Loop

```
Draft → Review → Feedback → Revise → Review → Final
```

**Example:** Code review cycle
```python
# Initial implementation
code = coding_agent.implement(feature_spec)

# Review
review = coding_agent.review(code)

# If issues found
if review.issues:
    revised = coding_agent.revise(code, review.issues)
    # Loop until clean
```

### Pattern 4: Fallback Chain

```
Primary Agent → (if fails) → Secondary Agent → (if fails) → Human Escalation
```

**Example:** Research with fallback
```python
try:
    result = research_agent.search(query)
except NoResultsFound:
    result = web_search.broad_search(query)
    if not result:
        escalate_to_user("Couldn't find information on this topic")
```

## Failure Handling

### Agent Failure Protocol

1. **Log the failure**
   ```python
   log_failure(agent_id, task, error, context)
   ```

2. **Describe what failed and why**
   - What was the task?
   - What went wrong?
   - Root cause analysis

3. **Retry strategy**
   - Retry with corrected instruction?
   - Try different agent?
   - Escalate to user?

4. **Never silently skip**
   - Always report failures
   - Provide context for user decision

### Example: Handling Coding Agent Failure

```python
try:
    result = coding_agent.run(task)
except AgentError as e:
    # Log
    error_log.add({
        "agent": "coding",
        "task": task.description,
        "error": str(e),
        "timestamp": now()
    })
    
    # Analyze
    if "permission" in str(e):
        # Retry with different permissions
        result = coding_agent.run(task, permissions="elevated")
    elif "timeout" in str(e):
        # Escalate — task too complex
        escalate_to_user(f"Coding task timed out: {task.description}")
    else:
        # Generic retry
        result = coding_agent.run(task, retry=True)
```

## Memory Sync Between Agents

After multi-agent sessions, update shared memory:

```markdown
## [DATE] — [Task Summary]

**Agents invoked:**
- Coding Agent: Implemented auth module
- Research Agent: Gathered security best practices

**Failures/Retries:**
- Coding Agent: Initial test failed (bcrypt version mismatch)
- Retry: Updated dependency, tests passed

**Outputs:**
- `src/auth.py` — Working auth module
- `tests/test_auth.py` — Passing tests

**Relevant paths:**
- `/workspace/src/auth.py`
- `/workspace/tests/test_auth.py`
```

## Tool-Heavy Task Optimization

For tool-intensive operations (LSP, complex searches, large file analysis):

**Model routing:**
```python
TOOL_HEAVY_TOOLS = ["LSP", "AnalyzeContext", "Skill", "WebSearch", "Grep", "Glob"]

if tool_name in TOOL_HEAVY_TOOLS:
    input_data["model_override"] = "deepseek-v3.1:671b-cloud"
```

**Rationale:**
- DeepSeek-V3 optimized for tool calling
- Better at parsing large contexts
- Cost-effective for bulk operations

## Best Practices

### Do's
✅ Decompose before delegating — Break complex tasks into atomic steps  
✅ One agent per step — Don't run multiple agents for same task simultaneously  
✅ Collect and synthesize — Consolidate results before reporting  
✅ Verify after completion — Check file state, validate outputs  
✅ Log failures — Record what failed and why  

### Don'ts
❌ Vague instructions — "fix the code" without specifics  
❌ Parallel agents for same task — Sequence properly  
❌ Forward raw output — Synthesize first  
❌ Silent failures — Always report  
❌ Skip verification — Always check results  

---

**Version:** 1.0.0  
**License:** MIT
