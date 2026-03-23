"""Isabelle verification tool configuration."""

from pydantic import ConfigDict, Field

from ..config import CodeExecuteToolConfig


class IsabelleVerifyToolConfig(CodeExecuteToolConfig):
    """Configuration for Isabelle theory verification via `isabelle process`."""

    model_config = ConfigDict(extra='forbid')

    timeout: float = Field(default=300.0, description="Verification timeout (seconds)")
    max_memory_gb: float = Field(default=8.0, description="Maximum memory usage (GB)")
    max_messages: int = Field(default=20, description="Maximum number of messages to return")
    isabelle_bin: str = Field(default="isabelle", description="Path to the Isabelle executable")
    quick_and_dirty: bool = Field(
        default=False,
        description="Run Isabelle in quick_and_dirty mode so `sorry` is accepted"
    )
