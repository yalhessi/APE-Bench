from pydantic import BaseModel
from ..config import ApeAgentConfig

class CLIEvaluationConfig(BaseModel):
    """CLI mode evaluation configuration."""

    lean_verify_timeout: int = 60  # Lean verification tool timeout (seconds)
    allow_sorries: bool = True

class ApeAgentCLIConfig(ApeAgentConfig):
    """Ape Agent CLI configuration.

    Inherits ApeAgentConfig (including complete BaseScaffoldConfig)
    and adds CLI-specific configuration parameters.
    """
    # CLI-specific evaluation configuration
    evaluation: CLIEvaluationConfig = CLIEvaluationConfig()

    # CLI mode special settings
    cli_interactive_mode: bool = True
    cli_show_welcome: bool = True
    cli_show_help_on_start: bool = False
    cli_auto_clear_screen: bool = False
    cli_confirm_dangerous_operations: bool = True

    # Log control
    cli_log_level: str = "WARNING"  # Default WARNING level