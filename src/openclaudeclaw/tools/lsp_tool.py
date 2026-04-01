"""
LSPTool — Python Language Server Protocol client
────────────────────────────────────────────────
Claude Code LSPTool referansı.
Python dosyalarında: goto definition, find references, hover, symbols.

Tam LSP değil — Python'un ast modülünü kullanarak benzer işlevsellik sağlar.
"""

import ast
import os
import re
import time
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


class LSPTool(BaseTool):
    """
    Python code intelligence - LSP benzeri.

    Operations:
    - goToDefinition: Bir sembolün tanımına git
    - findReferences: Sembolün kullanıldığı yerleri bul
    - hover: Sembolün dokümantasyonunu göster
    - documentSymbol: Dosyadaki tüm sembolleri listele
    - workspaceSymbol: Tüm dosyalardaki sembolleri ara
    - goToImplementation: Bir sınıfın/trait'in implementasyonlarını bul
    - incomingCalls: Bu fonksiyona kimler çağrı yapıyor
    - outgoingCalls: Bu fonksiyon kimleri çağırıyor

    Patterns: lsp, goto, definition, reference, symbol, hover, import
    """
    name = "LSP"
    category = ToolCategory.READ
    patterns = [
        "lsp", "goto", "definition", "find reference", "symbols",
        "hover", "import", "sembol", "tanım", "referans"
    ]
    readonly = True

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        operation = input_data.get("operation", "")
        file_path = input_data.get("file_path", "")
        line = input_data.get("line", 1)
        character = input_data.get("character", 1)

        if not operation:
            return ToolResult(self.name, False, "", "operation is required", int((time.time()-start)*1000))

        if not file_path:
            return ToolResult(self.name, False, "", "file_path is required", int((time.time()-start)*1000))

        # Resolve path
        cwd = os.getcwd()
        if not os.path.isabs(file_path):
            file_path = os.path.join(cwd, file_path)

        if not os.path.exists(file_path):
            return ToolResult(self.name, False, "", f"File not found: {file_path}", int((time.time()-start)*1000))

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()

            if operation == "goToDefinition":
                result = self._go_to_definition(source, file_path, line, character)
            elif operation == "findReferences":
                result = self._find_references(source, file_path, line, character)
            elif operation == "hover":
                result = self._hover(source, file_path, line, character)
            elif operation == "documentSymbol":
                result = self._document_symbol(source, file_path)
            elif operation == "workspaceSymbol":
                query = input_data.get("query", "")
                result = self._workspace_symbol(query, file_path)
            elif operation == "goToImplementation":
                result = self._go_to_implementation(source, file_path, line, character)
            elif operation == "incomingCalls":
                result = self._incoming_calls(source, file_path, line, character)
            elif operation == "outgoingCalls":
                result = self._outgoing_calls(source, file_path, line, character)
            else:
                return ToolResult(
                    self.name, False, "",
                    f"Unknown operation: {operation}",
                    int((time.time()-start)*1000)
                )

            return ToolResult(
                self.name, True,
                result["output"],
                duration_ms=int((time.time()-start)*1000),
                metadata={"operation": operation, "resultCount": result.get("count", 0)}
            )

        except Exception as e:
            return ToolResult(self.name, False, "", str(e), int((time.time()-start)*1000))

    def _get_symbol_at_cursor(self, source: str, line: int, char: int) -> Optional[tuple[str, ast.AST]]:
        """Get the symbol name and AST node at cursor position."""
        try:
            tree = ast.parse(source)
        except:
            return None

        lines = source.split("\n")
        target_line = line - 1  # 0-indexed
        if target_line < 0 or target_line >= len(lines):
            return None

        target_text = lines[target_line]

        # Find the word at cursor
        # Find identifiers before and after cursor
        before_cursor = target_text[:char-1] if char > 0 else ""
        after_cursor = target_text[char-1:] if char > 0 else target_text

        # Extract word before cursor
        match_before = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b$', before_cursor)
        word_before = match_before.group(1) if match_before else ""

        # Extract word after cursor
        match_after = re.search(r'^([a-zA-Z_][a-zA-Z0-9_]*)', after_cursor)
        word_after = match_after.group(1) if match_after else ""

        symbol_name = word_before or word_after
        if not symbol_name:
            return None

        # Find the AST node that defines this symbol
        node = self._find_symbol_node(tree, symbol_name, line)
        return symbol_name, node if node else None

    def _find_symbol_node(self, tree: ast.AST, name: str, line: int) -> Optional[ast.AST]:
        """Find the AST node that defines a symbol."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if node.name == name and hasattr(node, 'lineno') and node.lineno <= line:
                    return node
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id == name and hasattr(node, 'lineno') and node.lineno <= line:
                    return node
        return None

    def _go_to_definition(self, source: str, file_path: str, line: int, char: int) -> dict:
        """Go to definition of symbol at cursor."""
        result = self._get_symbol_at_cursor(source, line, char)
        if not result:
            return {"output": "No symbol found at cursor", "count": 0}

        symbol_name, node = result

        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            return {
                "output": f"Definition found:\n{symbol_name} @ line {node.lineno}\nType: {type(node).__name__}",
                "count": 1
            }

        # For imports, find the module
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == symbol_name:
                        return {
                            "output": f"Imported from: {node.module}.{alias.asname or alias.name} (line {node.lineno})",
                            "count": 1
                        }
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == symbol_name:
                        return {
                            "output": f"Imported module: {alias.name} (line {node.lineno})",
                            "count": 1
                        }

        return {"output": f"Definition of '{symbol_name}' found at line {line}", "count": 1}

    def _find_references(self, source: str, file_path: str, line: int, char: int) -> dict:
        """Find all references to symbol at cursor."""
        result = self._get_symbol_at_cursor(source, line, char)
        if not result:
            return {"output": "No symbol found", "count": 0}

        symbol_name, _ = result
        lines = source.split("\n")

        refs = []
        for i, line_text in enumerate(lines, 1):
            # Simple word match
            if re.search(rf'\b{symbol_name}\b', line_text):
                refs.append(f"  Line {i}: {line_text.strip()[:80]}")

        return {
            "output": f"References to '{symbol_name}' ({len(refs)} found):\n" + "\n".join(refs[:50]),
            "count": len(refs)
        }

    def _hover(self, source: str, file_path: str, line: int, char: int) -> dict:
        """Get documentation for symbol at cursor."""
        result = self._get_symbol_at_cursor(source, line, char)
        if not result:
            return {"output": "No symbol found", "count": 0}

        symbol_name, node = result

        doc = ast.get_docstring(node) if node else None

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            output = f"**{symbol_name}**({', '.join(args)})\n"
            if doc:
                output += f"\n{doc}"
            return {"output": output, "count": 1}

        if isinstance(node, ast.ClassDef):
            output = f"**class {symbol_name}**\n"
            if doc:
                output += f"\n{doc}"
            return {"output": output, "count": 1}

        return {"output": f"Symbol: {symbol_name}\nType: {type(node).__name__ if node else 'unknown'}", "count": 1}

    def _document_symbol(self, source: str, file_path: str) -> dict:
        """List all symbols in document."""
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return {"output": f"Parse error: {e}", "count": 0}

        symbols = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(f"[def] {node.name} @ line {node.lineno}")
            elif isinstance(node, ast.ClassDef):
                symbols.append(f"[class] {node.name} @ line {node.lineno}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.append(f"[var] {target.id} @ line {node.lineno}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.append(f"[import] {alias.name} @ line {node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    symbols.append(f"[from] {node.module}.{alias.name} @ line {node.lineno}")

        # Sort by line number
        symbols.sort(key=lambda x: int(x.split(" @ line ")[1]))

        return {
            "output": f"Symbols in {os.path.basename(file_path)} ({len(symbols)}):\n" + "\n".join(symbols),
            "count": len(symbols)
        }

    def _workspace_symbol(self, query: str, file_path: str) -> dict:
        """Search symbols across workspace."""
        workspace = Path(os.getcwd())
        py_files = list(workspace.rglob("*.py"))
        py_files = [f for f in py_files if ".venv" not in str(f) and "node_modules" not in str(f)]

        results = []
        for py_file in py_files[:50]:  # Limit to 50 files
            try:
                with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
                tree = ast.parse(source)
            except:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    name = node.name
                    if not query or query.lower() in name.lower():
                        rel_path = py_file.relative_to(workspace)
                        results.append(f"[{type(node).__name__.lower()}] {name} @ {rel_path}:{node.lineno}")

        return {
            "output": f"Symbols matching '{query}' ({len(results)}):\n" + "\n".join(results[:50]),
            "count": len(results)
        }

    def _go_to_implementation(self, source: str, file_path: str, line: int, char: int) -> dict:
        """Find implementations of class/method."""
        result = self._get_symbol_at_cursor(source, line, char)
        if not result:
            return {"output": "No symbol found", "count": 0}

        symbol_name, node = result

        # For classes, find subclasses in workspace
        if isinstance(node, ast.ClassDef):
            workspace = Path(os.getcwd())
            results = []
            for py_file in workspace.rglob("*.py"):
                if ".venv" in str(py_file):
                    continue
                try:
                    with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                        source = f.read()
                    tree = ast.parse(source)
                except:
                    continue

                for n in ast.walk(tree):
                    if isinstance(n, ast.ClassDef):
                        for base in n.bases:
                            if isinstance(base, ast.Name) and base.id == symbol_name:
                                results.append(f"class {n.name} @ {py_file.name}:{n.lineno}")

            return {
                "output": f"Implementations of {symbol_name} ({len(results)}):\n" + "\n".join(results),
                "count": len(results)
            }

        return {"output": f"No implementation found for '{symbol_name}'", "count": 0}

    def _incoming_calls(self, source: str, file_path: str, line: int, char: int) -> dict:
        """Find who calls this function."""
        result = self._get_symbol_at_cursor(source, line, char)
        if not result:
            return {"output": "No symbol found", "count": 0}

        symbol_name, node = result

        # Search workspace for calls
        workspace = Path(os.getcwd())
        calls = []
        for py_file in workspace.rglob("*.py"):
            if ".venv" in str(py_file):
                continue
            try:
                with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                    src = f.read()
            except:
                continue

            for i, line_text in enumerate(src.split("\n"), 1):
                if re.search(rf'\b{symbol_name}\s*\(', line_text):
                    rel = py_file.relative_to(workspace)
                    calls.append(f"  {rel}:{i}: {line_text.strip()[:70]}")

        return {
            "output": f"Calls to '{symbol_name}' ({len(calls)}):\n" + "\n".join(calls[:30]),
            "count": len(calls)
        }

    def _outgoing_calls(self, source: str, file_path: str, line: int, char: int) -> dict:
        """Find what this function calls."""
        result = self._get_symbol_at_cursor(source, line, char)
        if not result:
            return {"output": "No symbol found", "count": 0}

        symbol_name, node = result

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return {"output": "Not a function", "count": 0}

        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.add(child.attr)

        return {
            "output": f"Calls in {symbol_name} ({len(calls)}):\n" + "\n".join(f"  • {c}" for c in sorted(calls)),
            "count": len(calls)
        }
