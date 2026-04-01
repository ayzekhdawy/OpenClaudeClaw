"""
MCP Tool Pool — Model Context Protocol desteği
────────────────────────────────────────────
Claude Code'un MCP entegrasyonuna benzer tool havuzu.
"""

from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass
import json
import subprocess
import urllib.request
import urllib.error


WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
MCP_CONFIG = WORKSPACE / ".mcp" / "config.json"


@dataclass
class MCPTool:
    """MCP Tool tanımı."""
    name: str
    description: str
    input_schema: dict
    server_name: str
    server_path: Optional[str] = None


@dataclass
class MCPServer:
    """MCP Server tanımı."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    tools: list[MCPTool]
    status: str = "disconnected"  # connected, disconnected, error
    resources: list[dict] | None = None


class MCPToolPool:
    """
    MCP Tool havuzu.
    Claude Code'un MCP entegrasyonuna benzer.
    """
    
    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.tools: dict[str, MCPTool] = {}
        self._processes: dict[str, Any] = {}
        
        # Config'i yükle
        self._load_config()
    
    def _load_config(self):
        """MCP config dosyasını yükle."""
        if not MCP_CONFIG.exists():
            return
        
        try:
            config = json.loads(MCP_CONFIG.read_text())
            
            # Server tanımlarını al
            servers = config.get("mcpServers", config.get("servers", {}))
            
            for name, server_config in servers.items():
                command = server_config.get("command", "")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                
                server = MCPServer(
                    name=name,
                    command=command,
                    args=args,
                    env=env,
                    tools=[],
                )
                server.resources = server_config.get("resources", [])

                self.servers[name] = server
            
            # Tools tanımlarını al
            tools = config.get("tools", [])
            for tool_config in tools:
                tool = MCPTool(
                    name=tool_config.get("name", ""),
                    description=tool_config.get("description", ""),
                    input_schema=tool_config.get("inputSchema", {}),
                    server_name=tool_config.get("server", ""),
                )
                if tool.name:
                    self.tools[tool.name] = tool
        
        except Exception as e:
            print(f"MCP config error: {e}")
    
    def add_server(self, name: str, command: str, args: list[str] = None, env: dict = None) -> MCPServer:
        """Yeni MCP server ekle."""
        server = MCPServer(
            name=name,
            command=command,
            args=args or [],
            env=env or {},
            tools=[],
            status="disconnected",
        )
        
        self.servers[name] = server
        return server
    
    def remove_server(self, name: str):
        """MCP server sil."""
        if name in self.servers:
            self._stop_server(name)
            del self.servers[name]
    
    def list_servers(self) -> list[dict]:
        """Server listesini döndür."""
        return [
            {
                "name": s.name,
                "status": s.status,
                "tool_count": len(s.tools),
                "resource_count": len(s.resources or []),
                "command": s.command,
            }
            for s in self.servers.values()
        ]
    
    def list_tools(self, server_name: str = None) -> list[dict]:
        """Tool listesini döndür."""
        tools = self.tools.values()
        
        if server_name:
            tools = [t for t in tools if t.server_name == server_name]
        
        return [
            {
                "name": t.name,
                "description": t.description,
                "server": t.server_name,
                "schema": t.input_schema,
            }
            for t in tools
        ]
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Tool getir."""
        return self.tools.get(name)

    def list_resources(self, server_name: str = None) -> list[dict]:
        """Config tabanlı resource listesini döndür."""
        resources = []
        for name, server in self.servers.items():
            if server_name and name != server_name:
                continue
            for resource in server.resources or []:
                resources.append({"server": name, **resource})
        return resources
    
    def discover_tools(self, server_name: str) -> list[MCPTool]:
        """Server'dan tool listesini al."""
        if server_name not in self.servers:
            return []
        
        server = self.servers[server_name]
        
        # MCP protocol: tools/list endpoint
        try:
            # stdio için subprocess başlat
            proc = subprocess.Popen(
                [server.command] + server.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**subprocess.os.environ, **server.env},
            )
            
            # JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
            }
            
            stdout, _ = proc.communicate(
                input=json.dumps(request).encode(),
                timeout=5,
            )
            
            response = json.loads(stdout.decode())
            tools_data = response.get("result", {}).get("tools", [])
            
            tools = []
            for t in tools_data:
                tool = MCPTool(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server_name=server_name,
                )
                tools.append(tool)
                self.tools[tool.name] = tool
            
            server.tools = tools
            server.status = "connected"
            
            return tools
        
        except Exception as e:
            server.status = f"error: {e}"
            return []
    
    def call_tool(self, name: str, arguments: dict) -> dict:
        """Tool çağır."""
        tool = self.tools.get(name)
        
        if not tool:
            return {"error": f"Tool not found: {name}"}
        
        server = self.servers.get(tool.server_name)
        
        if not server:
            return {"error": f"Server not found: {tool.server_name}"}
        
        # MCP protocol: tools/call
        try:
            proc = subprocess.Popen(
                [server.command] + server.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**subprocess.os.environ, **server.env},
            )
            
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments,
                },
            }
            
            stdout, _ = proc.communicate(
                input=json.dumps(request).encode(),
                timeout=30,
            )
            
            response = json.loads(stdout.decode())
            return response.get("result", {})
        
        except Exception as e:
            return {"error": str(e)}
    
    def _stop_server(self, name: str):
        """Server'ı durdur."""
        if name in self._processes:
            try:
                self._processes[name].terminate()
                self._processes[name].wait(timeout=5)
            except Exception:
                pass
            del self._processes[name]
    
    def connect_all(self):
        """Tüm server'lara bağlan."""
        for name in self.servers:
            self.discover_tools(name)
    
    def get_prompt_section(self) -> str:
        """System prompt için MCP section döndür."""
        if not self.tools and not self.list_resources():
            return ""
        
        lines = ["\n\n## MCP Tools\n"]
        lines.append("Bu araçları kullanabilirsin:\n")
        
        by_server = {}
        for tool in self.tools.values():
            server = tool.server_name
            if server not in by_server:
                by_server[server] = []
            by_server[server].append(tool)
        
        for server, server_tools in by_server.items():
            lines.append(f"\n### {server}\n")
            for tool in server_tools:
                lines.append(f"- **{tool.name}**: {tool.description}")
            resources = self.list_resources(server)
            if resources:
                lines.append("- Resources:")
                for resource in resources[:10]:
                    uri = resource.get("uri") or resource.get("name") or "resource"
                    lines.append(f"  - {uri}")

        return '\n'.join(lines)


# Singleton
_mcp_pool: Optional[MCPToolPool] = None


def get_mcp_pool() -> MCPToolPool:
    global _mcp_pool
    if _mcp_pool is None:
        _mcp_pool = MCPToolPool()
    return _mcp_pool


if __name__ == "__main__":
    print("=== MCP TOOL POOL TEST ===\n")
    
    pool = get_mcp_pool()
    
    print(f"Servers: {len(pool.servers)}")
    print(f"Tools: {len(pool.tools)}")
    
    print("\n--- Servers ---")
    for s in pool.list_servers():
        print(f"  - {s['name']}: {s['status']} ({s['tool_count']} tools)")
    
    print("\n--- Prompt Section ---")
    print(pool.get_prompt_section()[:500])
