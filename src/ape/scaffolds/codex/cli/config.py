"""
Codex CLI Config - CLI configuration model
"""

from ..config import CodexConfig
from .task import CodexCLITaskConfig


class CodexCLIConfig(CodexConfig):
    """
    Codex CLI configuration
    
    Inherits CodexConfig, adds CLI-specific configuration.
    Note: CLI mode runs the interactive `codex` command; batch mode runs `codex exec`.
    """
    # Log control
    log_level: str = "WARNING"
    
    # CLI mode uses workspace-write (user can modify files)
    sandbox_mode: str = "workspace-write"
    
    # Task configuration
    task_config: CodexCLITaskConfig = CodexCLITaskConfig()
