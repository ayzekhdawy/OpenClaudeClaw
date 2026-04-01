"""NotebookEditTool, ListMcpResourcesTool, ReadMcpResourceTool, SyntheticOutputTool"""

import time
import json
from pathlib import Path

from ..models import BaseTool, ToolResult, ToolCategory


class NotebookEditTool(BaseTool):
    name = "NotebookEdit"
    category = ToolCategory.WRITE
    patterns = ["notebook", "jupyter", "ipynb", "notebook edit"]
    readonly = False

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        path = input_data.get("path", "")
        cell_index = input_data.get("cell_index", 0)
        new_content = input_data.get("content", "")
        cell_type = input_data.get("type", "code")

        if not path:
            return ToolResult(self.name, False, "", "path is required", int((time.time()-start)*1000))

        if not path.endswith(".ipynb"):
            return ToolResult(self.name, False, "", "path must end with .ipynb", int((time.time()-start)*1000))

        try:
            nb_path = Path(path)
            if nb_path.exists():
                with open(nb_path, "r") as f:
                    nb = json.load(f)
            else:
                nb = {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}

            cell = {
                "cell_type": cell_type,
                "metadata": {},
                "source": [new_content]
            }
            if cell_type == "code":
                cell["outputs"] = []
                cell["execution_count"] = None

            if cell_index < len(nb["cells"]):
                nb["cells"][cell_index] = cell
            else:
                nb["cells"].append(cell)

            nb_path.parent.mkdir(parents=True, exist_ok=True)
            with open(nb_path, "w") as f:
                json.dump(nb, f, indent=2)

            return ToolResult(self.name, True, f"Notebook cell {cell_index} edited: {path}", int((time.time()-start)*1000))

        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


class ListMcpResourcesTool(BaseTool):
    name = "ListMcpResources"
    category = ToolCategory.READ
    patterns = ["list resources", "mcp resources", "list mcp"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        server = input_data.get("server", "")

        mcp_config = Path("/home/ayzek/.openclaw/workspace/.mcp/config.json")
        if not mcp_config.exists():
            return ToolResult(self.name, True, "No MCP config found", int((time.time()-start)*1000))

        try:
            config = json.loads(mcp_config.read_text())
            servers = config.get("mcpServers", {})

            if server:
                if server in servers:
                    srv = servers[server]
                    return ToolResult(
                        self.name, True,
                        f"MCP Server: {server}\nCommand: {srv.get('command', '')}\nArgs: {srv.get('args', [])}",
                        int((time.time()-start)*1000)
                    )
                return ToolResult(self.name, False, "", f"Server not found: {server}", int((time.time()-start)*1000))

            output = f"MCP Servers ({len(servers)}):\n"
            for name, cfg in servers.items():
                output += f"  • {name}: {cfg.get('command', '')}\n"
            return ToolResult(self.name, True, output, int((time.time()-start)*1000))

        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


class ReadMcpResourceTool(BaseTool):
    name = "ReadMcpResource"
    category = ToolCategory.READ
    patterns = ["read mcp resource", "mcp resource", "resource oku"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        server = input_data.get("server", "")
        uri = input_data.get("uri", "")

        if not server or not uri:
            return ToolResult(self.name, False, "", "server and uri required", int((time.time()-start)*1000))

        return ToolResult(
            self.name, True,
            f"[MCP Resource]\nServer: {server}\nURI: {uri}\n[MCP server not connected]",
            int((time.time()-start)*1000)
        )


class SyntheticOutputTool(BaseTool):
    name = "SyntheticOutput"
    category = ToolCategory.READ
    patterns = ["synthetic", "output", "üret", "generate output"]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        template = input_data.get("template", "")
        data = input_data.get("data", {})

        if not template:
            return ToolResult(self.name, False, "", "template required", int((time.time()-start)*1000))

        try:
            output = template
            for key, value in data.items():
                output = output.replace(f"{{{key}}}", str(value))

            return ToolResult(self.name, True, output, int((time.time()-start)*1000))
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))
