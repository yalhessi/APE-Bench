"""
Claude Code CLI - Command line interface module

Provides a convenient command line entry, encapsulating:
- Relay mode and conversation tracking
- MCP server automatic configuration
- Environment variable setting
- Integration with external `claude` command

Main components:
- main.py: Command line entry and parameter parsing
- task.py: CLI dedicated task class
- config.py: CLI configuration model

Usage:
    python -m ape.scaffolds.claude_code.cli.main --help
"""

from .main import cli_main
from .task import CLITask, CLITaskConfig
from .config import ClaudeCodeCLIConfig

__all__ = [
    'cli_main',
    'CLITask',
    'CLITaskConfig',
    'ClaudeCodeCLIConfig',
]
