"""
File System Provider - File system operation tools (Simplified Core Version)

Uses explicit workspace parameter design, reference LeanVerifyTool mode:
- Specify workspace through tool parameters
- Use Path objects for consistent system design
- Use language layer unified mechanism to avoid duplicate design
- Abstract specific calculation mechanisms to tool functions and move to utils
- Use asynchronous IO to avoid blocking event loop
- Permission control is handled entirely at runtime layer (not in file system tools)
"""

import asyncio
import aiofiles
import fnmatch
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from ape.utils.logging import create_logger
from .utils import (
    generate_unified_diff, generate_word_diff, search_content_with_timeout,
    add_line_numbers, resolve_search_paths, calculate_relative_path,
    validate_file_exists_and_is_file,
    check_file_size_limit, read_file_content_safe, apply_line_range_to_content,
    get_default_config_values,
    apply_whitespace_processing,
    format_content_display, generate_modified_content_display,
    process_single_edit, apply_position_edits_to_content,
    open_file_in_vscode, extract_pdf_text_to_file
)

if TYPE_CHECKING:
    from ape.tasks.models import WorkspaceInfo
    from ape.tasks.base import BaseTask
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class FileSystemProvider:
    """
    File system operation provider (simplified core version)
    
    Uses explicit workspace parameter design, reference LeanVerifyTool mode:
    - scratch_workspace: fully read-write
    - target_workspace: control access through parameters
    - Use Path objects for consistent system design
    - Use language layer unified mechanism to avoid duplicate design
    - Delegate specific calculation mechanisms to utils tool functions
    """
    
    def __init__(self,
                 task: "BaseTask",
                 config: "BaseScaffoldConfig",
                 logger: Optional['logging.LoggerAdapter'] = None,
                 confirmation_bridge=None,
                 is_cli_mode: bool = False):
        """Initialize file system provider.

        Args:
            task: Task instance containing workspaces info
            config: Scaffold configuration (BaseScaffoldConfig)
            logger: Logger instance
            confirmation_bridge: Confirmation bridge for CLI mode
            is_cli_mode: Whether in CLI mode
        """
        from ape.scaffolds.config import BaseScaffoldConfig

        self.task = task
        self.scaffold_config = config
        self.logger = logger or create_logger()
        self.confirmation_bridge = confirmation_bridge
        self.is_cli_mode = is_cli_mode
        self.tool_instances: Dict[type, Any] = {}

        # Extract file system specific config
        self.fs_config = config.tools_config.file_system
        self.open_in_vscode = config.open_in_vscode

        # Store workspaces_dir - the only path we need for resolution
        self.workspaces_dir = task.workspaces_dir.resolve()

        # Ensure workspaces_dir exists
        if not self.workspaces_dir.exists():
            raise FileNotFoundError(f"Workspaces directory does not exist: {self.workspaces_dir}")

        self.logger.info(f"FileSystemProvider initialized")
        self.logger.info(f"  Workspaces directory: {self.workspaces_dir}")
        self.logger.info(f"  CLI mode: {is_cli_mode}")
    
    def _get_language_provider(self, file_path: Path):
        """Get language provider for file extension through code provider."""
        from ape.toolkits.code.base_provider import BaseCodeToolsProvider
        
        if not self.tool_instances:
            return None
            
        for provider_class, provider_instance in self.tool_instances.items():
            if isinstance(provider_instance, BaseCodeToolsProvider):
                try:
                    return provider_instance._route_to_provider(file_path)
                except ValueError:
                    return None
        return None

    def _get_executor(self, file_path: Path):
        """Get executor for file extension from shared tool instances.

        Uses registry to find executor class, then retrieves shared instance.
        If instance not found in tool_instances, constructs a new one using scaffold config.
        """
        from ape.toolkits.registry import get_executor_class
        ext = file_path.suffix
        executor_class = get_executor_class(ext)
        if not executor_class:
            return None

        # Try to get from shared tool instances first
        executor_instance = self.tool_instances.get(executor_class)
        if executor_instance:
            return executor_instance

        # If not found, construct new instance using scaffold config
        self.logger.info(f"Executor {executor_class.__name__} not found in tool_instances, constructing new instance")
        try:
            executor_instance = executor_class(
                task=self.task,
                config=self.scaffold_config,
                logger=self.logger,
                confirmation_bridge=self.confirmation_bridge,
                is_cli_mode=self.is_cli_mode,
            )
            # Store in tool_instances for reuse
            self.tool_instances[executor_class] = executor_instance
            return executor_instance
        except Exception as e:
            self.logger.error(f"Failed to construct executor {executor_class.__name__}: {e}")
            return None

    def _resolve_path(self, file_path: Path) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Resolve file path relative to workspaces_dir with security check.

        Args:
            file_path: Path relative to workspaces_dir (e.g., 'scratch/file.lean', 'target/Data.lean')

        Returns:
            Tuple[success, resolved_path, error_msg]:
            - success: Whether resolution succeeded
            - resolved_path: Absolute resolved path, None if failed
            - error_msg: Error message, None if successful

        Note:
            This method does NOT check if the path exists. Existence checks should be
            performed by the calling operation as needed (e.g., read requires existence,
            write allows creating new files).

        Security:
            - Rejects absolute paths (which would escape workspaces_dir)
            - Rejects paths with ".." (path traversal attack)
            - After these checks, resolves to handle symlinks (workspaces can be symlinks)
        """
        try:
            # Security check 1: Reject absolute paths
            # Path("/etc/passwd") would replace workspaces_dir instead of joining
            if file_path.is_absolute():
                return False, None, f"Absolute paths are not allowed: {file_path}"

            # Security check 2: Reject parent directory references
            # Prevents "scratch/../../etc/passwd" attacks
            if '..' in file_path.parts:
                return False, None, f"Parent directory references (..) are not allowed: {file_path}"

            # Safe to join and resolve (workspaces can be symlinks, that's OK)
            resolved = (self.workspaces_dir / file_path).resolve()

            return True, resolved, None

        except Exception as e:
            return False, None, f"Failed to resolve path '{file_path}': {e}"
    
    # ===== Core file operation methods =====
    
    async def file_read(self,
                       file_path: Path,
                       line_range: Optional[List] = None,
                       omit_details: bool = True) -> Dict[str, Any]:
        """
        Read file content

        Args:
            file_path: File path with workspace prefix:
                      - Path("scratch/file.lean") - file in scratch workspace
                      - Path("target/Data/Nat.lean") - file in target workspace
                      - Path("reference/mathlib/Mathlib/Data.lean") - file in reference workspace
            line_range: Optional line range [start, end) using 1-indexed Python-style slicing (end exclusive).
                       Both start and end support negative indices and None. Examples: [None, None] = all, [None, 10] = first 9, [10, None] = from 10.
            omit_details: Whether to omit detailed content (default True), omit proof blocks for .lean files, omit function bodies for .py files

        Returns:
            Operation result dictionary, content field contains formatted content with line numbers (LINE_NUMBER|LINE_CONTENT)
        """
        try:
            # Resolve path
            success, resolved_path, error_msg = self._resolve_path(file_path)
            if not success:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate file exists and is a file
            validation_error = validate_file_exists_and_is_file(resolved_path, file_path)
            if validation_error:
                return validation_error

            # Check file size limit
            max_size = self.fs_config.performance.max_file_size_for_reading
            size_error = check_file_size_limit(resolved_path, max_size, file_path)
            if size_error:
                return size_error

            # Read file content (asynchronous, avoid blocking)
            success, content_or_error, error_type = await read_file_content_safe(resolved_path, file_path)
            if not success:
                return {
                    "success": False,
                    "error": content_or_error
                }

            content = content_or_error

            # Use language provider for formatting if available
            try:
                lang_provider = self._get_language_provider(resolved_path)
                if lang_provider:
                    line_spans = None
                    if line_range:
                        # Normalize line range (handles negative indices and None)
                        from .utils import normalize_line_range
                        lines = content.splitlines()
                        total_lines = len(lines)
                        start_line, end_line = normalize_line_range(line_range, total_lines)
                        end_inclusive = end_line - 1
                        if end_inclusive >= start_line:
                            line_spans = [(start_line, end_inclusive)]
                    display_mode = "line_spans" if line_spans else "full"

                    content_with_line_numbers = await asyncio.to_thread(
                        lang_provider.display_content,
                        content,
                        display_mode=display_mode,
                        line_spans=line_spans,
                        add_line_numbers=True,
                        omit_details=omit_details
                    )
                else:
                    content_with_line_numbers = apply_line_range_to_content(content, line_range, with_line_numbers=True)
            except Exception as e:
                self.logger.warning(f"Failed to format content from {file_path}: {e}")
                content_with_line_numbers = add_line_numbers(content)
            
            return {
                "success": True,
                "content": content_with_line_numbers
            }
            
        except Exception as e:
            self.logger.error(f"Error reading file: {traceback.format_exc()}")
            return {"success": False, "error": f"File read error: {traceback.format_exc()}"}
    
    async def content_search(self,
                            content_pattern: str,
                            search_path: Path,
                            recursive: bool = True,
                            max_results: Optional[int] = None,
                            max_matches_per_file: Optional[int] = None,
                            timeout: Optional[float] = None,
                            use_regex: bool = True,
                            A: Optional[int] = None,
                            B: Optional[int] = None,
                            C: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for specified pattern in file content

        Args:
            content_pattern: File content search pattern (required, supports regular expressions)
            search_path: Path relative to workspaces_dir (e.g., 'scratch/', 'target/Data', supports file/directory/glob)
            recursive: Whether to search recursively (only effective when path is a directory)
            max_results: Maximum number of files to return
            max_matches_per_file: Maximum number of matches per file
            timeout: Timeout for single file regular matching (seconds)
            use_regex: Whether to use regular expression matching (default True, False uses simple string inclusion)
            A: Number of lines after matching line (similar to grep -A)
            B: Number of lines before matching line (similar to grep -B)
            C: Number of lines before and after matching line (similar to grep -C, will override A and B)

        Returns:
            Operation result dictionary, results field contains relative path strings
        """
        try:
            # Use configured default values
            if max_results is None or timeout is None:
                default_max_results, default_timeout = get_default_config_values(self.fs_config)
                if max_results is None:
                    max_results = default_max_results
                if timeout is None:
                    timeout = default_timeout

            # Parse search path relative to workspaces_dir
            files_to_search = await asyncio.to_thread(
                resolve_search_paths,
                search_path,
                self.workspaces_dir,
                recursive,
                self.logger
            )
            
            if not files_to_search:
                return {
                    "success": False,
                    "error": f"No files found for path: {search_path}"
                }
            
            results = []
            count = 0
            
            for file_path in files_to_search:
                if count >= max_results:
                    break
                
                
                # Check file size limit
                max_size = self.fs_config.performance.max_file_size_for_content_search
                if max_size and check_file_size_limit(file_path, max_size, file_path):
                    self.logger.debug(f"Skipping file due to size limit: {file_path}")
                    continue
                
                try:
                    # Asynchronously read file content, avoid blocking event loop
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                    
                    # Apply content matching (using functions in utils, possibly CPU intensive regular matching, moved to thread pool)
                    # Use asyncio.wait_for to control timeout
                    try:
                        matches = await asyncio.wait_for(
                            asyncio.to_thread(
                                search_content_with_timeout,
                                content, content_pattern, use_regex, timeout, A, B, C, max_matches_per_file, self.logger
                            ),
                            timeout=timeout
                        )
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Content search timeout for file: {file_path}")
                        continue
                    
                    if not matches:
                        continue
                        
                except (UnicodeDecodeError, OSError):
                    continue

                # Calculate relative path from workspaces_dir
                relative_path = calculate_relative_path(file_path, self.workspaces_dir)

                results.append({
                    "path": str(relative_path),
                    "matches": matches
                })
                count += 1
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching file content: {traceback.format_exc()}")
            return {"success": False, "error": f"Content search error: {traceback.format_exc()}"}
    
    async def file_search(self,
                         pattern: str,
                         directory_path: Path,
                         recursive: bool = True,
                         max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Search files by pattern (glob operation)

        Args:
            pattern: File name pattern (required, e.g. "*.lean", "*Nat*")
            directory_path: Directory path relative to workspaces_dir (e.g., 'scratch/', 'target/Data')
            recursive: Whether to search recursively
            max_results: Maximum number of results

        Returns:
            Operation result dictionary, results field contains relative path strings
        """
        try:
            # Use configured default values
            if max_results is None:
                max_results, _ = get_default_config_values(self.fs_config)

            # Resolve path
            success, resolved_path, error_msg = self._resolve_path(directory_path)
            if not success:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate directory exists and is a directory
            if not resolved_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}"
                }

            if not resolved_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory_path}"
                }
            
            results = []
            count = 0
            
            # File traversal
            if recursive:
                file_iter = resolved_path.rglob('*')
            else:
                file_iter = resolved_path.iterdir()
            
            for file_path in file_iter:
                if count >= max_results:
                    break
                
                if not file_path.is_file():
                    continue
                
                
                # Apply file name pattern filtering (required)
                # Convert file path to relative path for matching
                try:
                    relative_file = file_path.relative_to(self.workspaces_dir)
                    relative_str = relative_file.as_posix()
                except ValueError:
                    # File not in workspace, skip
                    continue

                # Use fnmatch for glob pattern matching
                if not fnmatch.fnmatch(relative_str, pattern):
                    continue

                # Add to results (calculate relative path from workspaces_dir)
                relative_path = calculate_relative_path(file_path, self.workspaces_dir)

                results.append({
                    "path": str(relative_path)
                })
                count += 1
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching files by pattern: {traceback.format_exc()}")
            return {"success": False, "error": f"File pattern search error: {traceback.format_exc()}"}
    
    async def file_write(self,
                        file_path: Path,
                        content: str,
                        execute: bool = True,
                        show_content: bool = True,
                        context_lines: int = 10,
                        max_messages: Optional[int] = None) -> Dict[str, Any]:
        """
        Write full file content (create or overwrite)

        Args:
            file_path: File path with workspace prefix (e.g., 'scratch/solution.lean', 'target/file.lean')
            content: Full file content
            execute: Whether to execute file verification/execution (default True)
            show_content: Whether to show written content in results (default True)
            context_lines: Number of lines to display when content is long (default 10)
            max_messages: Verification message limit (only effective when execute=True)

        Returns:
            Operation result dictionary
        """
        try:
            # Resolve path
            success, resolved_path, error_msg = self._resolve_path(file_path)
            if not success:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Auto-detect and remove line numbers from content
            from .utils import detect_and_remove_line_numbers
            cleaned_content, had_line_numbers, line_number_warning = detect_and_remove_line_numbers(content)
            if had_line_numbers:
                content = cleaned_content
                # We'll add the warning to the result later

            # Record whether overwritten
            existed = resolved_path.exists()

            # Create directory
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Asynchronously write file (avoid blocking event loop)
            async with aiofiles.open(resolved_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            # Build clear operation description
            if existed:
                operation_message = f"Overwrote '{file_path}'"
            else:
                operation_message = f"Created '{file_path}'"

            # Build result
            result = {
                "success": True,
                "message": operation_message,
            }

            # Add warning if line numbers were detected and removed
            if had_line_numbers:
                result["warning"] = line_number_warning

            # Execute verification if executor available
            if execute:
                executor = self._get_executor(resolved_path)
                if executor:
                    execution_result = await executor.execute(
                        code=content,
                        file_path=file_path,
                        max_messages=max_messages,
                    )
                    result["execution_result"] = execution_result

            # Optional: show content (CPU intensive text formatting, moved to thread pool)
            if show_content:
                lang_provider = self._get_language_provider(resolved_path)
                # Get language-specific omission marker
                if lang_provider and hasattr(lang_provider, 'get_omission_marker'):
                    omission_marker = lang_provider.get_omission_marker("... omitted lines ...")
                else:
                    omission_marker = "# ... omitted lines ..."
                result["written_content"] = await asyncio.to_thread(
                    format_content_display,
                    content, omission_marker, max_lines=context_lines
                )

            # CLI mode: open file in VS Code
            if self.is_cli_mode:
                open_file_in_vscode(resolved_path, enabled=self.open_in_vscode, logger=self.logger)

            return result
            
        except Exception as e:
            # Special handling: system-level exceptions and user interrupt, should be propagated
            # 1. KeyboardInterrupt and EOFError: user requests to exit system
            if isinstance(e, (KeyboardInterrupt, EOFError)):
                raise

            # 2. UserDeclinedConfirmation: user refused confirmation
            from ape.scaffolds.ape_agent.cli.ui.confirmation import UserDeclinedConfirmation
            if isinstance(e, UserDeclinedConfirmation):
                raise  # Re-throw, let conversation manager handle it

            # Other exceptions: record and return error
            self.logger.error(f"Error writing file '{file_path}': {traceback.format_exc()}")
            return {"success": False, "error": f"File write error: {traceback.format_exc()}"}
    
    
    async def file_multi_edit(self,
                       file_path: Path,
                       edits: Optional[List[Dict[str, Any]]] = None,
                       target_file_path: Optional[Path] = None,
                       execute: bool = True,
                       show_modified_content: Optional[bool] = None,
                       context_lines_before: int = 1,
                       context_lines_after: int = 1,
                       max_context_lines: Optional[int] = 10,
                       max_messages: Optional[int] = None,
                       fuzzy_match_threshold: float = 0.85,
                       fuzzy_match_ambiguity_margin: float = 0.05) -> Dict[str, Any]:
        """
        Execute edit operations on file (supports single or multiple edits, atomic, supports derived new files)

        Args:
            file_path: Source file path with workspace prefix (e.g., 'scratch/file.lean', 'target/Data.lean')
            edits: Edit operation list, each operation contains:
                - old_str: String to replace (use old_line_range or combine with old_str)
                - new_str: Replacement string (required)
                - old_line_range: Line range [start, end) using 1-indexed Python-style slicing (end exclusive).
                               Both start and end support negative indices and None (e.g., [None, None] = all, [-100, None] = last 100)
                - replace_all: Whether to replace all matches (optional, default False, only effective when using old_str)
            target_file_path: Target file path with workspace prefix (optional). If provided, will create new file instead of modifying original file
            execute: Whether to execute file verification/execution (default True), skip execution if False to avoid unexpected execution
            show_modified_content: Whether to show modified file content in results (default from config)
            context_lines_before: Number of lines to display before modified content (default 1)
            context_lines_after: Number of lines to display after modified content (default 1)
            max_context_lines: When modifications exceed this value, collapse the middle and evenly divide context before/after (default 10)
            max_messages: Verification message limit (only effective when execute=True)

        Behavior:
            - If target_file_path is provided: create new file (derived mode)
            - If target_file_path is not provided: try in-place edit
            - If original file is read-only and target_file_path is not provided: automatically generate new file name with version number

        Returns:
            Operation result dictionary, contains:
            - success: Whether successful
            - path: Actual operation file path (relative path string)
            - source_path: Source file path (only in derived mode)
            - derived: Whether to derive operation (only in derived mode)
            - edit_results: Detailed results of each edit
            - modified_content: Modified content (only when show_modified_content=True)
        """
        try:
            if show_modified_content is None:
                show_modified_content = self.fs_config.show_modified_content
            # Standardize edits parameter: None and [] are equivalent
            if edits is None:
                edits = []

            # Resolve source file path
            success, source_resolved_path, error_msg = self._resolve_path(file_path)
            if not success:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate source file exists and is a file
            validation_error = validate_file_exists_and_is_file(source_resolved_path, file_path)
            if validation_error:
                return validation_error

            # Read source file content
            success, original_content, error_type = await read_file_content_safe(source_resolved_path, file_path)
            if not success:
                return {
                    "success": False,
                    "error": original_content
                }
            
            # First step: independently validate each edit and convert to character position operations (based on original content)
            edit_results = []  # Store detailed results of each edit
            position_edits = []  # [(start_pos, end_pos, new_str, original_edit_index, edit_result)]
            
            for i, edit in enumerate(edits):
                # Use functions in utils to process single edit (CPU-intensive string matching, moved to thread pool)
                edit_result, single_position_edits = await asyncio.to_thread(
                    process_single_edit,
                    edit, original_content, i,
                    fuzzy_threshold=fuzzy_match_threshold,
                    ambiguity_margin=fuzzy_match_ambiguity_margin,
                    enable_fuzzy_matching=self.fs_config.performance.enable_fuzzy_matching
                )
                edit_results.append(edit_result)
                
                # Add successful edit positions to list
                if edit_result["success"]:
                    for start_pos, end_pos, new_str in single_position_edits:
                        position_edits.append((start_pos, end_pos, new_str, i, edit_result))
            
            # If all edits fail, return directly (unless original edits are empty and target_file_path is provided, i.e. file copy mode)
            if not position_edits and edits:
                return {
                    "success": False,
                    "error": "All edits failed validation",
                    "edit_results": edit_results,
                    "summary": {
                        "total_edits": len(edits),
                        "successful_edits": 0,
                        "failed_edits": len(edits)
                    }
                }
            
            # Second step: detect overlap (strict exclusion principle) - only detect successful edits
            # Sort by start position to detect overlap
            position_edits.sort(key=lambda x: x[0])
            for i in range(len(position_edits) - 1):
                curr_start, curr_end, _, curr_idx, curr_result = position_edits[i]
                next_start, next_end, _, next_idx, next_result = position_edits[i + 1]
                if curr_end > next_start:
                    # Mark overlapping edits as failed
                    overlap_error = f"Overlaps with edit #{next_idx+1} at position [{next_start}:{next_end}]"
                    curr_result["success"] = False
                    curr_result["error"] = overlap_error
                    next_result["success"] = False
                    next_result["error"] = f"Overlaps with edit #{curr_idx+1} at position [{curr_start}:{curr_end}]"
            
            # Filter out failed edits with overlap
            position_edits = [e for e in position_edits if e[4]["success"]]
            
            if not position_edits and edits:
                successful_count = sum(1 for r in edit_results if r["success"])
                failed_count = len(edit_results) - successful_count
                return {
                    "success": False,
                    "error": "All edits failed due to overlapping regions",
                    "edit_results": edit_results,
                    "summary": {
                        "total_edits": len(edits),
                        "successful_edits": successful_count,
                        "failed_edits": failed_count
                    }
                }
            
            # Third step: sort by position in descending order (apply from back to front)
            position_edits.sort(key=lambda x: -x[0])
            
            # Fourth step: apply all successful edits in order by position, and record detailed information
            # Use functions in utils to apply edits (CPU-intensive string operations, moved to thread pool)
            current_content, _ = await asyncio.to_thread(
                apply_position_edits_to_content, original_content, position_edits
            )
            
            # Determine target file path
            is_derived = False
            if target_file_path:
                # User explicitly provides target path
                success, target_resolved_path, error_msg = self._resolve_path(target_file_path)
                if not success:
                    return {
                        "success": False,
                        "error": f"target_file_path: {error_msg}"
                    }

                is_derived = True
            else:
                # Source file in-place edit

                target_resolved_path = source_resolved_path
                target_file_path = file_path

            
            # Create parent directory of target file
            target_resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # All edits can be successfully executed, now asynchronously write to target file (avoid blocking)
            async with aiofiles.open(target_resolved_path, 'w', encoding='utf-8') as f:
                await f.write(current_content)
            
            # Count successful and failed edits
            successful_edits = sum(1 for r in edit_results if r["success"])
            failed_edits = len(edit_results) - successful_edits

            # Build clear operation description
            if is_derived:
                if len(edits) == 0:
                    operation_message = f"Copied '{file_path}' → '{target_file_path}' (no edits)"
                else:
                    operation_message = f"Edited '{file_path}' → '{target_file_path}' ({successful_edits}/{len(edits)} edits succeeded)"
            else:
                operation_message = f"Edited '{target_file_path}' in-place ({successful_edits}/{len(edits)} edits succeeded)"

            # Build result
            result = {
                "success": True,
                "message": operation_message,
                "edit_results": edit_results
            }

            # Execute verification if executor available
            if execute:
                executor = self._get_executor(target_resolved_path)
                if executor:
                    execution_result = await executor.execute(
                        code=current_content,
                        file_path=target_file_path,
                        max_messages=max_messages,
                    )
                    result["execution_result"] = execution_result

            # If need to show modified content, generate content display with context (CPU-intensive text formatting, moved to thread pool)
            if show_modified_content and successful_edits > 0:
                lang_provider = self._get_language_provider(target_resolved_path)
                # Get language-specific omission marker
                if lang_provider and hasattr(lang_provider, 'get_omission_marker'):
                    omission_marker = lang_provider.get_omission_marker("... omitted lines ...")
                else:
                    omission_marker = "# ... omitted lines ..."
                result["modified_content"] = await asyncio.to_thread(
                    generate_modified_content_display,
                    current_content=current_content,
                    edit_results=[r for r in edit_results if r["success"]],
                    omission_marker=omission_marker,
                    context_lines_before=context_lines_before,
                    context_lines_after=context_lines_after,
                    max_context_lines=max_context_lines
                )

            # CLI mode: open file in VS Code, jump to the first successful edit position
            if self.is_cli_mode:
                if successful_edits > 0:
                    # Find the first successful edit, get the starting line number of its new line range
                    first_success = next((r for r in edit_results if r["success"]), None)
                    if first_success and first_success.get("new_line_range"):
                        # new_line_range is [start, end], take the starting line
                        line_number = first_success["new_line_range"][0]
                        open_file_in_vscode(target_resolved_path, line=line_number, enabled=self.open_in_vscode, logger=self.logger)
                    else:
                        open_file_in_vscode(target_resolved_path, enabled=self.open_in_vscode, logger=self.logger)
                else:
                    # No successful edit, only open file
                    open_file_in_vscode(target_resolved_path, enabled=self.open_in_vscode, logger=self.logger)

            return result
            
        except Exception as e:
            # Special handling: system-level exceptions and user interrupt, should be propagated
            # 1. KeyboardInterrupt and EOFError: user requested exit system
            if isinstance(e, (KeyboardInterrupt, EOFError)):
                raise

            # 2. UserDeclinedConfirmation: user declined confirmation
            from ape.scaffolds.ape_agent.cli.ui.confirmation import UserDeclinedConfirmation
            if isinstance(e, UserDeclinedConfirmation):
                raise  # Re-throw, let conversation manager handle it

            # Other exceptions: record and return error
            self.logger.error(f"Error editing file '{file_path}': {traceback.format_exc()}")
            return {"success": False, "error": f"File multi-edit error: {traceback.format_exc()}"}
    
    async def file_edit(self,
                       file_path: Path,
                       new_str: str,
                       old_str: Optional[str] = None,
                       old_line_range: Optional[List] = None,
                       replace_all: bool = False,
                       target_file_path: Optional[Path] = None,
                       execute: bool = True,
                       show_modified_content: Optional[bool] = None,
                       context_lines_before: int = 1,
                       context_lines_after: int = 1,
                       max_context_lines: Optional[int] = 10,
                       max_messages: Optional[int] = None,
                       fuzzy_match_threshold: float = 0.85,
                       fuzzy_match_ambiguity_margin: float = 0.05) -> Dict[str, Any]:
        """
        Execute single edit operation on file (flat parameter version of file_multi_edit)

        Args:
            file_path: Source file path with workspace prefix (e.g., 'scratch/file.lean', 'target/Data.lean')
            new_str: Replacement string (required)
            old_str: String to replace (use old_line_range or combine with old_str)
            old_line_range: Line range [start, end) using 1-indexed Python-style slicing (end exclusive).
                           Both start and end support negative indices and None
            replace_all: Whether to replace all matches (optional, default False, only effective when using old_str)
            target_file_path: Target file path with workspace prefix (optional). If provided, will create new file instead of modifying original file
            execute: Whether to execute file verification/execution (default True), skip execution if False to avoid unexpected execution
            show_modified_content: Whether to show modified file content in results (default from config)
            context_lines_before: Number of lines to display before modified content (default 1)
            context_lines_after: Number of lines to display after modified content (default 1)
            max_context_lines: When modifications exceed this value, collapse the middle and evenly divide context before/after (default 10)
            max_messages: Verification message limit (only effective when execute=True)
            fuzzy_match_threshold: Fuzzy match similarity threshold (0.0-1.0, default 0.85)
            fuzzy_match_ambiguity_margin: Fuzzy match ambiguity margin (default 0.05)

        Returns:
            Operation result dictionary, contains:
            - success: Whether successful
            - path: Actual operation file path (relative path string)
            - source_path: Source file path (only in derived mode)
            - derived: Whether to derive operation (only in derived mode)
            - edit_results: Detailed results of each edit
            - modified_content: Modified content (only when show_modified_content=True)
        """
        if show_modified_content is None:
            show_modified_content = self.fs_config.show_modified_content
        # Build single edit dictionary
        edit = {
            "new_str": new_str
        }
        
        if old_str is not None:
            edit["old_str"] = old_str
        
        if old_line_range is not None:
            edit["old_line_range"] = old_line_range
        
        if replace_all:
            edit["replace_all"] = replace_all
        
        # Call file_multi_edit
        return await self.file_multi_edit(
            file_path=file_path,
            edits=[edit],
            target_file_path=target_file_path,
            execute=execute,
            show_modified_content=show_modified_content,
            context_lines_before=context_lines_before,
            context_lines_after=context_lines_after,
            max_context_lines=max_context_lines,
            max_messages=max_messages,
            fuzzy_match_threshold=fuzzy_match_threshold,
            fuzzy_match_ambiguity_margin=fuzzy_match_ambiguity_margin
        )
    
    async def file_diff(self,
                       left_file_path: Path,
                       right_file_path: Path,
                       unified: int = 3,
                       ignore_space_change: bool = False,
                       ignore_all_space: bool = False,
                       ignore_blank_lines: bool = False,
                       word_diff: bool = False) -> Dict[str, Any]:
        """
        Compare two files and generate unified difference format

        Args:
            left_file_path: Left file path with workspace prefix (e.g., 'scratch/file.lean', 'target/Data.lean')
            right_file_path: Right file path with workspace prefix (e.g., 'scratch/file.lean', 'target/Data.lean')
            unified: Context lines (similar to git diff -U)
            ignore_space_change: Ignore space change
            ignore_all_space: Ignore all space difference
            ignore_blank_lines: Ignore blank line addition and deletion
            word_diff: Generate word level difference rather than line level difference

        Returns:
            Operation result dictionary, contains diff content
        """
        try:
            # Resolve left file path
            success, left_resolved_path, error_msg = self._resolve_path(left_file_path)
            if not success:
                return {
                    "success": False,
                    "error": f"left_file_path: {error_msg}"
                }

            # Resolve right file path
            success, right_resolved_path, error_msg = self._resolve_path(right_file_path)
            if not success:
                return {
                    "success": False,
                    "error": f"right_file_path: {error_msg}"
                }


            # Validate file exists and is file
            left_validation_error = validate_file_exists_and_is_file(left_resolved_path, left_file_path)
            if left_validation_error:
                return {
                    "success": False,
                    "error": f"Left file not found: {left_file_path}"
                }

            right_validation_error = validate_file_exists_and_is_file(right_resolved_path, right_file_path)
            if right_validation_error:
                return {
                    "success": False,
                    "error": f"Right file not found: {right_file_path}"
                }

            # Read file content (asynchronously, to avoid blocking)
            left_success, left_content, left_error_type = await read_file_content_safe(left_resolved_path, left_file_path)
            if not left_success:
                return {
                    "success": False,
                    "error": f"Cannot read left file as text: {left_file_path}"
                }

            right_success, right_content, right_error_type = await read_file_content_safe(right_resolved_path, right_file_path)
            if not right_success:
                return {
                    "success": False,
                    "error": f"Cannot read right file as text: {right_file_path}"
                }

            # Optional whitespace processing - use utils tool functions
            left_processed = apply_whitespace_processing(left_content, ignore_all_space, ignore_space_change, ignore_blank_lines)
            right_processed = apply_whitespace_processing(right_content, ignore_all_space, ignore_space_change, ignore_blank_lines)

            # Generate difference - use functions in utils (CPU-intensive text processing, moved to thread pool)
            if word_diff:
                diff_result = await asyncio.to_thread(
                    generate_word_diff,
                    left_processed, right_processed, left_file_path, right_file_path
                )
            else:
                diff_result = await asyncio.to_thread(
                    generate_unified_diff,
                    left_processed, right_processed, left_file_path, right_file_path, unified
                )
            
            return {
                "success": True,
                "diff": diff_result
            }
            
        except Exception as e:
            self.logger.error(f"Error generating file diff: {traceback.format_exc()}")
            return {"success": False, "error": f"File diff error: {traceback.format_exc()}"}
    
    async def extract_pdf_text(self,
                              pdf_path: Path,
                              output_path: Path,
                              extraction_mode: str = "text",
                              sort_text: bool = True) -> Dict[str, Any]:
        """
        Extract text content from PDF file and save to output file.

        Args:
            pdf_path: PDF file path with workspace prefix (e.g., 'scratch/paper.pdf')
            output_path: Output file path with workspace prefix (e.g., 'scratch/paper_text.txt')
            extraction_mode: Extraction mode - "text" for plain text, "dict" for structured JSON
            sort_text: Whether to sort text by position (only for text mode, default True)

        Returns:
            Operation result dictionary containing previews and metadata
        """
        try:
            # Resolve PDF path
            success, pdf_resolved_path, error_msg = self._resolve_path(pdf_path)
            if not success:
                return {
                    "success": False,
                    "error": f"pdf_path: {error_msg}"
                }

            # Validate PDF exists and is a file
            validation_error = validate_file_exists_and_is_file(pdf_resolved_path, pdf_path)
            if validation_error:
                return validation_error

            # Resolve output path
            success, output_resolved_path, error_msg = self._resolve_path(output_path)
            if not success:
                return {
                    "success": False,
                    "error": f"output_path: {error_msg}"
                }

            # Create output directory
            output_resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract text using utility function
            result = await extract_pdf_text_to_file(
                pdf_path=pdf_resolved_path,
                output_path=output_resolved_path,
                extraction_mode=extraction_mode,
                sort_text=sort_text,
                logger=self.logger
            )

            if not result["success"]:
                return result

            # Add relative paths to result
            result["pdf_path"] = str(pdf_path)
            result["output_path"] = str(output_path)

            return result

        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {traceback.format_exc()}")
            return {"success": False, "error": f"PDF text extraction error: {traceback.format_exc()}"}
