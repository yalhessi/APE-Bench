"""
Claude Code CLI Config - CLI configuration model

Design description:
Claude Code CLI is a simple wrapper for the official claude command, responsible for:
1. Starting MCP server (provide project tools)
2. Starting relay (model routing + conversation tracking)
3. Configuring environment variables
4. Calling external claude command

All UI interactions are handled by the external claude command, so no additional UI configuration is needed.
"""

from ..config import ClaudeCodeConfig
from .task import CLITaskConfig


class ClaudeCodeCLIConfig(ClaudeCodeConfig):
    """
    Claude Code CLI configuration

    Inherits ClaudeCodeConfig, adds CLI-specific configuration.
    Uses task_config field to support task configuration overrides.

    Note:
    1. Claude Code CLI is a simple wrapper for the official claude command,
       no additional UI configuration (welcome, help, etc.) is needed,
       all interactions are handled by the external claude command.
    2. Workspace configuration (verify/retrieve) is passed through task.data,
       not stored in Config (consistent with ApeAgent CLI)
    """
    # Log control
    log_level: str = "WARNING"  # default WARNING level, ignore INFO and DEBUG logs

    # CLI mode uses default permission mode (ask user for confirmation)
    permission_mode: str = "default"

    # Task configuration
    task_config: CLITaskConfig = CLITaskConfig()
