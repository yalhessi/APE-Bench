"""Lean code tools Provider

Provides LSP tool support and code display functionality for Lean language.
"""

from pathlib import Path
from typing import Annotated, Dict, Any, Set, Optional, List, Tuple

from fastmcp import FastMCP
from pydantic import Field
from leanclient import LeanLSPClient

from ape.toolkits.base import BaseToolsProvider
from ..base_provider import LanguageProviderInterface
from .utils import (
    find_project_path,
    setup_lean_client,
    extract_goals_list,
    format_diagnostics,
    extract_range,
    filter_diagnostics_by_position,
    find_position_by_content,
    get_line_context,
)
from .lean_parser import format_lean_code


class LeanCodeToolsProvider(BaseToolsProvider, LanguageProviderInterface):
    """
    Lean Code Tools Provider

    Dual roles:
    1. Implements LanguageProviderInterface (hover, goto, diagnostics, references)
       for routing by BaseCodeToolsProvider
    2. Inherits BaseToolsProvider, registers Lean-specific tools (get_lean_goal)
    """

    SUPPORTED_TOOLS = [
        "get_lean_goal",
    ]

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

        # Lean LSP client
        self._client: Optional[LeanLSPClient] = None
        self._project_path: Optional[Path] = None

        # Workspace root directory
        self._workspace_root = task.workspaces_dir if task else Path.cwd()

    def _resolve_in_workspace(self, file_path: Path) -> Path:
        """A workspace-relative path made absolute, the way every other toolkit reads one.

        The tools hand these methods exactly what the agent typed --
        `target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean` -- and `find_project_path`
        then walked *up from a relative path*, so it looked for `target/lean-toolchain`
        beneath the process working directory instead of beneath the task's workspace, found
        nothing, and raised. Measured across every ladder run: **122 `get_lean_goal` calls,
        122 failures**, all "Cannot find Lean project". No arm has ever inspected a goal state,
        and the rung whose whole hypothesis was "inspect the goal before proposing" could not
        have passed.

        Same rules as `file_system.core._resolve_path`, deliberately: relative joins onto the
        workspace root, `..` is refused, and an already-absolute path is left alone so callers
        that resolve for themselves keep working.
        """

        if file_path.is_absolute():
            return file_path
        if ".." in file_path.parts:
            raise ValueError(
                f"Parent directory references (..) are not allowed: {file_path}")
        return (Path(self._workspace_root) / file_path).resolve()

    def _ensure_client(self, file_path: Path) -> LeanLSPClient:
        """Ensure LSP client is initialized"""
        project_path = find_project_path(file_path)
        if not project_path:
            raise ValueError(f"Cannot find Lean project for {file_path}")

        if self._project_path != project_path:
            if self._client:
                self._client.close()

            self._client = setup_lean_client(project_path)
            self._project_path = project_path

        return self._client

    def _get_relative_path(self, file_path: Path) -> str:
        """Get path relative to project"""
        if not self._project_path:
            raise ValueError("Project path not set")

        try:
            return str(file_path.relative_to(self._project_path))
        except ValueError:
            raise ValueError(f"File {file_path} not in project {self._project_path}")

    # ========== Display functionality (as class methods) ==========

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
        body_placeholder: str = "/- ... omitted ... -/"
    ) -> str:
        """Display Lean code with optional body omission.

        Args:
            content: Source code content
            add_line_numbers: Whether to add line numbers
            display_mode: Display mode ("full" or "line_spans")
            line_spans: List of (start, end) line ranges to display
            context_lines: Number of context lines around each span
            range_separator: Separator between ranges
            omit_details: Whether to omit body details (deprecated, use body_handling)
            body_handling: Explicit body handling mode ("keep_all", "omit_all", "omit_outside_spans")
            body_placeholder: Placeholder text for omitted bodies

        Returns:
            Formatted code with line numbers

        Note:
            For Lean, "body" refers to proof content in theorems and lemmas.
        """
        # Determine body_handling: explicit parameter takes precedence over omit_details
        if body_handling is None:
            body_handling = "omit_all" if omit_details else "keep_all"

        # Map generic body_handling to Lean-specific proof_handling
        return format_lean_code(
            src=content,
            display_mode=display_mode,
            proof_handling=body_handling,  # Lean internally uses proof_handling
            line_spans=line_spans,
            context_lines=context_lines,
            add_line_numbers=add_line_numbers,
            proof_placeholder=body_placeholder,  # Lean internally uses proof_placeholder
            range_separator=range_separator
        )

    @staticmethod
    def get_omission_marker(text: str = None) -> str:
        """Get omission marker for Lean."""
        default_text = text or "... omitted lines ..."
        return f"/- {default_text} -/"

    @staticmethod
    def remove_comments(content: str) -> str:
        """Remove Lean comments from source code."""
        i = 0
        n = len(content)
        out = []
        block_nest = 0
        line_has_code = False

        while i < n:
            if block_nest == 0:
                if content.startswith("--", i):
                    j = content.find("\n", i + 2)
                    if not line_has_code:
                        while out and out[-1] in (" ", "\t"):
                            out.pop()
                        if j == -1:
                            i = n
                        else:
                            i = j + 1
                        line_has_code = False
                    else:
                        if j == -1:
                            i = n
                        else:
                            i = j + 1
                            out.append("\n")
                        line_has_code = False
                elif content.startswith("/-", i):
                    block_nest = 1
                    i += 2
                else:
                    ch = content[i]
                    out.append(ch)
                    if ch == "\n":
                        line_has_code = False
                    elif not ch.isspace():
                        line_has_code = True
                    i += 1
            else:
                if content.startswith("/-", i):
                    block_nest += 1
                    i += 2
                elif content.startswith("-/", i):
                    block_nest -= 1
                    i += 2
                else:
                    i += 1
        return "".join(out)

    # ========== Implement LanguageProviderInterface (for routing) ==========

    async def hover(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Implement hover interface"""
        try:
            file_path = self._resolve_in_workspace(file_path)
            client = self._ensure_client(file_path)
            rel_path = self._get_relative_path(file_path)

            client.open_file(rel_path)
            file_content = client.get_file_content(rel_path)

            position = find_position_by_content(file_content, line, content_snippet)
            if not position:
                return {
                    "success": False,
                    "error": f"Cannot find '{content_snippet}' at line {line}"
                }

            line_idx, char_idx = position
            hover_result = client.get_hover(rel_path, line_idx, char_idx)

            if not hover_result or not hover_result.get("contents"):
                return {
                    "success": False,
                    "error": "No hover information available"
                }

            hover_info = hover_result["contents"].get("value", "")
            hover_info = hover_info.replace("```lean\n", "").replace("\n```", "").strip()

            h_range = hover_result.get("range")
            symbol = extract_range(file_content, h_range) if h_range else content_snippet

            diagnostics = client.get_diagnostics(rel_path)
            filtered_diags = filter_diagnostics_by_position(diagnostics, line_idx, char_idx)

            context = get_line_context(file_content, line, context_lines=3)

            return {
                "success": True,
                "hover_content": hover_info,
                "symbol": symbol,
                "range": h_range,
                "diagnostics": format_diagnostics(filtered_diags),
                "context": context
            }

        except Exception as e:
            self.logger.error(f"Lean hover error: {e}")
            return {"success": False, "error": str(e)}

    async def goto(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Implement goto interface"""
        try:
            file_path = self._resolve_in_workspace(file_path)
            client = self._ensure_client(file_path)
            rel_path = self._get_relative_path(file_path)

            client.open_file(rel_path)
            file_content = client.get_file_content(rel_path)

            position = find_position_by_content(file_content, line, content_snippet)
            if not position:
                return {
                    "success": False,
                    "error": f"Cannot find '{content_snippet}' at line {line}"
                }

            line_idx, char_idx = position
            declarations = client.get_declarations(rel_path, line_idx, char_idx)

            if not declarations:
                return {"success": True, "definitions": []}

            definitions = []
            for decl in declarations:
                decl_uri = decl.get("targetUri") or decl.get("uri")
                decl_path = Path(client._uri_to_abs(decl_uri))

                try:
                    relative_path = decl_path.relative_to(self._workspace_root)
                except ValueError:
                    relative_path = decl_path

                decl_range = decl.get("targetRange") or decl.get("range")
                with open(decl_path, 'r') as f:
                    decl_content = f.read()

                content = extract_range(decl_content, decl_range)

                definitions.append({
                    "file_path": str(relative_path),
                    "line": decl_range["start"]["line"] + 1,
                    "character": decl_range["start"]["character"],
                    "content": content
                })

            return {
                "success": True,
                "definitions": definitions
            }

        except Exception as e:
            self.logger.error(f"Lean goto error: {e}")
            return {"success": False, "error": str(e)}

    async def diagnostics(self, file_path: Path) -> Dict[str, Any]:
        """Implement diagnostics interface"""
        try:
            file_path = self._resolve_in_workspace(file_path)
            client = self._ensure_client(file_path)
            rel_path = self._get_relative_path(file_path)

            client.open_file(rel_path)
            diagnostics = client.get_diagnostics(rel_path, inactivity_timeout=15.0)

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
            self.logger.error(f"Lean diagnostics error: {e}")
            return {"success": False, "error": str(e)}

    # async def references(
    #     self,
    #     file_path: Path,
    #     line: int,
    #     content_snippet: str
    # ) -> Dict[str, Any]:
    #     """Implement references interface"""
    #     try:
    #         client = self._ensure_client(file_path)
    #         rel_path = self._get_relative_path(file_path)

    #         client.open_file(rel_path)
    #         file_content = client.get_file_content(rel_path)

    #         position = find_position_by_content(file_content, line, content_snippet)
    #         if not position:
    #             return {
    #                 "success": False,
    #                 "error": f"Cannot find '{content_snippet}' at line {line}"
    #             }

    #         line_idx, char_idx = position
    #         references = client.get_references(rel_path, line_idx, char_idx)

    #         formatted_refs = []
    #         for ref in references:
    #             ref_uri = ref["uri"]
    #             ref_path = Path(client._uri_to_abs(ref_uri))

    #             try:
    #                 relative_path = ref_path.relative_to(self._workspace_root)
    #             except ValueError:
    #                 relative_path = ref_path

    #             ref_range = ref["range"]
    #             formatted_refs.append({
    #                 "file_path": str(relative_path),
    #                 "line": ref_range["start"]["line"] + 1,
    #                 "character": ref_range["start"]["character"]
    #             })

    #         return {
    #             "success": True,
    #             "references": formatted_refs,
    #             "count": len(formatted_refs)
    #         }

    #     except Exception as e:
    #         self.logger.error(f"Lean references error: {e}")
    #         return {"success": False, "error": str(e)}

    # ========== Lean-specific methods ==========

    async def get_goal(
        self,
        file_path: Path,
        line: int,
        content_snippet: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lean-specific: Get proof goals"""
        try:
            file_path = self._resolve_in_workspace(file_path)
            client = self._ensure_client(file_path)
            rel_path = self._get_relative_path(file_path)

            client.open_file(rel_path)
            file_content = client.get_file_content(rel_path)
            lines = file_content.splitlines()

            if line < 1 or line > len(lines):
                return {"success": False, "error": f"Line {line} out of range"}

            line_idx = line - 1
            line_context = lines[line_idx]

            if content_snippet:
                # Exact position
                position = find_position_by_content(file_content, line, content_snippet)
                if not position:
                    return {
                        "success": False,
                        "error": f"Cannot find '{content_snippet}' at line {line}"
                    }

                _, char_idx = position
                goal_result = client.get_goal(rel_path, line_idx, char_idx)

                return {
                    "success": True,
                    "line_context": line_context,
                    "goals": extract_goals_list(goal_result)
                }
            else:
                # before/after
                col_start = next((i for i, c in enumerate(line_context) if not c.isspace()), 0)
                col_end = len(line_context)

                goal_before = client.get_goal(rel_path, line_idx, col_start)
                goal_after = client.get_goal(rel_path, line_idx, col_end)

                return {
                    "success": True,
                    "line_context": line_context,
                    "goals_before": extract_goals_list(goal_before),
                    "goals_after": extract_goals_list(goal_after)
                }

        except Exception as e:
            self.logger.error(f"Lean get_goal error: {e}")
            return {"success": False, "error": str(e)}

    # ========== Register Lean-specific tools ==========

    def register_tools(self, mcp: FastMCP, enabled_tools: Set[str]) -> None:
        """Register Lean-specific tools"""

        if "get_lean_goal" in enabled_tools:
            @mcp.tool(description="""Get Lean proof goals at position.

**Two modes**:
- With content: exact position goal
- Without content: goals before/after line

**Returns**: Current proof state (goals list)""")
            async def get_lean_goal(
                file_path: Annotated[str, Field(description="Workspace file path (e.g., scratch/theorem.lean)")],
                line: Annotated[int, Field(description="Line number (1-indexed)", ge=1)],
                content: Annotated[
                    Optional[str],
                    Field(description="Content snippet at position (omit for before/after mode)")
                ] = None
            ) -> Dict[str, Any]:
                """Get Lean proof goals"""
                return await self.get_goal(Path(file_path), line, content)

    async def cleanup(self) -> None:
        """Clean up Lean LSP client"""
        if self._client:
            try:
                self._client.close()
                self.logger.debug("Lean LSP client closed")
            except Exception as e:
                self.logger.warning(f"Error closing Lean LSP client: {e}")


# Register tool at end of file
from ape.toolkits.registry import register_tool
register_tool(LeanCodeToolsProvider)
