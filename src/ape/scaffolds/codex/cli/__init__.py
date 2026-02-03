"""
Codex CLI - Command line interface module

Provides a convenient command line entry, encapsulating:
- Relay mode and conversation tracking
- MCP server automatic configuration
- TOML configuration (model provider + MCP server)
- Integration with external `codex` command

Main components:
- main.py: Command line entry and parameter parsing
- task.py: CLI dedicated task class
- config.py: CLI configuration model

Usage:
    python -m ape.scaffolds.codex.cli.main --help
"""

from .main import cli_main
from .task import CodexCLITask, CodexCLITaskConfig
from .config import CodexCLIConfig

__all__ = [
    'cli_main',
    'CodexCLITask',
    'CodexCLITaskConfig',
    'CodexCLIConfig',
]
