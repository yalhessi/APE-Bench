"""
Codex Scaffold - OpenAI Codex CLI Integration

Prerequisites: the `codex` CLI on PATH (checked with `codex-cli` 0.144.5, which speaks only the
Responses API).

1. Follows core Scaffold protocol
2. Runs `codex exec --json` per turn, resumed by thread id (`conversation.py`)
3. Configures the relay, the MCP server and the features through an attempt-local
   `workspaces/.codex/config.toml` (`scaffold.codex_config`)
4. Uses the relay to serve the CLI's Responses calls from APE's client and record them
5. Supports both batch and CLI modes
"""

from .scaffold import CodexScaffold

__all__ = [
    'CodexScaffold'
]

__version__ = '1.0.0'
