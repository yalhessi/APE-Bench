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

    # LLM streaming configuration (disabled by default for accurate token usage)
    enable_streaming: bool = False

    # Intelligent stop detection thresholds
    consecutive_retries_threshold: Optional[int] = 3
    total_retries_threshold: Optional[int] = None

    #: The preamble a batch session opens with (`ape.scaffolds.prompts.BATCH_PREAMBLES`).
    #: "standard" is what every run before 2026-10-01 saw; "plain" drops its imperatives (text
    #: "accomplishes NOTHING", batch every call, submit only when "COMPLETED and VALIDATED") for
    #: a task whose own contract says how to work. Part of the scaffold config, so of the plan.
    batch_preamble: Literal["standard", "plain"] = "standard"

    #: False drops the system prompt's `<environment>` section (scratch as a place for "rapid
    #: iteration and experimentation", target as the verification library) unless it carries
    #: blocked-path notes. True, the default, is every run before 2026-10-01.
    workspace_environment: bool = True

    def model_post_init(self, __context) -> None:
        """Apply streaming configuration to llm_config."""
        self.llm_config.streaming = self.enable_streaming
