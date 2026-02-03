"""
Ape Agent CLI - Main entry point with new architecture

New architecture design:
1. Use new Task-based architecture
2. Simplify main.py responsibilities: only handle CLI argument parsing and Task creation
3. All interaction logic moved to scaffold
4. Completely eliminate interface.py layer
"""

import argparse
import asyncio
import sys
import signal
from typing import Optional
from rich.console import Console

from .config import ApeAgentCLIConfig
from .task import CLITask
from ..scaffold import ApeAgentScaffold
from ape.utils import parse_cli_args


def handle_signal(_signum, _frame):
    """Handle signals (Ctrl+C etc.)"""
    console = Console()
    console.print("Shutting down gracefully...", style="gray")
    sys.exit(0)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Ape Agent CLI - Interactive AI Assistant for Formal Mathematics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
An AI assistant based on dialogue, specialized for Lean theorem proving and formal mathematics.

Configuration Override Examples (use Python literal syntax):
  python -m ape.scaffolds.ape_agent.cli.main --workspace /path/to/workspace llm_config.model_name=gpt_5_mini
  python -m ape.scaffolds.ape_agent.cli.main --prompt "Help me prove theorem X" llm_config.temperature=0.7
  python -m ape.scaffolds.ape_agent.cli.main llm_config.max_tokens=8000
  python -m ape.scaffolds.ape_agent.cli.main llm_config.streaming=False
  python -m ape.scaffolds.ape_agent.cli.main --log_level WARNING  # Reduce log output (default)
  python -m ape.scaffolds.ape_agent.cli.main --log_level DEBUG    # Full debug logging

Workspace and Retrieve Tool Examples:
  python -m ape.scaffolds.ape_agent.cli.main --workspace /path/to/lean/project  # Use local workspace
  python -m ape.scaffolds.ape_agent.cli.main --verify_commit_hash abc123 --verify_repo_url https://github.com/user/repo.git  # Use Git workspace
  python -m ape.scaffolds.ape_agent.cli.main  # Use current directory as workspace
        """
    )

    # runtime parameters (not in configuration)
    parser.add_argument(
        '--workspace', '-w',
        type=str,
        help='Workspace path (default: current directory)'
    )
    parser.add_argument(
        '--prompt', '-p',
        type=str,
        help='Initial prompt message (default: start interactive dialog)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt_5_mini',
        help='Model name to use (default: gpt_5_mini, overrides model in configuration)'
    )
    parser.add_argument(
        '--oneshot_mode',
        action='store_true',
        help='Exit after processing initial prompt'
    )
    parser.add_argument(
        '--log_level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='WARNING',
        help='Set logging level (default: WARNING to reduce noise)'
    )
    parser.add_argument(
        '--open_in_vscode',
        action='store_true',
        default=True,
        help='Open files in VS Code after editing (default: True, auto-disabled if not in VS Code terminal)'
    )
    # ===== Verify related parameters: control Target Workspace =====
    parser.add_argument(
        '--verify_commit_hash',
        type=str,
        help='Git commit hash for target workspace (enables get_workspace for verification)'
    )
    parser.add_argument(
        '--verify_repo_url',
        type=str,
        help='Git repository URL for target workspace'
    )
    parser.add_argument(
        '--verify_default_target',
        type=str,
        help='Default target directory for target workspace (e.g., Mathlib)'
    )

    # ===== Retrieve related parameters: create Reference Workspace for retrieval tool =====
    parser.add_argument(
        '--retrieve_commit_hash',
        type=str,
        default="2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
        help='Git commit hash for reference workspace (used by LeanRetrieve tools)'
    )
    parser.add_argument(
        '--retrieve_repo_url',
        default='https://github.com/leanprover-community/mathlib4.git',
        type=str,
        help='Git repository URL for reference workspace'
    )
    parser.add_argument(
        '--retrieve_default_target',
        type=str,
        default="Mathlib",
        help='Default target directory for reference workspace (e.g., Mathlib)'
    )

    return parser


def cli_main() -> None:
    """
    Ape Agent CLI - Interactive AI Assistant for Formal Mathematics
    Command line entry point - used for apea command

    All parameters are obtained from command-line arguments.
    """
    # parse command line arguments
    parser = create_argument_parser()
    args, remaining_args = parser.parse_known_args()

    # parse remaining arguments as configuration dictionary
    config_overrides = parse_cli_args(remaining_args)

    # extract parameters from args
    workspace = args.workspace
    initial_prompt = args.prompt
    model = args.model
    oneshot_mode = args.oneshot_mode
    log_level = args.log_level
    open_in_vscode = args.open_in_vscode
    verify_commit_hash = args.verify_commit_hash
    verify_repo_url = args.verify_repo_url
    verify_default_target = args.verify_default_target
    retrieve_commit_hash = args.retrieve_commit_hash
    retrieve_repo_url = args.retrieve_repo_url
    retrieve_default_target = args.retrieve_default_target

    # initialize configuration dictionary
    config_dict = config_overrides or {}

    # if --model parameter is provided, override configuration
    if model:
        llm_config = config_dict.setdefault('llm_config', {})
        llm_config['model_name'] = model

    # if --log-level parameter is provided, override configuration
    if log_level:
        config_dict['log_level'] = log_level

    # handle --open-in-vscode parameter
    if open_in_vscode:
        import os
        term_program = os.environ.get('TERM_PROGRAM', '')
        open_in_vscode_enabled = (term_program == 'vscode')
    else:
        open_in_vscode_enabled = False

    config_dict['open_in_vscode'] = open_in_vscode_enabled

    # create CLI task configuration (without workspace parameter, workspace passed through task.data)
    from .task import CLITaskConfig, CLITaskData, CLITask
    from pathlib import Path
    import uuid

    # extract task_config configuration overrides
    task_config_overrides = config_dict.pop('task_config', {})
    cli_task_config = CLITaskConfig.model_validate(task_config_overrides)

    # use configuration dictionary to create configuration instance
    config_dict['task_config'] = cli_task_config
    _config = ApeAgentCLIConfig.model_validate(config_dict)

    # ===== directly create TaskData (same design as Batch mode) =====
    # Batch mode: task_data = LeanProofEngineeringData(...); task = LeanProofEngineeringTask(task_data, config)
    # CLI mode: task_data = CLITaskData(...); cli_task = CLITask(task_data, config)

    # if workspace is not provided, default to current working directory
    if workspace is None:
        workspace = Path.cwd()

    task_data = CLITaskData(
        task_id=f"cli-{uuid.uuid4().hex[:8]}",
        verify_commit_hash=verify_commit_hash,
        verify_repo_url=verify_repo_url,
        verify_default_target=verify_default_target,
        local_workspace_path=Path(workspace),
        retrieve_commit_hash=retrieve_commit_hash,
        retrieve_repo_url=retrieve_repo_url,
        retrieve_default_target=retrieve_default_target
    )

    # create CLI task (same design as Batch mode)
    cli_task = CLITask(task_data, _config)

    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        # run new architecture CLI session
        asyncio.run(_run_cli_session_new_arch(
            config=_config,
            cli_task=cli_task,
            initial_prompt=initial_prompt,
            oneshot_mode=oneshot_mode
        ))

    except KeyboardInterrupt:
        console = Console()
        console.print("Session interrupted by user", style="dim")
        sys.exit(0)
    except Exception:
        console = Console()
        console.print("Error: Execution failed", style="red")
        import traceback
        console.print("Traceback:", style="dim")
        console.print(traceback.format_exc())
        sys.exit(1)


async def _run_cli_session_new_arch(
    config: ApeAgentCLIConfig,
    cli_task: 'CLITask',
    initial_prompt: Optional[str],
    oneshot_mode: bool,
) -> None:
    """
    Run new architecture CLI session

    Args:
        config: Pydantic configuration object (only contains system configuration)
        cli_task: created CLI task instance (contains task.data)
        initial_prompt: initial prompt message
        oneshot_mode: one-shot mode

    Design principles:
    - Config: describes system behavior (model, tools, logging, etc.).
    - TaskData: holds execution data (workspace path, Git info, etc.).
    - Matches batch mode design: task objects are pre-created and reused.
    """
    console = Console()

    # display startup information
    console.print(f"ℹ Model: {config.llm_config.model_name}", highlight=False)

    # display workspace information (from task.data)
    if cli_task.data.verify_commit_hash:
        console.print(f"ℹ Workspace: Git ({cli_task.data.verify_commit_hash[:8]}...)", highlight=False)
    elif cli_task.data.local_workspace_path:
        console.print(f"ℹ Workspace: {cli_task.data.local_workspace_path}", highlight=False)
    else:
        from pathlib import Path
        console.print(f"ℹ Workspace: {Path.cwd()}", highlight=False)

    if initial_prompt:
        console.print(f"ℹ Initial prompt: {initial_prompt}", highlight=False)
        console.print()

    # display welcome information (based on configuration)
    if config.show_welcome:
        _show_welcome(console)
    if config.show_help_on_start:
        _show_quick_help(console)

    try:
        
        # 2. create scaffold and run interactive session
        # scaffold.run_interactive_session() internally calls solve() to manage the setup workflow
        scaffold = ApeAgentScaffold()
        await scaffold.run_interactive_session(
            task=cli_task,
            initial_prompt=initial_prompt,
            oneshot_mode=oneshot_mode
        )
        
    except Exception:
        console.print("Failed to start CLI session", style="red")
        import traceback
        console.print(traceback.format_exc(), style="dim")
        raise


def _show_welcome(console: Console):
    """Display welcome information"""
    from rich.text import Text
    from .ui.colors import colors

    # title
    welcome_text = Text()
    welcome_text.append("APE Agent", style="bold")
    welcome_text.append(" — Automated Proof Engineering", style=colors.gray)
    console.print(welcome_text)
    console.print()

    # Commands section
    console.print("[bold]Commands[/bold]")
    console.print(f"  [{colors.accent_cyan}]/help[/{colors.accent_cyan}]      Show detailed help")
    console.print(f"  [{colors.accent_cyan}]/clear[/{colors.accent_cyan}]     Clear screen")
    console.print(f"  [{colors.accent_cyan}]/quit[/{colors.accent_cyan}]      Exit session")
    console.print()

    # Keyboard Controls section
    console.print("[bold]Keyboard Controls[/bold]")
    console.print(f"  [{colors.accent_yellow}]ESC[/{colors.accent_yellow}]        Interrupt AI response/tool execution and return to input")
    console.print(f"  [{colors.accent_yellow}]Ctrl+D[/{colors.accent_yellow}]     Exit system")
    console.print()


def _show_quick_help(console: Console):
    """Display quick help information"""
    from rich.text import Text
    from .ui.colors import colors
    
    help_text = Text()
    help_text.append("Quick Start:", style="bold")
    help_text.append("\n• Ask Ape Agent to help with theorem proving", style=colors.gray)
    help_text.append("\n• Try: ", style=colors.gray)
    help_text.append('"Help me prove that n + 0 = n in Lean"', style=colors.accent_green)
    help_text.append("\n• Try: ", style=colors.gray)
    help_text.append('"Create a Lean file for basic arithmetic theorems"', style=colors.accent_green)
    help_text.append("\n• Try: ", style=colors.gray)
    help_text.append('"Explain this Lean proof step by step"', style=colors.accent_green)
    help_text.append("\n\nCommands:", style="bold")
    help_text.append("\n• ", style=colors.gray)
    help_text.append("/help", style=colors.accent_cyan)
    help_text.append(" - Show all available commands", style=colors.gray)
    help_text.append("\n• ", style=colors.gray)
    help_text.append("/clear", style=colors.accent_cyan)
    help_text.append(" - Clear the screen", style=colors.gray)
    help_text.append("\n• ", style=colors.gray)
    help_text.append("/quit", style=colors.accent_cyan)
    help_text.append(" or ", style=colors.gray)
    help_text.append("/exit", style=colors.accent_cyan)
    help_text.append(" - Exit the session", style=colors.gray)
    help_text.append("\n\nKeyboard shortcuts:", style="bold")
    help_text.append("\n• Press ", style=colors.gray)
    help_text.append("ESC", style=colors.accent_yellow)
    help_text.append(" to interrupt AI response/tool execution and return to input", style=colors.gray)
    help_text.append("\n• Press ", style=colors.gray)
    help_text.append("Ctrl+D", style=colors.accent_yellow)
    help_text.append(" to exit\n", style=colors.gray)
    
    console.print(help_text)


if __name__ == '__main__':
    cli_main()
