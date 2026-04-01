"""
Additional tools — NotebookEdit, MCP Resources, SyntheticOutput
─────────────────────────────────────────────────────────────
Claude Code NotebookEditTool, ListMcpResourcesTool, ReadMcpResourceTool, SyntheticOutputTool referansı.
"""

import time
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


# ─── NotebookEditTool ─────────────────────────────────────────────────────────

class NotebookEditTool(BaseTool):
    """
    Edit Jupyter notebook (.ipynb) files.
    
    Input:
    - path: .ipynb file path
    - cell_index: Cell to edit (0-based)
    - new_content: New cell content
    - cell_type: "code" or "markdown"
    - action: "replace", "insert", "delete", "append"
    
    Patterns: notebook, jupyter, ipynb, hücre düzenle
    """
    name = "NotebookEdit"
    category = ToolCategory.EDIT
    patterns = ["notebook", "jupyter", "ipynb", "hücre", "cell edit"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        import json
        start = time.time()
        
        path = input_data.get("path", "")
        action = input_data.get("action", "replace")
        cell_index = input_data.get("cell_index", -1)
        new_content = input_data.get("new_content", "")
        cell_type = input_data.get("cell_type", "code")
        
        if not path:
            return ToolResult(self.name, False, "", "path is required", int((time.time()-start)*1000))
        
        if not path.endswith(".ipynb"):
            return ToolResult(self.name, False, "", "Only .ipynb files supported", int((time.time()-start)*1000))
        
        try:
            nb_path = Path(path)
            if not nb_path.exists():
                return ToolResult(self.name, False, "", f"File not found: {path}", int((time.time()-start)*1000))
            
            with open(nb_path) as f:
                nb = json.load(f)
            
            cells = nb.get("cells", [])
            
            if action == "replace":
                if cell_index < 0 or cell_index >= len(cells):
                    return ToolResult(self.name, False, "", f"Cell {cell_index} out of range", int((time.time()-start)*1000))
                cells[cell_index]["source"] = new_content
                cells[cell_index]["cell_type"] = cell_type
            
            elif action == "insert":
                new_cell = {"cell_type": cell_type, "source": new_content, "metadata": {}, " outputs": [], "execution_count": None}
                cells.insert(cell_index, new_cell)
            
            elif action == "append":
                new_cell = {"cell_type": cell_type, "source": new_content, "metadata": {}, "outputs": [], "execution_count": None}
                cells.append(new_cell)
            
            elif action == "delete":
                if cell_index < 0 or cell_index >= len(cells):
                    return ToolResult(self.name, False, "", f"Cell {cell_index} out of range", int((time.time()-start)*1000))
                cells.pop(cell_index)
            
            else:
                return ToolResult(self.name, False, "", f"Unknown action: {action}", int((time.time()-start)*1000))
            
            nb["cells"] = cells
            
            with open(nb_path, "w") as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
            
            return ToolResult(
                self.name, True,
                f"Notebook {action}: {len(cells)} cells",
                duration_ms=int((time.time()-start)*1000),
                metadata={"cells": len(cells), "action": action}
            )
        
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── ListMcpResourcesTool ────────────────────────────────────────────────────

class ListMcpResourcesTool(BaseTool):
    """
    List MCP server resources.
    
    Lists available resources from configured MCP servers.
    
    Patterns: mcp resources, mcp list, resources
    """
    name = "ListMcpResources"
    category = ToolCategory.READ
    patterns = ["mcp resources", "mcp list", "resources", "mcp kaynaklar"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        server = input_data.get("server", "")  # Optional filter
        
        try:
            from ..mcp_pool import get_mcp_pool
            pool = get_mcp_pool()
            servers = pool.list_servers()
            
            if not servers:
                return ToolResult(
                    self.name, True,
                    "No MCP servers configured",
                    duration_ms=int((time.time()-start)*1000),
                )
            
            output = f"{len(servers)} MCP server(s):\n\n"
            for s in servers:
                if server and s["name"] != server:
                    continue
                output += f"[{s['name']}] status={s['status']}\n"
                output += f"  tools: {s['tool_count']}, resources: {s['resource_count']}\n"
                output += f"  command: {s['command'][:60]}\n\n"
            
            return ToolResult(
                self.name, True,
                output,
                duration_ms=int((time.time()-start)*1000),
            )
        
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── ReadMcpResourceTool ─────────────────────────────────────────────────────

class ReadMcpResourceTool(BaseTool):
    """
    Read a specific MCP resource.
    
    Input:
    - uri: Resource URI (e.g., "mcp://server/resource")
    
    Patterns: mcp resource read, resource read, mcp oku
    """
    name = "ReadMcpResource"
    category = ToolCategory.READ
    patterns = ["mcp resource read", "resource read", "mcp oku", "mcp://"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        uri = input_data.get("uri", "")
        
        if not uri:
            return ToolResult(self.name, False, "", "uri is required", int((time.time()-start)*1000))
        
        # Parse mcp://server/resource format
        if uri.startswith("mcp://"):
            parts = uri[6:].split("/", 1)
            server_name = parts[0]
            resource_path = parts[1] if len(parts) > 1 else ""
        else:
            return ToolResult(
                self.name, False, "",
                f"Invalid URI format. Use: mcp://server/resource",
                int((time.time()-start)*1000)
            )
        
        try:
            from ..mcp_pool import get_mcp_pool
            pool = get_mcp_pool()
            
            # Try to read from server's resources
            server = pool.servers.get(server_name)
            if not server:
                return ToolResult(
                    self.name, False, "",
                    f"Server not found: {server_name}",
                    int((time.time()-start)*1000)
                )
            
            # For now, return server info
            return ToolResult(
                self.name, True,
                f"MCP Resource: {uri}\nServer: {server_name}\nPath: {resource_path}\nStatus: {server.status}",
                duration_ms=int((time.time()-start)*1000),
                metadata={"server": server_name, "path": resource_path}
            )
        
        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))


# ─── SyntheticOutputTool ─────────────────────────────────────────────────────

class SyntheticOutputTool(BaseTool):
    """
    Generate structured synthetic output.
    
    Used for test results, formatted reports, structured data.
    
    Input:
    - type: Output type (report, test_result, data, custom)
    - content: Content to format
    - format: "text", "json", "table"
    
    Patterns: synthetic, output, report, sonuç, çıktı
    """
    name = "SyntheticOutput"
    category = ToolCategory.NATURAL
    patterns = ["synthetic", "output", "report", "sonuç", "çıktı", "formatlı çıktı"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        output_type = input_data.get("type", "custom")
        content = input_data.get("content", "")
        format_type = input_data.get("format", "text")
        
        if not content:
            return ToolResult(
                self.name, False, "",
                "content is required",
                int((time.time()-start)*1000)
            )
        
        # Format based on type
        if format_type == "json":
            if isinstance(content, str):
                try:
                    import json
                    content = json.loads(content)
                except:
                    content = {"content": content}
            output = json.dumps(content, indent=2, ensure_ascii=False)
        
        elif format_type == "table":
            if isinstance(content, list):
                if not content:
                    output = "(empty)"
                elif isinstance(content[0], dict):
                    headers = list(content[0].keys())
                    rows = [[str(row.get(h, "")) for h in headers] for row in content]
                    col_widths = [max(len(str(h)), max(len(r[i]) for r in rows)) if rows else len(str(h)) for i, h in enumerate(headers)]
                    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
                    sep = "-+-".join("-" * w for w in col_widths)
                    row_lines = [" | ".join(c.ljust(col_widths[i]) for i, c in enumerate(row)) for row in rows]
                    output = header_line + "\n" + sep + "\n" + "\n".join(row_lines)
                else:
                    output = "\n".join(str(c) for c in content)
            else:
                output = str(content)
        
        else:  # text
            output = str(content)
        
        return ToolResult(
            self.name, True,
            output,
            duration_ms=int((time.time()-start)*1000),
            metadata={"type": output_type, "format": format_type}
        )
