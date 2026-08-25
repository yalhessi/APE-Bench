"""
Lean Verify Tool - New simplified tool interface
"""

from typing import Dict, Any, Optional, Annotated, TYPE_CHECKING, Union, List
import traceback
from fastmcp import FastMCP
from pydantic import Field
from pathlib import Path
import aiofiles

from .core.verification import VerificationEngine
from .config import LeanVerifyToolConfig
from ape.utils.logging import create_logger
from ape.toolkits.execute.base import BaseExecuteToolsProvider

if TYPE_CHECKING:
    import logging
    from ape.tasks.models import WorkspaceInfo
    from ape.tasks.base import BaseTask
    from ape.toolkits.base import BaseToolsProvider

class LeanVerifyToolsProvider(BaseExecuteToolsProvider):
    """Lean verification tool - simplified tool interface based on new architecture"""

    SUPPORTED_TOOLS = ["lean_verify"]

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        """Initialize verification tool"""
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
        self.tool_config = config.tools_config.lean_verify

        # Extract paths for convenience
        self.target_workspace = self.task.target_workspace.path if self.task.target_workspace else None
        self.scratch_workspace = self.task.scratch_workspace.path if self.task.scratch_workspace else None

        # Core components
        self.verification_engine = VerificationEngine(self.tool_config, self.logger)

        self.logger.info(f"Lean verification tool initialized: target={self.target_workspace}")

    def register_tools(self, mcp: FastMCP, enabled_tools: set[str]):
        """Register Lean verification tool to MCP server"""
        if "lean_verify" in enabled_tools:
            # Check if file editing tools with execute capability are enabled
            file_edit_tools = {"file_write", "file_edit", "file_multi_edit"}
            enabled_file_tools = file_edit_tools & enabled_tools

            # Construct tool description based on file tools availability
            if enabled_file_tools:
                # Generate tool list string from actually enabled tools
                tool_list = ", ".join(sorted(enabled_file_tools))
                tool_description = f"""Verify Lean code for correctness and provide detailed feedback.

**IMPORTANT**: For persistent files that need to be saved, use file editing tools ({tool_list}) with execute=True instead. Those tools will automatically verify and save the file.

**USE THIS TOOL ONLY FOR**: Temporary code snippets or one-time verification without file persistence."""
            else:
                tool_description = "Verify Lean code for correctness and provide detailed feedback."

            @mcp.tool(
                description=tool_description
            )
            async def lean_verify(
                code: Annotated[Optional[str], Field(
                    description="Lean code to verify"
                )] = None,
                file_path: Annotated[Optional[str], Field(
                    description="Lean file path: scratch/..."
                )] = None,
                max_messages: Annotated[Optional[int], Field(
                    description="Max messages to return (prioritized: error > warning > info)"
                )] = 20
            ) -> Dict[str, Any]:
                """Tool layer: handle placeholder parsing, then call core verification logic"""
                self.logger.info(f"Tool lean_verify: execution started (file_path={file_path}, has_code={bool(code)})")
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
                    # 1. Resolve full path
                    full_file_path = (self.task.workspaces_dir / file_path).resolve()

                    # 2. Security check: ensure path is within workspaces_dir
                    if not full_file_path.is_relative_to(self.task.workspaces_dir):
                        return {
                            "success": False,
                            "error": f"File path outside workspaces directory: {file_path}"
                        }

                    # 3. Verify the file is somewhere this task allows reading from.
                    #
                    # Scratch is always allowed. Some tasks — notably PR review — have no
                    # scratch file at all: the thing worth compiling is the reviewed file in
                    # `target/`, which is read-only but not blocked. Those tasks opt in via
                    # `lean_verify_allows_target`, so proof_engineering's rule that a
                    # submission must be self-contained is untouched.
                    #
                    # This was not a hypothetical. Every `lean_verify(file_path=...)` call in
                    # the rep3 and rep4 review runs passed `target/Mathlib/...` and every one
                    # was refused, in a task whose entire premise is compiling things.
                    allowed_roots = [self.scratch_workspace.resolve()]
                    if getattr(self.task, "lean_verify_allows_target", False) and self.target_workspace:
                        allowed_roots.append(Path(self.target_workspace).resolve())
                    if not any(full_file_path.is_relative_to(root) for root in allowed_roots):
                        hint = ""
                        if getattr(self.task, "lean_verify_allows_target", False):
                            hint = (" Reviewed files live under `target/`; to test a change to "
                                    "one, use lean_verify_edit.")
                        return {
                            "success": False,
                            "error": (
                                f"lean_verify can only read files under "
                                f"{', '.join(root.name for root in allowed_roots)}; got: {file_path}."
                                + hint
                            ),
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
                
                # Call core verification logic (only pass code string and max_messages)
                try:
                    result = await self.execute(code, max_messages=max_messages)
                    self.logger.info(f"Tool lean_verify: execution completed")
                    return result
                except Exception as e:
                    # System error: return full traceback for debugging
                    self.logger.error(f"Verification failed: {traceback.format_exc()}")
                    return {
                        "success": False,
                        "error": traceback.format_exc()
                    }

    async def execute(self, code: str, max_messages: Optional[int] = 20) -> Dict[str, Any]:
        """Execute service layer: core verification interface

        Args:
            code: Lean code string to verify (already passed through tool layer validation and processing)
            max_messages: Maximum message number limit (None means no limit)

        Returns:
            Dict: Verification result

        Note:
            This is internal service interface, tool layer is responsible for all input validation, file reading, etc.
            This method only responsible for core verification logic.
        """
        # Security check: verify code doesn't depend on blocked paths
        from ape.runtime.utils import collect_blocked_paths
        from ape.toolkits.code.lean.lean_parser import check_dependencies_against_blocked_paths

        if self.task.target_workspace:
            # Get blocked paths (absolute)
            blocked_paths_absolute = collect_blocked_paths(self.task.target_workspace, self.logger)

            # Convert to relative paths
            blocked_paths_relative = []
            for blocked_path in blocked_paths_absolute:
                try:
                    rel_path = blocked_path.relative_to(self.target_workspace)
                    blocked_paths_relative.append(rel_path)
                except ValueError:
                    # Skip paths outside target workspace
                    pass

            # Check dependencies (async call)
            is_safe, error_message, blocked_deps = await check_dependencies_against_blocked_paths(
                code=code.strip(),
                working_dir=self.target_workspace,
                blocked_paths=blocked_paths_relative
            )

            if not is_safe:
                return {
                    "success": False,
                    "errors": [{
                        "severity": "error",
                        "data": error_message,
                        "code_line": None,
                        "pos": None
                    }],
                    "warnings": [],
                    "infos": [],
                    "axioms": [],
                    "message": "Verification blocked: code depends on blocked paths"
                }

        # Execute verification
        result = await self.verification_engine.verify(
            code=code.strip(),
            working_dir=self.target_workspace,
            timeout=self.tool_config.timeout,
            max_memory_gb=self.tool_config.max_memory_gb,
            allow_sorries=self.tool_config.allow_sorries,
            accepted_axioms=self.tool_config.accepted_axioms,
            nproc=self.tool_config.nproc,
        )
        
        # Format messages
        errors_formatted = [
            {
                "severity": msg.severity,
                "data": msg.data,
                "code_line": msg.code_line,
                "pos": msg.pos
            } for msg in result.errors
        ]
        warnings_formatted = [
            {
                "severity": msg.severity,
                "data": msg.data,
                "code_line": msg.code_line,
                "pos": msg.pos
            } for msg in result.warnings
        ]
        infos_formatted = [
            {
                "severity": msg.severity,
                "data": msg.data,
                "code_line": msg.code_line,
                "pos": msg.pos
            } for msg in result.infos
        ]
        
        # Apply message number limit (priority: error > warning > info)
        messages_truncated = False
        original_total_messages = len(errors_formatted) + len(warnings_formatted) + len(infos_formatted)
        
        if max_messages is not None and max_messages > 0:
            remaining = max_messages
            
            # Prioritize keeping all errors
            if len(errors_formatted) >= remaining:
                messages_truncated = len(errors_formatted) > remaining or len(warnings_formatted) > 0 or len(infos_formatted) > 0
                errors_formatted = errors_formatted[:remaining]
                warnings_formatted = []
                infos_formatted = []
            else:
                remaining -= len(errors_formatted)
                
                # Then keep warnings
                if len(warnings_formatted) >= remaining:
                    messages_truncated = len(warnings_formatted) > remaining or len(infos_formatted) > 0
                    warnings_formatted = warnings_formatted[:remaining]
                    infos_formatted = []
                else:
                    remaining -= len(warnings_formatted)
                    
                    # Finally keep infos
                    if len(infos_formatted) > remaining:
                        messages_truncated = True
                        infos_formatted = infos_formatted[:remaining]
        
        # Build return result
        response = {
            "success": result.success,
            "errors": errors_formatted,
            "warnings": warnings_formatted,
            "infos": infos_formatted,
            "axioms": result.axioms
        }
        
        # Add truncation indicator
        if messages_truncated:
            response["messages_truncated"] = True
            response["total_messages_before_truncation"] = original_total_messages
        
        # Check if timeout
        is_timeout = result.return_code == -15
        if is_timeout:
            response["timeout"] = True
            response["message"] = f"Lean verification timed out after {self.tool_config.timeout}s. Collected {len(result.messages)} messages before timeout."
        else:
            # Set message field
            if result.success:
                response["message"] = "Lean verification completed successfully"
            else:
                response["message"] = "Lean verification failed"
        
        return response

    @classmethod
    def get_required_resources(
        cls,
        scratch_workspace_info: Optional['WorkspaceInfo'] = None,
        target_workspace_info: Optional['WorkspaceInfo'] = None,
        reference_workspaces_info: Optional[List['WorkspaceInfo']] = None,
        config: Optional[Any] = None,
    ) -> List[tuple[Path, Optional[Path]]]:
        """Get complete resources required by lean_verify toolkit.

        Returns:
            List of (host_path, container_path) tuples containing:
            - All workspace paths (target + references) - in PROJECT_ROOT
            - All snapshot state files - in PROJECT_ROOT
            - .elan structure with all required toolchains - in HOME
        """
        actual_config = config.tools_config.lean_verify
        resources = []
        reference_workspaces_info = reference_workspaces_info or []

        # Helper to add workspace and snapshot (these are in PROJECT_ROOT)
        def add_workspace_resources(ws_info: "WorkspaceInfo", repo_name: str):
            if not ws_info or not ws_info.commit_hash:
                return

            # Add workspace path (in PROJECT_ROOT, use default mapping)
            workspace_path = actual_config.get_workspace_dir(repo_name) / ws_info.commit_hash
            if workspace_path.exists():
                resources.append((workspace_path, None))

            # Add snapshot state file (in PROJECT_ROOT, use default mapping)
            state_file = (actual_config.get_snapshot_dir(repo_name) / ws_info.commit_hash).with_suffix('.state')
            if state_file.exists():
                resources.append((state_file, None))

            # Collect toolchain from WorkspaceInfo (in HOME, map to /root/.elan)
            if ws_info.toolchain:
                try:
                    dir_name = ws_info.toolchain.replace('/', '--').replace(':', '---')
                    host_elan_root = Path.home() / ".elan"
                    toolchain_path = host_elan_root / "toolchains" / dir_name
                    if toolchain_path.exists():
                        # Map to /root/.elan/toolchains/{dir_name}
                        container_toolchain_path = Path("/root/.elan/toolchains") / dir_name
                        resources.append((toolchain_path, container_toolchain_path))
                except Exception:
                    pass  # Silently skip if toolchain not found

        # Add target workspace resources
        if target_workspace_info:
            repo_name, _ = actual_config.resolve_repo(target_workspace_info.repo_url)
            add_workspace_resources(target_workspace_info, repo_name)

        # Add reference workspaces resources
        for ref_ws in reference_workspaces_info:
            repo_name, _ = actual_config.resolve_repo(ref_ws.repo_url)
            add_workspace_resources(ref_ws, repo_name)

        # Add .elan common structure (excluding tmp/) - map to /root/.elan
        host_elan_root = Path.home() / ".elan"
        if host_elan_root.exists():
            for item in ["bin", "env", "settings.toml"]:
                host_path = host_elan_root / item
                if host_path.exists():
                    container_path = Path("/root/.elan") / item
                    resources.append((host_path, container_path))

        return resources

    @classmethod
    def get_environment_config(cls, config: Optional[Any] = None) -> Dict[str, str]:
        """Get environment variables required for Lean verification in container.

        Args:
            config: Toolkit configuration or scaffold config

        Returns:
            Environment variables for ELAN_HOME and PATH configuration.
            Values containing $VAR will be expanded by runtime using container's actual values.
        """
        return {
            "ELAN_HOME": "/root/.elan",
            "PATH": "/root/.elan/bin:$PATH"  # $PATH will be expanded to container's actual PATH
        }

# Automatically register tool
from ape.toolkits.registry import register_tool
register_tool(LeanVerifyToolsProvider)
