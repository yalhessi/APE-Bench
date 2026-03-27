"""Codex CLI package."""

from __future__ import annotations

__all__ = ["cli_main", "CodexCLITask", "CodexCLITaskConfig", "CodexCLIConfig"]


def __getattr__(name: str):
    if name == "cli_main":
        from .main import cli_main

        return cli_main
    if name in {"CodexCLITask", "CodexCLITaskConfig"}:
        from .task import CodexCLITask, CodexCLITaskConfig

        return {"CodexCLITask": CodexCLITask, "CodexCLITaskConfig": CodexCLITaskConfig}[name]
    if name == "CodexCLIConfig":
        from .config import CodexCLIConfig

        return CodexCLIConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
