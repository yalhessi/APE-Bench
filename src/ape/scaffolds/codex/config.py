"""
Codex Scaffold Configuration Models

Codex Scaffold configuration models, inherit from BaseScaffoldConfig and add Codex-specific configurations.
"""

from typing import List, Optional
from pydantic import Field

from ape.scaffolds.config import BaseScaffoldConfig


class CodexConfig(BaseScaffoldConfig):
    """Codex Scaffold configuration, inherit from BaseScaffoldConfig and add specific configurations"""

    # Scaffold type identifier
    scaffold_type: str = "codex"

    # MCP server name prefix (includes trailing __). The server is registered as `core`, which
    # Codex presents as the namespace `mcp__core`, and the relay flattens its tools to
    # `mcp__core__<tool>`: the names Claude Code gives the same tools, so the task's prompt text
    # is the same under both.
    mcp_server_name: str = "mcp__core__"

    # Codex specific configurations
    mcp_server_startup_timeout: float = 2.0
    # NOTE: Model selection is driven by llm_config (canonical model name) to match Claude Code behavior.
    use_native_tools: bool = False  # Whether to use our native MCP tools (file_system, bash_execute); if False, use Codex builtin tools instead

    #: The model name Codex is told, which selects its own per-model prompt and tool behaviour
    #: from its catalog. Unset: `llm_config.model_name` in OpenAI's spelling (`gpt_5.2` ->
    #: `gpt-5.2`). The relay calls `llm_config`'s model whatever this says.
    codex_model: Optional[str] = None

    #: Codex features switched off (`[features]` in the attempt's config.toml). A review sets
    #: `shell_tool` and `unified_exec`, which leaves Codex no shell, plus the browser, computer-use,
    #: image, apps, plugin, multi-agent, memories and goals features.
    disabled_features: List[str] = Field(default_factory=list)

    #: Codex's own tools the relay passes to the model, by name. `None` passes all of them. The MCP
    #: server's tools always pass. A review keeps `update_plan` (Claude Code's TodoWrite): Codex
    #: offers `view_image`, `request_user_input` and MCP-resource tools with no way to disable them.
    relayed_builtin_tools: Optional[List[str]] = None

    #: List the MCP server's tools in every request, as Claude Code does, instead of behind
    #: Codex's `tool_search`, which its catalog turns on for gpt-5.2. Done with a per-attempt copy
    #: of the catalog entry with `supports_search_tool` off; everything else in it is Codex's.
    list_mcp_tools_upfront: bool = True

    # Sandbox and permission configurations, written to the attempt's config.toml
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
