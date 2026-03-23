"""Isabelle verification tool provider."""

import traceback
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING, Annotated

from fastmcp import FastMCP
from pydantic import Field

from ape.tasks.models import IsabelleWorkspaceInfo
from ape.toolkits.execute.base import BaseExecuteToolsProvider
from ape.utils.logging import create_logger

from .config import IsabelleVerifyToolConfig
from .core import IsabelleVerificationEngine

if TYPE_CHECKING:
    import logging
    from ape.tasks.base import BaseTask


class IsabelleVerifyToolsProvider(BaseExecuteToolsProvider):
    """Verify Isabelle theories using `isabelle process`."""

    SUPPORTED_TOOLS = ["isabelle_verify"]

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        super().__init__(
            task=task,
            config=config,
            logger=logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )

        if not self.logger:
            self.logger = create_logger()

        self.tool_config = config.tools_config.isabelle_verify
        self.verification_engine = IsabelleVerificationEngine(self.tool_config, self.logger)
        self.target_workspace = self.task.target_workspace if self.task else None
        self.scratch_workspace = self.task.scratch_workspace.path if self.task and self.task.scratch_workspace else None

        self.logger.info("Isabelle verification tool initialized")

    def register_tools(self, mcp: FastMCP, enabled_tools: set[str]):
        """Register the Isabelle verification tool."""
        if "isabelle_verify" not in enabled_tools:
            return

        file_edit_tools = {"file_write", "file_edit", "file_multi_edit"}
        enabled_file_tools = file_edit_tools & enabled_tools

        if enabled_file_tools:
            tool_list = ", ".join(sorted(enabled_file_tools))
            description = f"""Verify an Isabelle theory file and return diagnostics.

**IMPORTANT**: For persistent theory edits, use file editing tools ({tool_list}) with execute=True.

**NOTE**: Isabelle verification is file-based in this MVP, so file_path is required."""
        else:
            description = "Verify an Isabelle theory file and return diagnostics."

        @mcp.tool(description=description)
        async def isabelle_verify(
            file_path: Annotated[str, Field(description="Theory file path, e.g. target/Foo/Bar.thy")],
            max_messages: Annotated[Optional[int], Field(
                description="Max messages to return (prioritized: error > warning > info)"
            )] = None,
        ) -> Dict[str, Any]:
            self.logger.info(f"Tool isabelle_verify: execution started (file_path={file_path})")
            try:
                result = await self.execute(file_path=file_path, max_messages=max_messages)
                self.logger.info("Tool isabelle_verify: execution completed")
                return result
            except Exception:
                self.logger.error(f"Isabelle verification failed: {traceback.format_exc()}")
                return {"success": False, "error": traceback.format_exc()}

    def _resolve_workspace_file(self, file_path: str | Path) -> Path:
        """Resolve a workspace-relative theory path."""
        candidate = Path(file_path)
        if candidate.is_absolute():
            return candidate.resolve()

        if not self.task or not self.task.workspaces_dir:
            raise ValueError("Task workspaces are not initialized")
        if ".." in candidate.parts:
            raise ValueError(f"Parent directory references are not allowed: {file_path}")

        # Preserve workspace-relative security checks before resolving symlinks.
        # Target workspaces are commonly symlinked to external checkout locations.
        return (self.task.workspaces_dir / candidate).resolve()

    async def execute(
        self,
        code: Optional[str] = None,
        file_path: Optional[str | Path] = None,
        max_messages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Verify an Isabelle theory file.

        The optional code parameter is accepted for compatibility with the file-system
        auto-execution path, but verification always runs against the on-disk theory file.
        """
        del code  # Isabelle verification is file-based in this MVP.

        if not file_path:
            return {
                "success": False,
                "error": "Isabelle verification requires file_path because verification is file-based.",
            }

        if not isinstance(self.target_workspace, IsabelleWorkspaceInfo):
            return {
                "success": False,
                "error": "Task target workspace is not configured as IsabelleWorkspaceInfo.",
            }
        if not self.target_workspace.path:
            return {
                "success": False,
                "error": "Task target workspace path is not initialized.",
            }

        theory_path = self._resolve_workspace_file(file_path)

        if self.scratch_workspace and theory_path.is_relative_to(self.scratch_workspace.resolve()):
            return {
                "success": False,
                "error": (
                    "Isabelle verification currently supports theory files in the target workspace only. "
                    "Use a target-relative theory path for process-based verification."
                ),
            }

        if not theory_path.is_relative_to(self.target_workspace.path.resolve()):
            return {
                "success": False,
                "error": f"Theory file must be inside target workspace: {file_path}",
            }

        return await self.verification_engine.verify_file(
            file_path=theory_path,
            workspace=self.target_workspace,
            max_messages=max_messages,
        )


from ape.toolkits.registry import register_tool

register_tool(IsabelleVerifyToolsProvider)
