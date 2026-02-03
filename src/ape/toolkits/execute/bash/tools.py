"""Bash Execute Tool - Simple subprocess-based execution."""

import asyncio
import tempfile
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING, Annotated
from pathlib import Path
from fastmcp import FastMCP
from pydantic import Field
import aiofiles

from ape.utils.logging import create_logger
from ape.toolkits.execute.base import BaseExecuteToolsProvider
from .config import BashExecuteToolConfig

if TYPE_CHECKING:
    import logging
    from ape.tasks.models import WorkspaceInfo
    from ape.scaffolds.config import BaseScaffoldConfig
    from ape.tasks.base import BaseTask
    from ape.toolkits.base import BaseToolsProvider


class BashExecuteToolsProvider(BaseExecuteToolsProvider):
    """Bash execution tool - simple subprocess-based execution."""

    SUPPORTED_TOOLS = ["bash_execute"]

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        """Initialize Bash execution tool."""
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

        # Extract tool configuration
        self.tool_config = config.tools_config.bash_execute

        self.logger.info("BashExecuteToolsProvider initialized")

    def register_tools(self, mcp: FastMCP, enabled_tools: set[str]):
        """Register Bash execution tool to MCP server"""
        if "bash_execute" in enabled_tools:
            # Check if file editing tools with execute capability are enabled
            file_edit_tools = {"file_write", "file_edit", "file_multi_edit"}
            enabled_file_tools = file_edit_tools & enabled_tools

            # Construct tool description based on file tools availability
            if enabled_file_tools:
                # Generate tool list string from actually enabled tools
                tool_list = ", ".join(sorted(enabled_file_tools))
                tool_description = f"""Execute Bash script and return output.

**IMPORTANT**: For persistent Bash scripts that need to be saved, use file editing tools ({tool_list}) with execute=True instead. Those tools will automatically save and execute the file.

**USE THIS TOOL ONLY FOR**: Temporary scripts or one-time execution without file persistence."""
            else:
                tool_description = "Execute Bash script and return output."

            @mcp.tool(
                description=tool_description
            )
            async def bash_execute(
                code: Annotated[Optional[str], Field(
                    description="Bash script code to execute"
                )] = None,
                file_path: Annotated[Optional[str], Field(
                    description="Bash script file path: scratch/..."
                )] = None,
                max_output_chars: Annotated[Optional[int], Field(
                    description="Max output characters to return"
                )] = 10000
            ) -> Dict[str, Any]:
                """Tool layer: handle placeholder parsing, then call core execution logic"""
                self.logger.info(f"Tool bash_execute: execution started (file_path={file_path}, has_code={bool(code)})")

                # Parameter validation: must provide and only provide one
                has_code = code and code.strip()
                has_file_path = file_path is not None

                if not has_code and not has_file_path:
                    return {
                        "success": False,
                        "error": "Either code or file_path must be provided"
                    }

                if has_code and has_file_path:
                    return {
                        "success": False,
                        "error": "Cannot provide both code and file_path, choose one"
                    }

                # If file_path is provided, need to read file content
                if file_path:
                    import aiofiles

                    # 1. Resolve full path
                    full_file_path = (self.task.workspaces_dir / file_path).resolve()

                    # 2. Security check: ensure path is within workspaces_dir
                    if not full_file_path.is_relative_to(self.task.workspaces_dir):
                        return {
                            "success": False,
                            "error": f"File path outside workspaces directory: {file_path}"
                        }

                    # 3. Verify file is in scratch workspace
                    scratch_workspace = self.task.scratch_workspace.path.resolve()
                    if not full_file_path.is_relative_to(scratch_workspace):
                        return {
                            "success": False,
                            "error": f"bash_execute only supports files in scratch workspace, got: {file_path}"
                        }

                    # 4. Check file existence
                    if not full_file_path.exists():
                        return {
                            "success": False,
                            "error": f"File not found: {file_path}"
                        }

                    # 5. Asynchronously read file content (avoid blocking event loop)
                    try:
                        async with aiofiles.open(full_file_path, 'r', encoding='utf-8') as f:
                            code = await f.read()
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Failed to read file {file_path}: {e}"
                        }

                    # 6. Verify file content is not empty
                    if not code or not code.strip():
                        return {
                            "success": False,
                            "error": f"File is empty: {file_path}"
                        }

                # Call core execution logic
                try:
                    result = await self.execute(code, max_output_chars=max_output_chars)
                    self.logger.info("Tool bash_execute: execution completed")
                    return result
                except Exception as e:
                    import traceback
                    self.logger.error(f"Bash execution failed: {traceback.format_exc()}")
                    return {
                        "success": False,
                        "error": traceback.format_exc()
                    }

    async def execute(self, code: str, max_output_chars: Optional[int] = None) -> Dict[str, Any]:
        """Execute Bash script in subprocess and return result.

        Args:
            code: Bash script to execute
            max_output_chars: Maximum output characters to return (None uses config default)

        Returns:
            Dict with 'success', 'stdout', 'stderr', 'exit_code'
        """
        # Use provided max_output_chars or fall back to config default
        if max_output_chars is None:
            max_output_chars = self.tool_config.max_output_chars

        # Create temporary file for script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            # Make executable
            temp_file.chmod(0o755)

            # Execute in subprocess with workspaces_dir as working directory
            # This matches file_system tools' path resolution: all paths are relative to workspaces_dir
            cwd = self.task.workspaces_dir if self.task and self.task.workspaces_dir else None
            process = await asyncio.create_subprocess_exec(
                'bash',
                str(temp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
            )

            # Wait with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.tool_config.timeout
                )
                exit_code = process.returncode
                timed_out = False
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                stdout_bytes = b''
                stderr_bytes = f"Execution timed out after {self.tool_config.timeout}s".encode()
                exit_code = -1
                timed_out = True

            # Decode output
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')

            # Truncate by characters if too long
            stdout_truncated = False
            stderr_truncated = False

            if len(stdout) > max_output_chars:
                stdout = stdout[:max_output_chars]
                stdout_truncated = True

            if len(stderr) > max_output_chars:
                stderr = stderr[:max_output_chars]
                stderr_truncated = True

            if stdout_truncated:
                stdout += "\n... (output truncated, showing first {} characters)".format(max_output_chars)
            if stderr_truncated:
                stderr += "\n... (output truncated, showing first {} characters)".format(max_output_chars)

            # Build result
            result = {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }

            if timed_out:
                result["timeout"] = True
                result["message"] = f"Execution timed out after {self.tool_config.timeout}s"
            elif exit_code == 0:
                result["message"] = "Execution completed successfully"
            else:
                result["message"] = f"Execution failed with exit code {exit_code}"

            return result

        finally:
            # Clean up temp file
            try:
                temp_file.unlink()
            except Exception:
                pass

# Automatically register tool
from ape.toolkits.registry import register_tool
register_tool(BashExecuteToolsProvider)
