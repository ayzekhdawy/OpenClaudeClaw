"""
AskUserQuestionTool — Kullanıcıya soru sor
──────────────────────────────────────────
Claude Code AskUserQuestionTool referansı.
Agent kullanıcıya soru sorar, cevap bekler.
"""

import time
import json
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


_QUESTIONS_FILE = Path("/home/ayzek/.openclaw/workspace/.harness/questions.jsonl")


class AskUserQuestionTool(BaseTool):
    """
    Ask user a question - Claude Code pattern.
    
    Input:
    - question: Question text
    - options: Optional multiple choice list
    - required: Whether answer is required (default: True)
    - timeout_seconds: Max wait time (default: 300)
    
    Patterns: soru sor, ask, question, kullanıcıya sor
    """
    name = "AskUserQuestion"
    category = ToolCategory.NATURAL
    patterns = ["ask", "soru", "question", "kullanıcıya sor", "seç"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        question = input_data.get("question", "")
        options = input_data.get("options", [])  # ["A", "B", "C"]
        required = input_data.get("required", True)
        timeout = input_data.get("timeout_seconds", 300)
        
        if not question:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="question is required",
                duration_ms=int((time.time() - start) * 1000),
            )
        
        # Save question to file
        question_id = f"q_{int(time.time()*1000)}"
        q_entry = {
            "id": question_id,
            "question": question,
            "options": options,
            "required": required,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "answer": None,
        }
        
        _QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_QUESTIONS_FILE, "a") as f:
            f.write(json.dumps(q_entry, ensure_ascii=False) + "\n")
        
        # Build question text
        if options:
            opt_text = "\n".join(f"  {i+1}. {o}" for i, o in enumerate(options))
            full_question = f"{question}\n{opt_text}\n\nCevabınızı yazın (1-{len(options)}):"
        else:
            full_question = f"{question}\n\nCevabınızı yazın:"
        
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"[QUESTION_QUEUED] {question_id}\n\n{full_question}",
            duration_ms=int((time.time() - start) * 1000),
            metadata={
                "question_id": question_id,
                "options_count": len(options),
                "required": required,
            },
        )
    
    def _get_answer(self, question_id: str) -> Optional[dict]:
        """Check if question was answered."""
        if not _QUESTIONS_FILE.exists():
            return None
        
        with open(_QUESTIONS_FILE) as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("id") == question_id and entry.get("status") == "answered":
                    return entry
        return None


class ToolSearchTool(BaseTool):
    """
    Search available tools - Claude Code pattern.
    
    Input:
    - query: Search query
    - category: Optional category filter
    
    Patterns: tool search, araç ara, search tools
    """
    name = "ToolSearch"
    category = ToolCategory.SEARCH
    patterns = ["tool search", "search tools", "araç ara", "tool bul"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        query = input_data.get("query", "")
        category = input_data.get("category", "")
        
        # Get tool pool
        from ..tool_pool import get_tool_pool
        pool = get_tool_pool()
        
        if query:
            results = pool.search(query)
            output = f"'{query}' için sonuçlar:\n\n"
            for spec in results:
                output += f"[{spec.category.value}] {spec.name}\n  {spec.description[:100]}...\n\n"
        else:
            # List all
            all_tools = pool.list_tools()
            output = f"{len(all_tools)} tool:\n\n"
            by_category = {}
            for t in all_tools:
                cat = t.category.value
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(t.name)
            
            for cat, names in sorted(by_category.items()):
                output += f"\n[{cat.upper()}] ({len(names)})\n"
                for n in sorted(names):
                    output += f"  • {n}\n"
        
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=output,
            duration_ms=int((time.time() - start) * 1000),
        )


class SleepTool(BaseTool):
    """
    Sleep/wait for specified duration.
    
    Input:
    - seconds: Seconds to sleep (max 300)
    
    Patterns: sleep, bekle, wait, duraklat
    """
    name = "Sleep"
    category = ToolCategory.EXECUTE
    patterns = ["sleep", "bekle", "wait", "duraklat"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        import time as time_module
        start = time.time()
        
        seconds = min(input_data.get("seconds", 1), 300)
        
        time_module.sleep(seconds)
        
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Slept for {seconds} seconds",
            duration_ms=int((time.time() - start) * 1000),
        )


class ConfigTool(BaseTool):
    """
    Read/write OpenClaw configuration.
    
    Input:
    - action: "get" or "set"
    - key: Config key (e.g., "model", "temperature")
    - value: New value (for set)
    
    Patterns: config, ayar, configuration, seting
    """
    name = "Config"
    category = ToolCategory.READ
    patterns = ["config", "ayar", "configuration", "setting", "setting get", "setting set"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        action = input_data.get("action", "get")
        key = input_data.get("key", "")
        value = input_data.get("value")
        
        config_file = Path("/home/ayzek/.openclaw/workspace/.harness/config.json")
        
        if not config_file.exists():
            config = {}
        else:
            config = json.loads(config_file.read_text())
        
        if action == "get":
            if key:
                val = config.get(key, "not set")
                return ToolResult(
                    self.name, True,
                    f"{key} = {val}",
                    duration_ms=int((time.time()-start)*1000),
                )
            else:
                output = "Current config:\n"
                for k, v in sorted(config.items()):
                    output += f"  {k} = {v}\n"
                return ToolResult(self.name, True, output, duration_ms=int((time.time()-start)*1000))
        
        elif action == "set":
            if not key:
                return ToolResult(self.name, False, "", "key is required for set", int((time.time()-start)*1000))
            
            config[key] = value
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(json.dumps(config, indent=2))
            
            return ToolResult(
                self.name, True,
                f"Set {key} = {value}",
                duration_ms=int((time.time()-start)*1000),
            )
        
        else:
            return ToolResult(
                self.name, False, "",
                f"Unknown action: {action}. Use get or set.",
                int((time.time()-start)*1000)
            )


class EnterPlanModeTool(BaseTool):
    """
    Enter plan mode - Claude Code pattern.
    Agent plan moduna girer, eylem yapmaz.
    
    Patterns: plan, plan mod, düşün, düşünme modu
    """
    name = "EnterPlanMode"
    category = ToolCategory.NATURAL
    patterns = ["plan", "plan mod", "düşün", "düşünme modu", "think mode"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        task = input_data.get("task", "")
        context_text = input_data.get("context", "")
        
        if task:
            output = f"[PLAN MODE] Görev: {task}\n\n"
            if context_text:
                output += f"Kontekst: {context_text}\n\n"
            output += "Agent şimdi adım adım plan oluşturacak..."
        else:
            output = "[PLAN MODE] Plan modu aktif. Görev belirtilmedi."
        
        # Save plan mode state
        state_file = Path("/home/ayzek/.openclaw/workspace/.harness/plan_mode.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({
            "active": True,
            "task": task,
            "context": context_text,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }))
        
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=output,
            duration_ms=int((time.time() - start) * 1000),
        )


class ExitPlanModeTool(BaseTool):
    """
    Exit plan mode - Claude Code pattern.
    
    Patterns: execute, uygula, planı uygula, commit
    """
    name = "ExitPlanMode"
    category = ToolCategory.EXECUTE
    patterns = ["execute", "uygula", "planı uygula", "commit", "plan bitir"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        # Clear plan mode state
        state_file = Path("/home/ayzek/.openclaw/workspace/.harness/plan_mode.json")
        
        if state_file.exists():
            state_file.unlink()
        
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="[PLAN MODE] Plan modu sonlandı. Agent eylem moduna geçti.",
            duration_ms=int((time.time() - start) * 1000),
        )
