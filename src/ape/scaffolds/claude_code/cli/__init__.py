"""Claude Code CLI package."""

from __future__ import annotations

__all__ = ["cli_main", "CLITask", "CLITaskConfig", "ClaudeCodeCLIConfig"]


def __getattr__(name: str):
    if name == "cli_main":
        from .main import cli_main

        return cli_main
    if name in {"CLITask", "CLITaskConfig"}:
        from .task import CLITask, CLITaskConfig

        return {"CLITask": CLITask, "CLITaskConfig": CLITaskConfig}[name]
    if name == "ClaudeCodeCLIConfig":
        from .config import ClaudeCodeCLIConfig

        return ClaudeCodeCLIConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
