"""
APE Agent Scaffold Configuration Module.

Provides configuration models for the APE Agent scaffold.
"""

from typing import Optional
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

    def model_post_init(self, __context) -> None:
        """Apply streaming configuration to llm_config."""
        self.llm_config.streaming = self.enable_streaming
