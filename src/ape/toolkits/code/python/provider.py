"""Python code tools Provider"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Set, Optional, List, Tuple
import ast

from ape.toolkits.base import BaseToolsProvider
from ..base_provider import LanguageProviderInterface
from .utils import (
    find_position_by_content,
    get_line_context,
    format_diagnostics,
    extract_range_content,
)


class PythonCodeToolsProvider(BaseToolsProvider, LanguageProviderInterface):
    """
    Python Code Tools Provider

    Implements LanguageProviderInterface (hover, goto, diagnostics, references)
    for routing by BaseCodeToolsProvider.

    Uses pylsp (Python Language Server Protocol)
    """

    SUPPORTED_TOOLS = []

    def __init__(
        self,
        task=None,
        config=None,
        logger=None,
        confirmation_bridge=None,
        is_cli_mode=False,
    ):
        super().__init__(
            task=task,
            config=config,
            logger=logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )

        # pylspclient related
        self._lsp_process: Optional[subprocess.Popen] = None
        self._lsp_client = None
        self._initialized = False

        # Workspace root directory
        self._workspace_root = task.workspaces_dir if task else Path.cwd()

        # Open files
        self._open_files: Dict[str, str] = {}  # uri -> content

    async def _ensure_lsp_started(self):
        """Ensure Python LSP server is started"""
        if self._initialized:
            return

        try:
            # Start pylsp process
            self._lsp_process = subprocess.Popen(
                ['pylsp'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self._workspace_root)
            )

            # Create LSP client (using pylspclient library)
            from pylspclient import LspClient, LspEndpoint

            lsp_endpoint = LspEndpoint(
                self._lsp_process.stdout,
                self._lsp_process.stdin
            )
            self._lsp_client = LspClient(lsp_endpoint)

            # Initialize
            root_uri = self._workspace_root.as_uri()
            self._lsp_client.initialize(
                processId=self._lsp_process.pid,
                rootUri=root_uri,
                rootPath=str(self._workspace_root)
            )
            self._lsp_client.initialized()

            self._initialized = True
            self.logger.debug("Python LSP server started")

        except FileNotFoundError:
            self.logger.error("pylsp not found. Install with: pip install python-lsp-server")
            raise ValueError("pylsp not installed")
        except Exception as e:
            self.logger.error(f"Failed to start Python LSP: {e}")
            raise

    def _path_to_uri(self, file_path: Path) -> str:
        """Convert path to URI"""
        return file_path.resolve().as_uri()

    def _uri_to_path(self, uri: str) -> Path:
        """Convert URI to path"""
        from urllib.parse import urlparse, unquote
        parsed = urlparse(uri)
        return Path(unquote(parsed.path))

    # ========== Display functionality (as static methods) ==========

    @staticmethod
    def display_content(
        content: str,
        add_line_numbers: bool = True,
        display_mode: str = "full",
        line_spans: Optional[List[Tuple[int, int]]] = None,
        context_lines: int = 3,
        range_separator: str = "\n",
        omit_details: bool = False,
        body_handling: Optional[str] = None,
        body_placeholder: str = "# ... omitted ... #"
    ) -> str:
        """Display Python code with line numbers.

        Args:
            content: Source code content
            add_line_numbers: Whether to add line numbers
            display_mode: Display mode ("full" or "line_spans")
            line_spans: List of (start, end) line ranges to display
            context_lines: Number of context lines around each span
            range_separator: Separator between ranges
            omit_details: Whether to omit function bodies (deprecated, use body_handling)
            body_handling: Body handling mode ("keep_all", "omit_all", "omit_outside_spans")
            body_placeholder: Placeholder text for omitted bodies

        Returns:
            Formatted code with line numbers

        Note:
            For Python, "body" refers to function body content.
            body_handling modes:
            - "keep_all": Show all function bodies
            - "omit_all": Omit all function bodies (top-level only)
            - "omit_outside_spans": Same as keep_all for Python (not implemented)
        """
        # Determine body_handling: explicit parameter takes precedence over omit_details
        if body_handling is None:
            body_handling = "omit_all" if omit_details else "keep_all"

        # Apply body omission if requested
        formatted_content = content
        if body_handling == "omit_all":
            try:
                formatted_content = PythonCodeToolsProvider._omit_function_bodies(
                    content,
                    body_placeholder
                )
            except Exception:
                # If AST parsing fails, use original content
                formatted_content = content

        lines = formatted_content.splitlines()

        if display_mode == "line_spans" and line_spans:
            # Display only specified line spans with context
            result_lines = []
            for start, end in line_spans:
                # Add context
                context_start = max(1, start - context_lines)
                context_end = min(len(lines), end + context_lines)

                if result_lines:
                    result_lines.append(range_separator)

                for i in range(context_start - 1, context_end):
                    if add_line_numbers:
                        result_lines.append(f"{i+1:6d}|{lines[i]}")
                    else:
                        result_lines.append(lines[i])

            return '\n'.join(result_lines)
        else:
            # Full display
            if add_line_numbers:
                return '\n'.join(f"{i+1:6d}|{line}" for i, line in enumerate(lines))
            else:
                return formatted_content

    @staticmethod
    def get_omission_marker(text: str = None) -> str:
        """Get omission marker for Python."""
        default_text = text or "... omitted lines ..."
        return f"# {default_text}"

    @staticmethod
    def remove_comments(content: str) -> str:
        """Remove Python comments from source code."""
        import re
        lines = content.splitlines(keepends=True)
        result = []

        for line in lines:
            # Remove inline comments
            stripped = re.sub(r'#.*$', '', line)
            # Keep line if it has non-whitespace content
            if stripped.strip():
                result.append(stripped.rstrip() + '\n' if line.endswith('\n') else stripped)
            elif not line.strip():
                # Keep blank lines
                result.append(line)

        return ''.join(result)

    @staticmethod
    def _omit_function_bodies(content: str, body_placeholder: str = "# ... omitted ... #") -> str:
        """Omit function bodies, keep function signatures.

        Args:
            content: Python source code
            body_placeholder: Placeholder text for omitted bodies

        Returns:
            Code with function bodies replaced by placeholder comments
        """

        tree = ast.parse(content)
        lines = content.splitlines()

        # Collect top-level function definition nodes, avoid nested function issues
        function_nodes = []

        # Only process top-level functions (functions not inside other functions)
        def collect_top_level_functions(node, parent_is_function=False):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not parent_is_function:
                    function_nodes.append(node)
                # Mark parent as function when recursively processing child nodes
                for child in ast.iter_child_nodes(node):
                    collect_top_level_functions(child, True)
            else:
                # For non-function nodes, continue recursively but don't change parent_is_function state
                for child in ast.iter_child_nodes(node):
                    collect_top_level_functions(child, parent_is_function)

        collect_top_level_functions(tree)

        # Sort by end line number in descending order, ensure processing from back to front
        function_nodes.sort(key=lambda n: n.end_lineno, reverse=True)

        # Process each function
        for node in function_nodes:
            signature_end_line = PythonCodeToolsProvider._find_signature_end_line(node, lines)

            # If function has body (function body start line <= function end line)
            if signature_end_line <= node.end_lineno:
                # Calculate function signature indentation
                func_line = lines[node.lineno - 1]
                indent = PythonCodeToolsProvider._get_line_indent(func_line)
                # Create replacement content: comment with custom placeholder
                body_indent = indent + "    "
                replacement_lines = [
                    f"{body_indent}{body_placeholder}"
                ]

                # Replace function body part (note: need to convert 1-based line number to 0-based index)
                start_idx = signature_end_line - 1
                end_idx = node.end_lineno  # end_lineno is 1-based, slice is exactly the end position not included
                lines[start_idx:end_idx] = replacement_lines

        return '\n'.join(lines)

    @staticmethod
    def _find_signature_end_line(node: 'ast.FunctionDef', lines: List[str]) -> int:
        """Find the line number where the function signature ends (after the colon).

        Args:
            node: AST function definition node
            lines: Source code lines

        Returns:
            Line number where function body starts (1-indexed)
        """
        # Function body start line number (line number of first body node in AST)
        if node.body:
            first_body_line = node.body[0].lineno
            return first_body_line

        # If there is no body, find colon from function start line
        for line_idx in range(node.lineno - 1, node.end_lineno):
            line = lines[line_idx]
            if ':' in line:
                return line_idx + 1

        # Fallback: return function end line
        return node.end_lineno

    @staticmethod
    def _get_line_indent(line: str) -> str:
        """Get line indentation.

        Args:
            line: Source code line

        Returns:
            Indentation string (spaces/tabs before first non-whitespace character)
        """
        return line[:len(line) - len(line.lstrip())]

    async def _ensure_file_open(self, file_path: Path) -> str:
        """Ensure file is open in LSP"""
        await self._ensure_lsp_started()

        uri = self._path_to_uri(file_path)

        if uri in self._open_files:
            return uri

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Open file
        self._lsp_client.didOpen(
            textDocument={
                'uri': uri,
                'languageId': 'python',
                'version': 1,
                'text': content
            }
        )

        self._open_files[uri] = content
        return uri

    # ========== Implement LanguageProviderInterface ==========

    async def hover(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Implement hover interface"""
        try:
            uri = await self._ensure_file_open(file_path)

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Find position
            position = find_position_by_content(file_content, line, content_snippet)
            if not position:
                return {
                    "success": False,
                    "error": f"Cannot find '{content_snippet}' at line {line}"
                }

            line_idx, char_idx = position

            # Call LSP hover
            hover_result = self._lsp_client.hover(
                textDocument={'uri': uri},
                position={'line': line_idx, 'character': char_idx}
            )

            if not hover_result or not hover_result.get('contents'):
                return {
                    "success": False,
                    "error": "No hover information available"
                }

            # Format contents
            contents = hover_result['contents']
            if isinstance(contents, str):
                hover_text = contents
            elif isinstance(contents, dict) and 'value' in contents:
                hover_text = contents['value']
            elif isinstance(contents, list):
                hover_text = '\n\n'.join(
                    item['value'] if isinstance(item, dict) else str(item)
                    for item in contents
                )
            else:
                hover_text = str(contents)

            # Clean markdown markers
            hover_text = hover_text.replace("```python\n", "").replace("\n```", "").strip()

            context = get_line_context(file_content, line, context_lines=3)

            return {
                "success": True,
                "hover_content": hover_text,
                "symbol": content_snippet,
                "range": hover_result.get('range'),
                "diagnostics": [],  # pylsp hover doesn't return diagnostics
                "context": context
            }

        except Exception as e:
            self.logger.error(f"Python hover error: {e}")
            return {"success": False, "error": str(e)}

    async def goto(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Implement goto interface"""
        try:
            uri = await self._ensure_file_open(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            position = find_position_by_content(file_content, line, content_snippet)
            if not position:
                return {
                    "success": False,
                    "error": f"Cannot find '{content_snippet}' at line {line}"
                }

            line_idx, char_idx = position

            # Call LSP definition
            definition_result = self._lsp_client.definition(
                textDocument={'uri': uri},
                position={'line': line_idx, 'character': char_idx}
            )

            if not definition_result:
                return {"success": True, "definitions": []}

            # Process result (could be single Location or Location array)
            locations = definition_result if isinstance(definition_result, list) else [definition_result]

            definitions = []
            for loc in locations:
                def_uri = loc['uri']
                def_range = loc['range']
                def_path = self._uri_to_path(def_uri)

                # Relative path
                try:
                    relative_path = def_path.relative_to(self._workspace_root)
                except ValueError:
                    relative_path = def_path

                # Read definition content
                try:
                    with open(def_path, 'r', encoding='utf-8') as f:
                        def_content = f.read()

                    content = extract_range_content(def_content, def_range)
                except Exception:
                    content = ""

                definitions.append({
                    "file_path": str(relative_path),
                    "line": def_range["start"]["line"] + 1,
                    "character": def_range["start"]["character"],
                    "content": content
                })

            return {
                "success": True,
                "definitions": definitions
            }

        except Exception as e:
            self.logger.error(f"Python goto error: {e}")
            return {"success": False, "error": str(e)}

    async def diagnostics(self, file_path: Path) -> Dict[str, Any]:
        """Implement diagnostics interface"""
        try:
            uri = await self._ensure_file_open(file_path)

            # Wait for LSP processing (simple delay)
            await asyncio.sleep(0.5)

            # pylspclient automatically collects diagnostics
            # But we need to actively get them, use a simple method here:
            # Reopen file to trigger diagnostics
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self._lsp_client.didChange(
                textDocument={'uri': uri, 'version': 2},
                contentChanges=[{'text': content}]
            )

            # Wait a bit more
            await asyncio.sleep(0.5)

            # Get diagnostics (simplified here, should actually listen to publishDiagnostics notification)
            # Due to pylspclient limitations, we return empty list here
            # Real implementation needs to listen to diagnostics notifications
            diagnostics = []

            formatted = format_diagnostics(diagnostics)

            error_count = sum(1 for d in formatted if d["severity"] == "error")
            warning_count = sum(1 for d in formatted if d["severity"] == "warning")

            return {
                "success": True,
                "diagnostics": formatted,
                "error_count": error_count,
                "warning_count": warning_count,
                "has_errors": error_count > 0
            }

        except Exception as e:
            self.logger.error(f"Python diagnostics error: {e}")
            return {"success": False, "error": str(e)}

    async def references(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Implement references interface"""
        try:
            uri = await self._ensure_file_open(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            position = find_position_by_content(file_content, line, content_snippet)
            if not position:
                return {
                    "success": False,
                    "error": f"Cannot find '{content_snippet}' at line {line}"
                }

            line_idx, char_idx = position

            # Call LSP references
            references_result = self._lsp_client.references(
                textDocument={'uri': uri},
                position={'line': line_idx, 'character': char_idx},
                context={'includeDeclaration': True}
            )

            if not references_result:
                return {"success": True, "references": [], "count": 0}

            formatted_refs = []
            for ref in references_result:
                ref_uri = ref['uri']
                ref_range = ref['range']
                ref_path = self._uri_to_path(ref_uri)

                try:
                    relative_path = ref_path.relative_to(self._workspace_root)
                except ValueError:
                    relative_path = ref_path

                formatted_refs.append({
                    "file_path": str(relative_path),
                    "line": ref_range["start"]["line"] + 1,
                    "character": ref_range["start"]["character"]
                })

            return {
                "success": True,
                "references": formatted_refs,
                "count": len(formatted_refs)
            }

        except Exception as e:
            self.logger.error(f"Python references error: {e}")
            return {"success": False, "error": str(e)}

    # ========== Register tools (Python currently has no specific tools) ==========

    def register_tools(self, mcp, enabled_tools: Set[str]) -> None:
        """Register Python-specific tools (none currently)"""
        pass

    async def cleanup(self) -> None:
        """Clean up Python LSP resources"""
        # Close all open files
        for uri in list(self._open_files.keys()):
            try:
                self._lsp_client.didClose(textDocument={'uri': uri})
            except Exception:
                pass

        self._open_files.clear()

        # Close LSP client
        if self._lsp_client:
            try:
                self._lsp_client.shutdown()
                self._lsp_client.exit()
            except Exception as e:
                self.logger.warning(f"Error shutting down Python LSP client: {e}")

        # Terminate LSP process
        if self._lsp_process:
            try:
                self._lsp_process.terminate()
                self._lsp_process.wait(timeout=5)
            except Exception:
                try:
                    self._lsp_process.kill()
                except Exception as e:
                    self.logger.warning(f"Error killing Python LSP process: {e}")

        self._initialized = False
        self.logger.debug("Python LSP cleaned up")


# Register tool at end of file
from ape.toolkits.registry import register_tool
register_tool(PythonCodeToolsProvider)
