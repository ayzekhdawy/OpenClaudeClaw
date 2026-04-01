"""
PlanModeTool — Planning Mode System
──────────────────────────────────────────────────────────
Claude Code EnterPlanModeTool referansı.
Plan modu: agent'ın sadece düşünmesini, konuşmasını sağlar.
Yürütme yapmaz — sadece plan oluşturur.
"""

import time
import json
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


_PLAN_STATE = Path("/home/ayzek/.openclaw/workspace/.harness/plan_state.json")


class EnterPlanModeTool(BaseTool):
    """
    Enter planning mode - Claude Code pattern.

    In plan mode:
    - Agent thinks and discusses
    - No tool execution
    - Creates structured plan
    - Waits for user approval

    Patterns: plan modu, düşün, plan yap, düşünme modu
    """
    name = "EnterPlanMode"
    category = ToolCategory.UTILITY
    patterns = ["plan modu", "düşün", "plan yap", "planla", "planning mode"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        mode = input_data.get("mode", "plan")
        description = input_data.get("description", "")
        initial_thought = input_data.get("thought", "")

        # Check if already in plan mode
        if _PLAN_STATE.exists():
            state = json.loads(_PLAN_STATE.read_text())
            if state.get("active"):
                return ToolResult(
                    self.name, True,
                    f"Already in {state.get('mode', 'plan')} mode since {state.get('started_at', '')}",
                    int((time.time()-start)*1000)
                )

        # Enter plan mode
        state = {
            "active": True,
            "mode": mode,
            "description": description,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "thoughts": [],
            "plan": None,
            "approved": False
        }

        if initial_thought:
            state["thoughts"].append({
                "text": initial_thought,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

        _PLAN_STATE.parent.mkdir(parents=True, exist_ok=True)
        _PLAN_STATE.write_text(json.dumps(state))

        output = f"[PLAN MODE] Entered planning mode.\n"
        output += f"Mode: {mode}\n"
        if description:
            output += f"Goal: {description}\n"
        output += "\nI'll think through this step by step. Use 'ExitPlanMode' to execute or 'UpdatePlan' to refine."

        return ToolResult(
            self.name, True, output,
            int((time.time()-start)*1000),
            metadata={"mode": mode}
        )


class ExitPlanModeTool(BaseTool):
    """
    Exit planning mode - Claude Code pattern.

    Options:
    - execute: Execute the plan
    - discard: Discard and return to normal mode
    - save: Save plan for later

    Patterns: plan bitir, execute plan, planı uygula, çıkış plan modu
    """
    name = "ExitPlanMode"
    category = ToolCategory.UTILITY
    patterns = ["plan bitir", "planı uygula", "execute plan", "planı kaydet", "exit planning"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        action = input_data.get("action", "discard")
        save_path = input_data.get("save_path", "")

        if not _PLAN_STATE.exists():
            return ToolResult(
                self.name, False, "",
                "Not in plan mode",
                int((time.time()-start)*1000)
            )

        state = json.loads(_PLAN_STATE.read_text())

        if action == "discard":
            _PLAN_STATE.unlink()
            return ToolResult(
                self.name, True,
                "[PLAN MODE] Discarded plan, returned to normal mode.",
                int((time.time()-start)*1000)
            )

        elif action == "save":
            plan_content = self._format_plan(state)
            if save_path:
                path = Path(save_path)
            else:
                path = Path(f"/home/ayzek/.openclaw/workspace/plans/plan_{int(time.time())}.md")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(plan_content)
            _PLAN_STATE.unlink()
            return ToolResult(
                self.name, True,
                f"[PLAN MODE] Plan saved to {path}",
                int((time.time()-start)*1000)
            )

        elif action == "execute":
            # Mark as approved
            state["approved"] = True
            state["executed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            _PLAN_STATE.write_text(json.dumps(state))

            plan_content = self._format_plan(state)

            return ToolResult(
                self.name, True,
                f"[PLAN MODE] Plan approved for execution.\n\n{plan_content}\n\n[Ready to execute]",
                int((time.time()-start)*1000),
                metadata={"approved": True}
            )

        else:
            return ToolResult(
                self.name, False, "",
                f"Unknown action: {action}. Use: discard, save, execute",
                int((time.time()-start)*1000)
            )

    def _format_plan(self, state: dict) -> str:
        """Format plan for display."""
        output = f"# Plan: {state.get('description', 'Untitled')}\n\n"
        output += f"Mode: {state.get('mode', 'plan')}\n"
        output += f"Created: {state.get('started_at', '')}\n\n"

        if state.get("thoughts"):
            output += "## Thoughts\n\n"
            for thought in state["thoughts"]:
                output += f"- {thought.get('text', '')} ({thought.get('timestamp', '')})\n"
            output += "\n"

        if state.get("plan"):
            output += "## Plan\n\n"
            for i, step in enumerate(state["plan"], 1):
                output += f"{i}. {step}\n"
            output += "\n"

        return output


class UpdatePlanTool(BaseTool):
    """
    Update current plan - Claude Code pattern.

    Actions:
    - add_step: Add a step to the plan
    - remove_step: Remove a step
    - add_thought: Add a thought
    - set_goal: Update the goal/description

    Patterns: plan güncelle, düşünce ekle, adım ekle
    """
    name = "UpdatePlan"
    category = ToolCategory.UTILITY
    patterns = ["plan güncelle", "düşünce ekle", "adım ekle", "update plan", "planı düzelt"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        if not _PLAN_STATE.exists():
            return ToolResult(
                self.name, False, "",
                "Not in plan mode",
                int((time.time()-start)*1000)
            )

        state = json.loads(_PLAN_STATE.read_text())
        action = input_data.get("action", "")
        value = input_data.get("value", "")

        if action == "add_step":
            plan = state.get("plan", [])
            plan.append(value)
            state["plan"] = plan
            _PLAN_STATE.write_text(json.dumps(state))
            return ToolResult(
                self.name, True,
                f"[PLAN] Step added: {value}",
                int((time.time()-start)*1000)
            )

        elif action == "add_thought":
            thoughts = state.get("thoughts", [])
            thoughts.append({
                "text": value,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            state["thoughts"] = thoughts
            _PLAN_STATE.write_text(json.dumps(state))
            return ToolResult(
                self.name, True,
                f"[PLAN] Thought added: {value[:50]}...",
                int((time.time()-start)*1000)
            )

        elif action == "set_goal":
            state["description"] = value
            _PLAN_STATE.write_text(json.dumps(state))
            return ToolResult(
                self.name, True,
                f"[PLAN] Goal updated: {value}",
                int((time.time()-start)*1000)
            )

        elif action == "remove_step":
            plan = state.get("plan", [])
            try:
                idx = int(value) - 1
                removed = plan.pop(idx)
                state["plan"] = plan
                _PLAN_STATE.write_text(json.dumps(state))
                return ToolResult(
                    self.name, True,
                    f"[PLAN] Removed step: {removed}",
                    int((time.time()-start)*1000)
                )
            except (ValueError, IndexError):
                return ToolResult(
                    self.name, False, "",
                    f"Invalid step index: {value}",
                    int((time.time()-start)*1000)
                )

        else:
            return ToolResult(
                self.name, False, "",
                f"Unknown action: {action}. Use: add_step, add_thought, set_goal, remove_step",
                int((time.time()-start)*1000)
            )


class PlanStatusTool(BaseTool):
    """
    Show current plan status - Claude Code pattern.

    Patterns: plan durumu, plan status, ne planlıyoruz
    """
    name = "PlanStatus"
    category = ToolCategory.UTILITY
    patterns = ["plan durumu", "plan status", "ne planlıyoruz", "show plan"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        if not _PLAN_STATE.exists():
            return ToolResult(
                self.name, True,
                "[PLAN] Not in plan mode.",
                int((time.time()-start)*1000)
            )

        state = json.loads(_PLAN_STATE.read_text())
        output = self._format_plan(state)

        return ToolResult(
            self.name, True, output,
            int((time.time()-start)*1000)
        )
