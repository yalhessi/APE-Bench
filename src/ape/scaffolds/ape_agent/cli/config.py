from ..config import ApeAgentConfig

class ApeAgentCLIConfig(ApeAgentConfig):
    """Ape Agent CLI configuration.

    Inherits ApeAgentConfig (including complete BaseScaffoldConfig)
    and adds CLI-specific configuration parameters.

    Note: CLI mode does not require evaluation config as it is interactive
    without automatic evaluation.
    """
    # CLI mode special settings
    interactive_mode: bool = True
    show_welcome: bool = True
    show_help_on_start: bool = False
    auto_clear_screen: bool = False
    confirm_dangerous_operations: bool = True

    # Log control
    log_level: str = "WARNING"  # Default WARNING level, ignores INFO and DEBUG logs

    # Retry configuration for CLI mode (overrides parent defaults)
    # CLI mode expects quick response and immediate feedback, no retries
    retry_max_attempts: int = 1  # No retry in CLI mode (1 attempt)