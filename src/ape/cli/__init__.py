"""Top-level CLI package for interactive APE agent sessions."""

from __future__ import annotations

__all__ = ["cli_main"]


def __getattr__(name: str):
    if name == "cli_main":
        from .main import cli_main

        return cli_main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
