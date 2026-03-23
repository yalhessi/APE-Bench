"""
Claude Code CLI Task - CLI-specific task

Design description:
1. Used to support MCP server setup for Claude Code CLI
2. Call external `claude` command for interaction, no own UI required
3. Support relay mode and conversation tracking
4. Fully align with new conversation manager architecture
"""

from typing import Dict, Any, Optional, TYPE_CHECKING, Literal
from pathlib import Path
from pydantic import Field

# import task base class
from ape.tasks.base import BaseTask, BaseTaskData, BaseTaskConfig, register_task, BaseTaskResult, EvaluationResult

if TYPE_CHECKING:
    from ape.tasks.models import WorkspaceInfo
    from ape.scaffolds.config import BaseScaffoldConfig

class CLITaskData(BaseTaskData):
    """CLI task data model - completely separate verify and retrieve configurations

    Design principles (consistent with ApeAgent):
    1. verify_* parameters → Target Workspace (used for code verification)
       - if provided: get Git repository through get_workspace, create WorkspaceInfo with Git information
       - if not provided: create local WorkspaceInfo using local_workspace_path (commit/repo/default_target=None)

    2. retrieve_* parameters → Reference Workspaces (used for semantic retrieval)
       - create reference workspace for LeanRetrieve tool usage
       - completely independent of target workspace

    3. Three scenarios:
       Scenario A: only local path (--workspace /path)
         - Target workspace: local path, no Git information
         - Reference workspaces: empty
         - LeanRetrieve: returns "Workspace 'target' not found" (naturally fails)

       Scenario B: only verify configuration (--verify_commit_hash abc123)
         - Target workspace: abc123 version of Git repository
         - Reference workspaces: empty
         - LeanRetrieve: can search on target workspace

       Scenario C: verify + retrieve configuration
         - Target workspace: verify specified version
         - Reference workspaces: [retrieve specified version]
         - LeanRetrieve: can search on reference workspace, also on target workspace

    4. Consistent with Batch mode:
       - Batch mode: task.data.target_workspace → target workspace
       - CLI mode: task.data.verify_*/local_workspace_path → target workspace
       - all passed through task.data, maintaining consistency
    """

    task_type: Literal["claude_code_cli"] = Field(
        default="claude_code_cli",
        description="Task type identifier"
    )

    # ===== Verify configuration: control Target Workspace retrieval =====
    # if provided, get Git repository through get_workspace as target workspace
    verify_commit_hash: Optional[str] = None
    verify_repo_url: Optional[str] = None
    verify_default_target: Optional[str] = None

    # ===== Local workspace path =====
    # mutually exclusive with verify_*, used to specify local path as target workspace
    local_workspace_path: Optional[Path] = None

    # ===== Retrieve configuration: create Reference Workspaces for retrieval tool usage =====
    # if provided, create reference workspace for LeanRetrieve tool retrieval
    retrieve_commit_hash: Optional[str] = None
    retrieve_repo_url: Optional[str] = None
    retrieve_default_target: Optional[str] = None

    # ===== Reference workspaces list (future extension: support multiple references) =====
    reference_workspaces: Optional[list] = None


class CLITaskConfig(BaseTaskConfig):
    """CLI task configuration

    Tool configuration is managed through BaseScaffoldConfig.task_config
    """
    pass


class CLITask(BaseTask):
    """
    Claude Code CLI-specific task

    Design principles:
    1. Minimal implementation - only provide necessary task interfaces
    2. No special tools registration - all tools registered through basic tools
    3. No interaction management - interaction handled by external `claude` command
    4. Support conversation tracking - through relay callback

    Differences from ApeAgent CLITask:
    - ApeAgent: internal interaction management (own UI components)
    - Claude Code: external `claude` command (delegate to Claude Code SDK)
    """

    # class variable configuration
    task_type = "claude_code_cli"
    data_class = CLITaskData
    task_config_class = CLITaskConfig

    def __init__(self, data: CLITaskData, config: 'BaseScaffoldConfig'):
        """Initialize Claude Code CLI task"""
        super().__init__(data, config)

    def _is_lean_task(self) -> bool:
        """
        Check if it is a Lean task (requires Lean workspace)

        New logic: CLI task does not use this method to determine, because:
        - CLI task's workspace is explicitly specified through verify_*/local_workspace_path
        - does not rely on implicit _is_lean_task()

        To maintain compatibility with base class interface, always return False
        """
        return False

    async def _setup_target_workspace(self) -> Optional['WorkspaceInfo']:
        """
        Override base class method, implement CLI-specific target workspace logic

        CLI mode:
        - Priority 1: verify configuration (Git repository)
        - Priority 2: local_workspace_path (local path)
        """
        from ape.tasks.models import WorkspaceInfo, GitWorkspaceSource, LocalWorkspaceSource

        # Priority 1: verify configuration (Git repository)
        if self.data.verify_commit_hash:
            target_workspace_path = await self._get_lean_repo_workspace(
                self.data.verify_commit_hash,
                repo_url=self.data.verify_repo_url
            )
            self.logger.info(f"Target workspace from verify config: {target_workspace_path}")

            return WorkspaceInfo(
                name="target",
                path=target_workspace_path,
                source=GitWorkspaceSource(
                    commit_hash=self.data.verify_commit_hash,
                    repo_url=self.data.verify_repo_url,
                ),
                default_target=self.data.verify_default_target,
                read_only_path_patterns=[]  # CLI mode writable
            )

        # Priority 2: local workspace path
        elif self.data.local_workspace_path:
            target_workspace_path = self.data.local_workspace_path.resolve()
            if not target_workspace_path.exists():
                raise RuntimeError(f"Local workspace does not exist: {self.data.local_workspace_path}")
            self.logger.info(f"Target workspace from local path: {target_workspace_path}")

            return WorkspaceInfo(
                name="target",
                path=target_workspace_path,
                source=LocalWorkspaceSource(path=target_workspace_path),
                default_target=None,
                read_only_path_patterns=[]  # CLI mode writable
            )

        return None

    async def _setup_reference_workspaces(self) -> Optional[list['WorkspaceInfo']]:
        """
        Override base class method, implement CLI-specific reference workspaces logic

        CLI mode:
        - Create single reference workspace from retrieve_* parameters
        """
        from ape.tasks.models import WorkspaceInfo, GitWorkspaceSource
        from ape.utils.file_ops import normalize_repo_url

        if self.data.retrieve_commit_hash:
            ref_workspace_path = await self._get_lean_repo_workspace(
                self.data.retrieve_commit_hash,
                repo_url=self.data.retrieve_repo_url
            )
            self.logger.info(f"Reference workspace from retrieve config: {ref_workspace_path}")

            # Extract repo name from repo_url as workspace name
            ref_workspace_name = normalize_repo_url(self.data.retrieve_repo_url)

            ref_ws_info = WorkspaceInfo(
                name=ref_workspace_name,  # use repo name (e.g. 'mathlib4')
                path=ref_workspace_path,
                source=GitWorkspaceSource(
                    commit_hash=self.data.retrieve_commit_hash,
                    repo_url=self.data.retrieve_repo_url,
                ),
                default_target=self.data.retrieve_default_target,
                read_only_path_patterns=["**/*"]  # Reference workspace is completely read-only
            )
            return [ref_ws_info]

        return None

    @classmethod
    def create_data_from_dict(cls, data: Dict[str, Any]) -> CLITaskData:
        """Create task data instance from dictionary (for API calls, etc.)"""
        return CLITaskData(
            task_id=data.get("task_id", "claude-cli"),
            verify_commit_hash=data.get("verify_commit_hash"),
            verify_repo_url=data.get("verify_repo_url"),
            verify_default_target=data.get("verify_default_target"),
            local_workspace_path=Path(data["local_workspace_path"]) if data.get("local_workspace_path") else None,
            retrieve_commit_hash=data.get("retrieve_commit_hash"),
            retrieve_repo_url=data.get("retrieve_repo_url"),
            retrieve_default_target=data.get("retrieve_default_target")
        )

    async def create_user_prompt(self) -> str:
        """
        Create user prompt

        Claude Code CLI mode does not need initial prompt, because:
        1. Interaction is handled by external `claude` command
        2. User provides prompt directly through command-line parameters or interactive input

        Returns:
            Empty string
        """
        return ""

    async def register_task_tools(self, mcp) -> None:
        """
        Register task-specific tools

        Claude Code CLI mode does not need special tools:
        - All file operations through basic file tools
        - All Lean operations through basic lean tools
        - No submit_result (CLI is controlled by user)

        """
        return

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """
        Check if termination should be performed

        Claude Code CLI mode never terminates automatically, because:
        - Interaction is controlled by user
        - User decides when to exit `claude` command

        Returns:
            False - never terminates automatically
        """
        return False

    def create_result(self, **kwargs) -> BaseTaskResult:
        """
        Create task result

        Claude Code CLI mode usually does not need result, but provides minimal implementation for compatibility

        Args:
            **kwargs: Result parameters

        Returns:
            BaseTaskResult instance
        """
        return BaseTaskResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=kwargs.get("success", True),
            score=kwargs.get("score", 1.0),
            error=kwargs.get("error"),
            metadata={
                "mode": "claude_code_cli",
                "scaffold": "claude_code",
                **kwargs
            }
        )


# Automatically register task type
register_task("claude_code_cli", CLITask)
