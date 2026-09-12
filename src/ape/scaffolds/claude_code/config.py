"""
Claude Code Scaffold Configuration Models

Claude Code Scaffold configuration models, inherit from BaseScaffoldConfig and add specific configurations.
"""

from typing import List, Optional
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

    # --- containment -----------------------------------------------------------------------
    #
    # This package's docstring said "Disables Bash commands". It did not: the scaffold set
    # `disallowed_tools = ["Explore"]` and nothing else, with `permission_mode` on
    # `bypassPermissions`, so Bash, WebFetch, WebSearch, Task, Write and Edit all ran
    # auto-approved. A stale docstring that reads like containment is worse than none.
    #
    # It matters here because this scaffold is being pointed at the Mathlib review task, where
    # the agent must not see the future. Verified reachable from a review workspace with the
    # defaults above: the per-workspace `.git` is deleted, but the workspace sits inside the
    # APE-Bench repository, so git resolves upward and `git show HEAD:inputs/.../gold/` is the
    # answer key; `data/code_execute/repos/mathlib4/source` is a real clone whose HEAD is
    # months past every episode and contains the squash-merged form of the PR under review;
    # and the PR number is in the prompt, so WebFetch of the GitHub page returns the maintainer
    # comments the obligations were derived from.
    #
    # None of these are hypothetical and none are closed by the prompt. They are closed by not
    # granting the capability.

    #: Tools the agent may use at all. `None` leaves the SDK's full built-in set, which is the
    #: old behaviour. A review task sets this to the read-only set; note that dropping Bash is
    #: not a handicap relative to the scheduled arms, whose grant
    #: (`DEFAULT_REVIEW_TOOLS`) is read-only and has no shell either -- granting one here would
    #: hand the baseline a capability class the incumbent lacks, breaking the comparison in the
    #: same motion that it breaks containment.
    tools: Optional[List[str]] = None

    #: Tools refused even if `tools` would allow them. Applied on top of the scaffold's own
    #: `Explore` entry rather than replacing it.
    disallowed_tools: List[str] = Field(default_factory=list)

    #: Which on-disk settings the SDK loads. Unset means *all* of them, and because cwd is
    #: inside this repository that pulled in APE-Bench's own `CLAUDE.md` and
    #: `.claude/rules/mathlib-review.md` -- which describe the gold layout and the retrieval
    #: cutoff -- plus `.claude/settings.json`, whose `UserPromptSubmit` hook injected the
    #: `[session]` line into the experiment every turn. `[]` loads none.
    setting_sources: Optional[List[str]] = None

    #: Ignore any MCP server not passed programmatically.
    strict_mcp_config: bool = False

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
