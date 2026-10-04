"""
Claude Code Scaffold Configuration Models

Claude Code Scaffold configuration models, inherit from BaseScaffoldConfig and add specific configurations.
"""

import re
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import Field, model_validator
from ape.scaffolds.config import BaseScaffoldConfig
from ape.llm_clients.config import LLMConfig

#: A Claude model's full API name. An alias (`opus`, `sonnet`, `opus[1m]`, `best`) resolves to
#: whatever the CLI release maps it to, so a run pinned by one names no model.
CLAUDE_MODEL_NAME = re.compile(r"^claude-[a-z]+-\d+(-\d+)*$")


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

    #: Refuse, by a PreToolUse hook, any built-in tool call whose path leaves the attempt's
    #: workspace, and write `containment_audit.json` from the session transcript after it
    #: (`containment.py`). The grant above names which tools exist; this bounds where they
    #: reach, which `dontAsk` was never shown to do. Batch mode only.
    contain_to_workspace: bool = False

    # --- the subscription route ------------------------------------------------------------
    #
    # With `llm_config.model_name: null` no relay starts, and the CLI reaches Anthropic on its
    # own login. These three name what that session is, so they sit in the scaffold config and
    # therefore in the run plan's digest. On the relay route all three stay unset: the model
    # and its reasoning are `llm_config`'s, served by the relay.

    #: The Claude model the CLI runs, by its full name. Required on the subscription route,
    #: where the CLI's default model would otherwise be whatever its release ships with.
    claude_model: Optional[str] = None

    #: The CLI release, run from `data/resources/claude-<version>-linux-x64`. Unset means the
    #: SDK's bundled CLI (2.1.139 with claude-agent-sdk 0.1.81), which refuses claude-opus-5-5
    #: ("version 2.1.280 or newer is required") and takes Opus 5 and 4.8 for 200K-context
    #: models when they are 1M, so it compacts a long session early.
    cli_version: Optional[str] = None

    #: The CLI's `--effort`. A launching Claude Code session exports its own `CLAUDE_EFFORT`,
    #: which the SDK passes to the child; this pins the reviewer's instead.
    effort: Optional[Literal["low", "medium", "high", "xhigh", "max"]] = None

    @property
    def subscription_route(self) -> bool:
        """Whether this session runs a Claude model on the CLI's own login, with no relay."""
        return self.claude_model is not None

    def resolved_cli_path(self) -> Optional[Path]:
        """The pinned CLI binary, or None for the SDK's bundled one."""
        if self.cli_version is None:
            return None
        from ape.utils.project import PROJECT_ROOT

        return PROJECT_ROOT / "data" / "resources" / f"claude-{self.cli_version}-linux-x64"

    @model_validator(mode="after")
    def _a_subscription_session_names_itself(self) -> "ClaudeCodeConfig":
        """Refuse a subscription-route config that leaves what the session is to the CLI."""
        if self.claude_model is None:
            if self.effort is not None:
                raise ValueError(
                    "effort is the Claude model's on the subscription route; on the relay route "
                    "the backend's reasoning is set in llm_config")
            return self
        problems = []
        if self.llm_config.model_name is not None:
            problems.append(
                f"llm_config.model_name is {self.llm_config.model_name!r}, which starts the "
                "relay and serves that model instead; set it to null")
        if not CLAUDE_MODEL_NAME.match(self.claude_model):
            problems.append(f"claude_model {self.claude_model!r} is not a full model name "
                            "(an alias moves with the CLI release)")
        if self.cli_version is None:
            problems.append("cli_version is unset, so the SDK's bundled CLI would run")
        if self.effort is None:
            problems.append("effort is unset, so the launching shell's CLAUDE_EFFORT or the "
                            "CLI's default would decide it")
        if not self.contain_to_workspace:
            problems.append("contain_to_workspace is off, so nothing bounds or audits where "
                            "the built-in tools reach")
        if self.setting_sources != []:
            problems.append("setting_sources is not [], so on-disk settings, CLAUDE.md and "
                            "hooks would load into the session")
        if not self.strict_mcp_config:
            problems.append("strict_mcp_config is off, so the login's claude.ai connectors "
                            "attach and announce themselves into the reviewer's context")
        if problems:
            raise ValueError("claude_model set (the subscription route), but: "
                             + "; ".join(problems))
        return self

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
