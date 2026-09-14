"""
Claude Code Scaffold - Claude Code SDK Integration

Based on Claude Code SDK scaffold implementation:
1. Follows core Scaffold protocol
2. Uses Claude Code SDK built-in tool system (Read, Write, Edit, etc.)
3. Configures tool permissions and dual workspace through ClaudeAgentOptions
4. Provides lean_verify and lean_retrieve extension tools through MCP server

This used to claim "Disables Bash commands". It did not, and had not since it was written:
the scaffold refused exactly one tool (`Explore`) while `permission_mode` defaulted to
`bypassPermissions`, so Bash, WebFetch, WebSearch, Task, Write and Edit all ran auto-approved.
Nothing read the claim and enforced it, so it survived as documentation of a contract the code
never had -- the most expensive kind of comment, because it stops people checking.

Containment is now configured and off by default, which keeps existing callers working and
makes the posture something a run states rather than inherits: `tools`, `disallowed_tools`,
`setting_sources` and `strict_mcp_config` on `ClaudeCodeConfig`, logged at INFO when the
session starts. `config.py` records what the permissive defaults reach from a Mathlib review
workspace, and why that list is a measurement problem rather than a security one.
"""

from .scaffold import ClaudeCodeScaffold

__all__ = [
    'ClaudeCodeScaffold'
]

