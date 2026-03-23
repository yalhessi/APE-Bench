"""
File System Tools Provider - Enhanced MCP tool registration (refactored version)

Uses explicit workspace parameter design, reference LeanVerifyTool mode.
"""

from typing import Dict, Any, List, Optional, Annotated, TYPE_CHECKING
from pathlib import Path
from fastmcp import FastMCP
from pydantic import Field
from ape.utils.logging import create_logger
from .core import FileSystemProvider
from ape.toolkits.base import BaseToolsProvider

if TYPE_CHECKING:
    from ape.tasks.base import BaseTask
    import logging


class FileSystemToolsProvider(BaseToolsProvider):
    """
    File system tools provider

    Implements explicit workspace parameter design, provides detailed usage instructions.
    """

    SUPPORTED_TOOLS = ["file_read", "content_search", "file_search", "file_write", "file_diff", "file_edit", "file_multi_edit", "extract_pdf_text"]

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        """Initialize file system tools provider"""
        # Call parent constructor
        super().__init__(
            task=task,
            config=config,
            logger=logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )

        # Override logger if not provided
        if not self.logger:
            self.logger = create_logger()

        self.scaffold_config = config

        # Create FileSystemProvider with full scaffold config
        self.file_system = FileSystemProvider(
            task=self.task,
            config=config,
            logger=self.logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )

        self.logger.info("FileSystemToolsProvider initialized")

    def sync_tool_instances(self, tool_instances: Dict[type, "BaseToolsProvider"]) -> None:
        """Sync tool instances to both this provider and the internal FileSystemProvider."""
        super().sync_tool_instances(tool_instances)
        # Also sync to the internal FileSystemProvider
        self.file_system.tool_instances = tool_instances

    def register_tools(self, mcp: FastMCP, enabled_tools: set[str]):
        """Register all file operation tools to MCP server"""
        
        # Check if there is a confirmation mechanism (CLI mode)
        has_confirmation = self.confirmation_bridge is not None
        default_show_modified_content = self.file_system.fs_config.show_modified_content
        
        if "file_read" in enabled_tools:
            @mcp.tool(
                description="""Read file content with optional line range.

**OUTPUT**: Lines prefixed with `LINE_NUMBER|CONTENT` (line numbers are display metadata only).

**DEFAULT**: `line_range` defaults to `[1, 200]`.

**RANGE SEMANTICS**: `line_range=[start, end]` uses Python-style slicing on 1-indexed lines:
- `[start, end)` - end is exclusive
- Negative indices: -1 is last line, -2 is second-to-last, etc.
- None for start means "from the beginning", None for end means "to the end"
- Examples: `[None, None]` = all lines, `[None, 10]` = first 9 lines, `[10, None]` = from line 10 to end, `[-10, None]` = last 10 lines, `[None, -1]` = all except last

**WARNING**: Large ranges can be expensive; keep reads focused.

**IMPORTANT**: When `omit_details=True`, markers like `/- ... omitted proof ... -/` are display-only, NOT actual file content. Never include them when writing files."""
            )
            async def file_read(
                file_path: Annotated[str, Field(
                    description="Workspace file path (e.g., scratch/file.lean)"
                )],
                line_range: Annotated[Optional[list], Field(
                    description="Read specific lines [start, end). Both can be None/int/negative. Examples: [None, None] = all, [None, 10] = first 9, [10, None] = from 10, [-10, None] = last 10"
                )] = [1, 200],
                omit_details: Annotated[bool, Field(
                    description="Hide implementation details (proofs, function bodies) with display-only markers"
                )] = True
            ) -> Dict[str, Any]:
                """Read file content."""
                self.logger.info(f"Tool file_read: execution started (file_path={file_path})")
                result = await self.file_system.file_read(
                    file_path=Path(file_path),
                    line_range=line_range,
                    omit_details=omit_details
                )
                self.logger.info(f"Tool file_read: execution completed")
                return result
        
        if "content_search" in enabled_tools:
            @mcp.tool(
                description="""Search file contents using text or regex patterns.

**OUTPUT**: Matches as `LINE_NUMBER|CONTENT` (line numbers are display metadata)"""
            )
            async def content_search(
                content_pattern: Annotated[str, Field(
                    description="Text or regex pattern to search for"
                )],
                path: Annotated[str, Field(
                    description="Workspace path (e.g., scratch/path/to/file). Supports files, directories, wildcards"
                )],
                recursive: Annotated[bool, Field(
                    description="Search recursively in subdirectories"
                )] = True,
                limit: Annotated[int, Field(
                    description="Maximum files to return"
                )] = 20,
                max_matches_per_file: Annotated[int, Field(
                    description="Maximum matches per file"
                )] = 10,
                timeout: Annotated[float, Field(
                    description="Timeout in seconds for regex matching per file"
                )] = 5.0,
                use_regex: Annotated[bool, Field(
                    description="Use regex (True) or simple string matching (False)"
                )] = True,
                A: Annotated[Optional[int], Field(
                    description="Lines after each match (grep -A)"
                )] = None,
                B: Annotated[Optional[int], Field(
                    description="Lines before each match (grep -B)"
                )] = None,
                C: Annotated[Optional[int], Field(
                    description="Lines before and after each match (grep -C, overrides A/B)"
                )] = 2
            ) -> Dict[str, Any]:
                """Search for files containing specific content patterns."""
                self.logger.info(f"Tool content_search: execution started (pattern={content_pattern[:50]}, path={path})")

                result = await self.file_system.content_search(
                    content_pattern=content_pattern,
                    search_path=Path(path),
                    recursive=recursive,
                    max_results=limit,
                    max_matches_per_file=max_matches_per_file,
                    timeout=timeout,
                    use_regex=use_regex,
                    A=A,
                    B=B,
                    C=C
                )
                self.logger.info(f"Tool content_search: execution completed")
                return result
        
        if "file_search" in enabled_tools:
            @mcp.tool(
                description="Search for files by name patterns (glob)"
            )
            async def file_search(
                pattern: Annotated[str, Field(
                    description="File name pattern (e.g., '*.lean', '*Nat*')"
                )],
                directory_path: Annotated[str, Field(
                    description="Workspace directory path (e.g., scratch/ or target/subdir)"
                )],
                recursive: Annotated[bool, Field(
                    description="Search recursively in subdirectories"
                )] = True,
                limit: Annotated[int, Field(
                    description="Maximum results to return"
                )] = 50
            ) -> Dict[str, Any]:
                """Search for files by name patterns."""
                self.logger.info(f"Tool file_search: execution started (directory_path={directory_path})")

                result = await self.file_system.file_search(
                    pattern=pattern,
                    directory_path=Path(directory_path),
                    recursive=recursive,
                    max_results=limit
                )
                self.logger.info(f"Tool file_search: execution completed")
                return result
        
        if "file_write" in enabled_tools:
            if has_confirmation:
                write_desc = """Write complete file content (create or overwrite). Use file_edit for modifying existing files.

**EXECUTION**: When execute=True (default), the tool automatically runs the registered verifier or executor for that file type.

**USER CONFIRMATION**: Writing to target workspace will automatically prompt for user confirmation before applying changes.

**IMPORTANT**: Write actual code only - no line numbers or display markers."""
            else:
                write_desc = """Write complete file content (create or overwrite). Use file_edit for modifying existing files.

**EXECUTION**: When execute=True (default), the tool automatically runs the registered verifier or executor for that file type.

**IMPORTANT**: Write actual code only - no line numbers or display markers."""

            @mcp.tool(description=write_desc)
            async def file_write(
                file_path: Annotated[str, Field(
                    description="Workspace file path (e.g., scratch/solution.lean)"
                )],
                content: Annotated[str, Field(
                    description="Complete file content as plain text (actual code only, no line numbers or markers)"
                )],
                execute: Annotated[bool, Field(
                    description="Auto-run the registered verifier or executor after writing (for example Lean verification, Isabelle theory checking, or Bash execution)"
                )] = True,
                show_content: Annotated[bool, Field(
                    description="Include file content in return"
                )] = True,
                context_lines: Annotated[int, Field(
                    description="Max lines to show from start/end when show_content=True"
                )] = 10
            ) -> Dict[str, Any]:
                """Write complete file content with optional verification."""
                self.logger.info(f"Tool file_write: execution started (file_path={file_path})")
                result = await self.file_system.file_write(
                    file_path=Path(file_path),
                    content=content,
                    execute=execute,
                    show_content=show_content,
                    context_lines=context_lines,
                    max_messages=None
                )
                self.logger.info(f"Tool file_write: execution completed")
                return result
        
        if "file_diff" in enabled_tools:
            @mcp.tool(
                description="Compare two files and generate unified diff"
            )
            async def file_diff(
                left_file_path: Annotated[str, Field(
                    description="Left file workspace path (e.g., scratch/file.lean)"
                )],
                right_file_path: Annotated[str, Field(
                    description="Right file workspace path (e.g., target/path/to/file)"
                )],
                unified: Annotated[int, Field(
                    description="Context lines around changes (git diff -U)"
                )] = 3,
                ignore_space_change: Annotated[bool, Field(
                    description="Ignore whitespace changes (git diff -b)"
                )] = False,
                ignore_all_space: Annotated[bool, Field(
                    description="Ignore all whitespace (git diff -w)"
                )] = False,
                ignore_blank_lines: Annotated[bool, Field(
                    description="Ignore blank line changes"
                )] = False,
                word_diff: Annotated[bool, Field(
                    description="Word-level diff instead of line-level"
                )] = False
            ) -> Dict[str, Any]:
                """Compare two files and generate unified diff output with configurable options."""
                self.logger.info(f"Tool file_diff: execution started (left_file_path={left_file_path}, right_file_path={right_file_path})")
                result = await self.file_system.file_diff(
                    left_file_path=Path(left_file_path),
                    right_file_path=Path(right_file_path),
                    unified=unified,
                    ignore_space_change=ignore_space_change,
                    ignore_all_space=ignore_all_space,
                    ignore_blank_lines=ignore_blank_lines,
                    word_diff=word_diff
                )
                self.logger.info(f"Tool file_diff: execution completed")
                return result

        if "file_multi_edit" in enabled_tools:
            if has_confirmation:
                multi_edit_desc = """Edit file with multiple replacements OR copy file between workspaces. Use line ranges or text matching.

**EDIT MODES** (must specify at least one per edit):
- `old_line_range` only: Replace lines [start, end) (1-indexed, end exclusive). Both start/end can be None/int/negative. Examples: [None, None] = all, [None, 10] = first 9, [10, None] = from 10, [-100, None] = last 100
- `old_str` only: Find and replace text
- Both: Find old_str within line range (recommended when old_str appears multiple times)

**FILE COPY MODE**: When edits is empty or omitted AND target_path is provided, this copies the file from file_path to target_path without any modifications. This is commonly used to copy verified files from scratch workspace to target workspace.

**EDITS EXECUTION**: Applied sequentially. Line numbers are based on the original file (not updated after each edit). Multiple edits must not overlap.

**target_path**:
- With edits: applies edits to file_path and writes the result to target_path
- Without edits (empty or omitted): copies file_path to target_path without modification
- When omitted: modifies file_path in-place for writable workspaces, or creates versioned file like "file_v1.lean" for read-only workspaces

**EXECUTION**: When execute=True (default), the tool automatically runs the registered verifier or executor for that file type.

**USER CONFIRMATION**: Writing or editing files in target workspace will automatically prompt for user confirmation before applying changes.

**IMPORTANT**:
- Write actual code only - no line numbers or display markers
- edits is a LIST of DICT objects - use proper JSON formatting"""
            else:
                multi_edit_desc = """Edit file with multiple replacements OR copy file between workspaces. Use line ranges or text matching.

**EDIT MODES** (must specify at least one per edit):
- `old_line_range` only: Replace lines [start, end) (1-indexed, end exclusive). Both start/end can be None/int/negative. Examples: [None, None] = all, [None, 10] = first 9, [10, None] = from 10, [-100, None] = last 100
- `old_str` only: Find and replace text
- Both: Find old_str within line range (recommended when old_str appears multiple times)

**FILE COPY MODE**: When edits is empty or omitted AND target_path is provided, this copies the file from file_path to target_path without any modifications. This is commonly used to copy verified files from scratch workspace to target workspace.

**EDITS EXECUTION**: Applied sequentially. Line numbers are based on the original file (not updated after each edit). Multiple edits must not overlap.

**target_path**:
- With edits: applies edits to file_path and writes the result to target_path
- Without edits (empty or omitted): copies file_path to target_path without modification
- When omitted: modifies file_path in-place for writable workspaces, or creates versioned file like "file_v1.lean" for read-only workspaces

**EXECUTION**: When execute=True (default), the tool automatically runs the registered verifier or executor for that file type.

**IMPORTANT**:
- Write actual code only - no line numbers or display markers
- edits is a LIST of DICT objects - use proper JSON formatting"""

            @mcp.tool(description=multi_edit_desc)
            async def file_multi_edit(
                file_path: Annotated[str, Field(
                    description="Workspace file path (e.g., scratch/file.lean)"
                )],
                edits: Annotated[Optional[list[Dict[str, Any]]], Field(
                description='List of edit dicts. Each dict MUST have new_str plus at least one of old_line_range or old_str. old_line_range: both start/end can be None/int/negative. Examples: [{"old_line_range": [10, 21], "new_str": "replacement"}] or [{"old_line_range": [None, None], "new_str": "replace all"}] or [{"old_line_range": [-100, None], "new_str": "replace last 100"}] or [{"old_str": "find this", "new_str": "replace", "replace_all": true}]. Empty list [] with target_path copies file without modification'
            )] = None,
                target_path: Annotated[Optional[str], Field(
                    description="Optional output workspace path (creates modified copy). If omitted, edits in-place." if has_confirmation else "Optional output workspace path. If omitted, edits in-place."
                )] = None,
                execute: Annotated[bool, Field(
                    description="Auto-verify after editing"
                )] = True,
                show_modified_content: Annotated[bool, Field(
                    description="Show edited sections with context in result"
                )] = default_show_modified_content,
                context_before: Annotated[int, Field(
                    description="Context lines before each edit"
                )] = 1,
                context_after: Annotated[int, Field(
                    description="Context lines after each edit"
                )] = 1
            ) -> Dict[str, Any]:
                """Edit files with one or more replacements. Returns detailed per-edit results."""
                edits_count = len(edits) if edits else 0
                self.logger.info(f"Tool file_multi_edit: execution started (edits_count={edits_count})")
                result = await self.file_system.file_multi_edit(
                    file_path=Path(file_path),
                    edits=edits,
                    target_file_path=Path(target_path) if target_path else None,
                    execute=execute,
                    show_modified_content=show_modified_content,
                    context_lines_before=context_before,
                    context_lines_after=context_after,
                    max_context_lines=self.file_system.fs_config.performance.max_context_lines,
                    max_messages=None,
                    fuzzy_match_threshold=self.file_system.fs_config.performance.fuzzy_match_threshold,
                    fuzzy_match_ambiguity_margin=self.file_system.fs_config.performance.fuzzy_match_ambiguity_margin
                )
                self.logger.info(f"Tool file_multi_edit: execution completed")
                return result
        
        if "file_edit" in enabled_tools:
            if has_confirmation:
                simple_edit_desc = """Edit file with single replacement. Use line range or text matching.

**EDIT MODES**:
- `old_line_range` only: Replace lines [start, end) (1-indexed, end exclusive). Both start/end can be None/int/negative
- `old_str` only: Find and replace text
- Both: Find old_str within line range (avoids ambiguity)

**EXECUTION**: When execute=True (default), the tool automatically runs the registered verifier or executor for that file type.

**USER CONFIRMATION**: Editing files in target workspace will automatically prompt for user confirmation before applying changes.

**IMPORTANT**: Write actual code only - no line numbers or display markers."""
            else:
                simple_edit_desc = """Edit file with single replacement. Use line range or text matching.

**EDIT MODES**:
- `old_line_range` only: Replace lines [start, end) (1-indexed, end exclusive). Both start/end can be None/int/negative
- `old_str` only: Find and replace text
- Both: Find old_str within line range (avoids ambiguity)

**EXECUTION**: When execute=True (default), the tool automatically runs the registered verifier or executor for that file type.

**IMPORTANT**: Write actual code only - no line numbers or display markers."""

            @mcp.tool(description=simple_edit_desc)
            async def file_edit(
                file_path: Annotated[str, Field(
                    description="Workspace file path (e.g., scratch/file.lean)"
                )],
                new_str: Annotated[str, Field(
                    description="Replacement text (actual code only, no line numbers or markers)"
                )],
                old_str: Annotated[Optional[str], Field(
                    description="Text to find and replace (optional)"
                )] = None,
                old_line_range: Annotated[Optional[list], Field(
                    description="Line range [start, end) to replace. Both can be None/int/negative. Examples: [None, None] = all, [10, None] = from 10, [-100, None] = last 100"
                )] = None,
                replace_all: Annotated[bool, Field(
                    description="Replace all matches of old_str"
                )] = False,
                target_path: Annotated[Optional[str], Field(
                    description="Optional output workspace path (creates modified copy). If omitted, edits in-place." if has_confirmation else "Optional output workspace path. If omitted, edits in-place."
                )] = None,
                execute: Annotated[bool, Field(
                    description="Auto-verify after editing"
                )] = True,
                show_modified_content: Annotated[bool, Field(
                    description="Show edited sections with context in result"
                )] = default_show_modified_content,
                context_before: Annotated[int, Field(
                    description="Context lines before edit"
                )] = 1,
                context_after: Annotated[int, Field(
                    description="Context lines after edit"
                )] = 1
            ) -> Dict[str, Any]:
                """Edit file with single change using flat parameters. Returns detailed result."""
                self.logger.info(f"Tool file_edit: execution started (file_path={file_path})")
                result = await self.file_system.file_edit(
                    file_path=Path(file_path),
                    new_str=new_str,
                    old_str=old_str,
                    old_line_range=old_line_range,
                    replace_all=replace_all,
                    target_file_path=Path(target_path) if target_path else None,
                    execute=execute,
                    show_modified_content=show_modified_content,
                    context_lines_before=context_before,
                    context_lines_after=context_after,
                    max_context_lines=self.file_system.fs_config.performance.max_context_lines,
                    max_messages=None,
                    fuzzy_match_threshold=self.file_system.fs_config.performance.fuzzy_match_threshold,
                    fuzzy_match_ambiguity_margin=self.file_system.fs_config.performance.fuzzy_match_ambiguity_margin
                )
                self.logger.info(f"Tool file_edit: execution completed")
                return result
            
        if "extract_pdf_text" in enabled_tools:
            @mcp.tool(
                description="""Extract text content from PDF file and save to output file.

**OUTPUT**: Returns previews of start/end of extracted text along with metadata.

**MODES**:
- "text": Plain text extraction (default, uses get_text("text", sort=True))
- "dict": Structured JSON extraction (uses get_text("dict"))

**USE CASE**: Use this tool to inspect PDF content quality before evaluation."""
            )
            async def extract_pdf_text(
                pdf_path: Annotated[str, Field(
                    description="Workspace PDF file path (e.g., scratch/paper.pdf)"
                )],
                output_path: Annotated[str, Field(
                    description="Workspace output file path (e.g., scratch/paper_text.txt or scratch/paper_data.json)"
                )],
                extraction_mode: Annotated[str, Field(
                    description="Extraction mode: 'text' for plain text, 'dict' for structured JSON"
                )] = "text",
                sort_text: Annotated[bool, Field(
                    description="Sort text by position (only for text mode)"
                )] = True
            ) -> Dict[str, Any]:
                """Extract text from PDF file and save to output file."""
                self.logger.info(f"Tool extract_pdf_text: execution started (pdf_path={pdf_path})")
                result = await self.file_system.extract_pdf_text(
                    pdf_path=Path(pdf_path),
                    output_path=Path(output_path),
                    extraction_mode=extraction_mode,
                    sort_text=sort_text
                )
                self.logger.info(f"Tool extract_pdf_text: execution completed")
                return result


# Automatically register all supported tools
from ape.toolkits.registry import register_tool
register_tool(FileSystemToolsProvider)
