"""
TaskOutputTool — Claude Code inspired task output reader
────────────────────────────────────────────────────────
Cleans-room implementation of Claude Code's TaskOutputTool.
Reads output from previously executed tasks.
"""

import json
import time
import os
from typing import Optional

from .models import ToolResult, ToolCategory, BaseTool


class TaskOutputTool(BaseTool):
    """
    Task output reader - retrieves output from tasks.
    
    Claude Code pattern:
    - Input: task_id, block (wait for completion), timeout
    - Output: task_id, task_type, status, output, error, etc.
    """
    
    name = "TaskOutput"
    category = ToolCategory.READ
    patterns = [
        "task output", "görev çıktısı", "görev sonucu", "task result",
        "task status", "görev durumu", "output", "sonuç"
    ]
    
    def execute(self, input_data: dict, context: dict = None) -> ToolResult:
        """
        Execute task output retrieval.
        
        Input:
        - task_id: The ID of the task to get output from
        - block: Whether to wait for completion (default: true)
        - timeout: Max wait time in ms (default: 30000)
        """
        task_id = input_data.get("task_id", "")
        block = input_data.get("block", True)
        timeout = input_data.get("timeout", 30000)
        
        if not task_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="task_id is required"
            )
        
        # Try to get from task_manager first
        task_data = None
        
        try:
            from .task_manager import get_task_manager
            
            tm = get_task_manager()
            task = tm.get(task_id)
            
            if task:
                task_data = {
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "description": task.description or "",
                    "output": task.result or "",
                    "error": task.error,
                    "exitCode": task.exit_code
                }
                
                # If blocking and not done, wait
                if block and task.status == "running":
                    start = time.time()
                    while time.time() - start < (timeout / 1000):
                        time.sleep(0.5)
                        task = tm.get(task_id)
                        if task and task.status != "running":
                            task_data["status"] = task.status
                            task_data["output"] = task.result or ""
                            task_data["error"] = task.error
                            break
                    else:
                        task_data["status"] = "timeout"
                
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=json.dumps(task_data, indent=2)
                )
        except ImportError:
            pass
        
        # Fallback: try disk output
        disk_output_path = f"/tmp/esra_tasks/{task_id}.json"
        if os.path.exists(disk_output_path):
            try:
                with open(disk_output_path, 'r') as f:
                    data = json.load(f)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=json.dumps(data, indent=2)
                )
            except Exception as e:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Failed to read disk output: {str(e)}"
                )
        
        return ToolResult(
            tool_name=self.name,
            success=False,
            output="",
            error=f"Task not found: {task_id}"
        )
