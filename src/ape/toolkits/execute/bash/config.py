"""Bash Execute Tool Configuration."""

from pydantic import BaseModel, ConfigDict


class BashExecuteToolConfig(BaseModel):
    """Bash execution configuration - simple and minimal."""
    model_config = ConfigDict(extra='forbid')

    timeout: float = 300.0  # seconds
    max_output_chars: int = 10000  # maximum characters of output to return
