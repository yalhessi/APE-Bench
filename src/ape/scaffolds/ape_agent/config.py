"""
APE Agent Scaffold Configuration Module.

Provides configuration models for the APE Agent scaffold.
"""

from typing import Literal, Optional
from ape.scaffolds.config import BaseScaffoldConfig


class ApeAgentConfig(BaseScaffoldConfig):
    """APE Agent Scaffold configuration."""

    # Scaffold type identifier
    scaffold_type: str = "ape_agent"

    #: Where the session's system text (the preamble, then the task's brief) is delivered.
    #: "system", the default and every run before 2026-10-03: a system message. "user": no system
    #: message; the same text opens the first user message, where the Claude Code and Codex
    #: harnesses already put the preamble. Added to test whether an open-weight reviewer does
    #: better without a system role (results/pr_review_v5/probes/local-unlock-2026-10-03/). Part
    #: of the scaffold config, so of the run plan.
    system_prompt_role: Literal["system", "user"] = "system"

    # LLM streaming configuration (disabled by default for accurate token usage)
    enable_streaming: bool = False

    # Intelligent stop detection thresholds
    consecutive_retries_threshold: Optional[int] = 3
    total_retries_threshold: Optional[int] = None

    def model_post_init(self, __context) -> None:
        """Apply streaming configuration to llm_config."""
        self.llm_config.streaming = self.enable_streaming
