"""
Codex Scaffold Configuration Models

Codex Scaffold configuration models, inherit from BaseScaffoldConfig and add Codex-specific configurations.
"""

from typing import Optional
from ape.scaffolds.config import BaseScaffoldConfig


class CodexConfig(BaseScaffoldConfig):
    """Codex Scaffold configuration, inherit from BaseScaffoldConfig and add specific configurations"""

    # Scaffold type identifier
    scaffold_type: str = "codex"

    # MCP server name prefix for Codex scaffold (includes trailing __)
    mcp_server_name: str = "mcp__lean-research__"

    # Codex specific configurations
    mcp_server_startup_timeout: float = 2.0
    codex_timeout: int = 600  # Codex CLI execution timeout (seconds)
    # NOTE: Model selection is driven by llm_config (canonical model name) to match Claude Code behavior.
    use_native_tools: bool = False  # Whether to use our native MCP tools (file_system, bash_execute); if False, use Codex builtin tools instead

    # Sandbox and permission configurations (aligned with CodexBridge)
    sandbox_mode: str = "danger-full-access"  # Sandbox mode: "read-only" / "workspace-write" / "danger-full-access"
    network_access: bool = False  # Allow networked commands (curl, git clone, API calls)
    web_search: bool = False  # Allow built-in web search tool
    approval_policy: str = "never"  # Approval policy: "never" / "on-request" / "on-failure" / "untrusted"

    # LLM streaming configuration
    # Default disable streaming to ensure token usage statistics correct
    # In streaming mode, some provider's token usage may not return correctly, resulting in cost statistics of 0
    enable_streaming: bool = False

    # Intelligent stop detection configuration (similar to ClaudeCode)
    consecutive_retries_threshold: Optional[int] = 3  # Consecutive prompt supplement threshold, None means not to check
    total_retries_threshold: Optional[int] = None  # Total retries threshold, None means not to check

    def model_post_init(self, __context) -> None:
        """Post-initialization processing: ensure relay mode and streaming configuration correct"""
        # Codex uses internal relay, all LLMConfig should enable relay_mode
        # relay_mode allows empty return (e.g. edge case of max_tokens=1), avoid MalformedResponseError
        self.llm_config.relay_mode = True

        # Apply scaffold-level streaming configuration to llm_config
        self.llm_config.streaming = self.enable_streaming
