"""
Claude Code Scaffold Configuration Models

Claude Code Scaffold configuration models, inherit from BaseScaffoldConfig and add specific configurations.
"""

from typing import Optional
from pydantic import Field
from ape.scaffolds.config import BaseScaffoldConfig
from ape.llm_clients.config import LLMConfig


class ClaudeCodeConfig(BaseScaffoldConfig):
    """Claude Code Scaffold configuration, inherit from BaseScaffoldConfig and add specific configurations"""

    # Scaffold type identifier
    scaffold_type: str = "claude_code"

    # MCP server name prefix for ClaudeCode scaffold (includes trailing __)
    mcp_server_name: str = "mcp__core__"

    # Claude Code specific configurations
    fast_llm_config: Optional[LLMConfig] = Field(
        default_factory=lambda: LLMConfig(model_name="gpt_5_nano")
    )  # Fast model configuration (for Haiku/Subagent), None means using main model llm_config
    mcp_server_startup_timeout: float = 2.0
    use_native_tools: bool = False  # whether to use our native MCP tools (file_system, bash_execute); if False, use SDK builtin tools instead
    permission_mode: str = "bypassPermissions"  # permission mode: "default" or "bypassPermissions"

    # LLM streaming configuration
    # default disable streaming to ensure token usage statistics correct
    # in streaming mode, some provider's token usage may not return correctly, resulting in cost statistics of 0
    enable_streaming: bool = False

    # Intelligent stop detection configuration (similar to ApeAgent)
    consecutive_retries_threshold: Optional[int] = 3  # Consecutive prompt supplement threshold, None means not to check
    total_retries_threshold: Optional[int] = None  # Total retries threshold, None means not to check

    def model_post_init(self, __context) -> None:
        """Post-initialization processing: ensure relay mode and streaming configuration correct"""
        # Claude Code uses internal relay, all LLMConfig should enable relay_mode
        # relay_mode allows empty return (e.g. edge case of max_tokens=1), avoid MalformedResponseError
        self.llm_config.relay_mode = True

        # Apply scaffold-level streaming configuration to llm_config
        self.llm_config.streaming = self.enable_streaming

        if self.fast_llm_config:
            self.fast_llm_config.relay_mode = True
            self.fast_llm_config.streaming = self.enable_streaming
