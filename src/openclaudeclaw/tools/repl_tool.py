"""
REPLTool — Interactive Python REPL
──────────────────────────────────────────────────
Claude Code REPLTool referansı.
Interactive Python shell çalıştırır.
"""

import subprocess
import sys
import time
import json
import tempfile
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


_REPL_STATE_FILE = Path("/home/ayzek/.openclaw/workspace/.harness/repl_state.json")


class REPLTool(BaseTool):
    """
    Interactive Python REPL - Claude Code pattern.

    Commands:
    - start: Start REPL session
    - eval: Execute Python code
    - stop: End REPL session
    - history: Show command history
    - reset: Reset REPL state

    Patterns: repl, python, shell, interactive, konsol
    """
    name = "REPL"
    category = ToolCategory.EXECUTE
    patterns = ["repl", "python", "shell", "interactive", "konsol", "python shell"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        command = input_data.get("command", "start")
        code = input_data.get("code", "")
        timeout = input_data.get("timeout", 10)

        if command == "start":
            return self._start_repl(start)
        elif command == "eval":
            return self._eval_code(code, timeout, start)
        elif command == "stop":
            return self._stop_repl(start)
        elif command == "history":
            return self._show_history(start)
        elif command == "reset":
            return self._reset_repl(start)
        else:
            return ToolResult(
                self.name, False, "",
                f"Unknown command: {command}. Use: start, eval, stop, history, reset",
                int((time.time()-start)*1000)
            )

    def _read_state(self) -> dict:
        """Read REPL state file."""
        if _REPL_STATE_FILE.exists():
            try:
                return json.loads(_REPL_STATE_FILE.read_text())
            except:
                pass
        return {}

    def _write_state(self, state: dict) -> None:
        """Write REPL state file."""
        _REPL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _REPL_STATE_FILE.write_text(json.dumps(state))

    def _start_repl(self, start: float) -> ToolResult:
        """Start a new REPL session."""
        state = {
            "active": True,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "executions": 0,
        }
        self._write_state(state)

        return ToolResult(
            self.name, True,
            "[REPL] Python REPL started. Use 'eval' to execute code, 'stop' to end.",
            int((time.time()-start)*1000),
            metadata={"session": "started"}
        )

    def _eval_code(self, code: str, timeout: int, start: float) -> ToolResult:
        """Execute Python code in REPL context."""
        if not code:
            return ToolResult(self.name, False, "", "code is required", int((time.time()-start)*1000))

        # Read current state
        state = self._read_state()
        executions_before = state.get("executions", 0)

        # Save code to temp file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Run with python
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=min(timeout, 30),
                cwd="/home/ayzek/.openclaw/workspace"
            )

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[ERROR]\n{result.stderr}"

            if result.returncode != 0 and not output:
                output = f"Exit code: {result.returncode}"

            # Update state
            state["executions"] = executions_before + 1
            state["last_output"] = output[:200]
            self._write_state(state)

            return ToolResult(
                self.name,
                result.returncode == 0,
                output[:5000],
                int((time.time()-start)*1000),
                metadata={"exit_code": result.returncode, "executions": state["executions"]}
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                self.name, False, "",
                f"Timeout after {timeout}s",
                int((time.time()-start)*1000)
            )
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))
        finally:
            if temp_file:
                Path(temp_file).unlink(missing_ok=True)

    def _stop_repl(self, start: float) -> ToolResult:
        """Stop REPL session."""
        state = self._read_state()
        executions = state.get("executions", 0)
        if _REPL_STATE_FILE.exists():
            _REPL_STATE_FILE.unlink()

        return ToolResult(
            self.name, True,
            f"[REPL] Stopped. {executions} executions.",
            int((time.time()-start)*1000)
        )

    def _show_history(self, start: float) -> ToolResult:
        """Show REPL history."""
        state = self._read_state()
        if not state:
            return ToolResult(self.name, True, "[REPL] No active session", int((time.time()-start)*1000))

        output = f"[REPL Session]\n"
        output += f"Started: {state.get('started_at', 'unknown')}\n"
        output += f"Executions: {state.get('executions', 0)}\n"
        if state.get("last_output"):
            output += f"Last output: {state['last_output'][:100]}..."

        return ToolResult(self.name, True, output, int((time.time()-start)*1000))

    def _reset_repl(self, start: float) -> ToolResult:
        """Reset REPL state."""
        if _REPL_STATE_FILE.exists():
            _REPL_STATE_FILE.unlink()
        return self._start_repl(start)
