"""
Codex CLI Config - CLI configuration model
"""

from ..config import CodexConfig
from .task import CodexCLITaskConfig


class CodexCLIConfig(CodexConfig):
    """
    Codex CLI configuration
    
    Inherits CodexConfig, adds CLI-specific configuration.
    Note: CLI mode does not use CodexBridge, directly calls `codex` command.
    """
    # Log control
    log_level: str = "WARNING"
    
    # CLI mode uses workspace-write (user can modify files)
    sandbox_mode: str = "workspace-write"
    
    # Task configuration
    task_config: CodexCLITaskConfig = CodexCLITaskConfig()
