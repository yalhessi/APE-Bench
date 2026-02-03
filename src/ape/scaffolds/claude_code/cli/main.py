#!/usr/bin/env python3
"""
Claude Code CLI - Main entry point

Design description:
Claude Code CLI is a simple wrapper for the official claude command, responsible for:
1. Starting MCP server (provide project tools: lean_verify, lean_retrieve, etc.)
2. Starting relay (model routing + conversation tracking)
3. Configuring environment variables (pointing to relay)
4. Calling external `claude` command

Difference from using `claude` command directly:
- cli/main.py: Automatically configure MCP + relay
- `claude` command: Manually configure

All UI interactions are handled by the external claude command.
"""

import argparse
import asyncio
import sys
import signal
from typing import Optional

from .config import ClaudeCodeCLIConfig
from .task import CLITask
from ..scaffold import ClaudeCodeScaffold
from ape.utils import parse_cli_args


def handle_signal(signum, frame):
    """Handle signals (Ctrl+C etc.)"""
    print("\nShutting down gracefully...", file=sys.stderr)
    sys.exit(0)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Claude Code CLI - Enhanced claude command with MCP and conversation tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Claude Code CLI is an enhanced version of the claude command line tool, providing:
- Automatically configure relay mode and conversation tracking
- Automatically configure MCP server
- Record complete conversation history

Examples:
  python -m ape.scaffolds.claude_code.cli.main --workspace /path/to/workspace
  python -m ape.scaffolds.claude_code.cli.main --prompt "Help me with this task"
  python -m ape.scaffolds.claude_code.cli.main --model deepseek_v3.1 --workspace .

Configuration Override (use Python literal syntax):
  python -m ape.scaffolds.claude_code.cli.main llm_config.temperature=0.7
  python -m ape.scaffolds.claude_code.cli.main llm_config.streaming=False
  python -m ape.scaffolds.claude_code.cli.main llm_config.max_tokens=8000
  python -m ape.scaffolds.claude_code.cli.main task_config.enabled_tools='["Read","Write"]'
        """
    )

    # Runtime parameters
    parser.add_argument(
        '--workspace', '-w',
        type=str,
        help='Workspace path (default: current directory)'
    )
    parser.add_argument(
        '--prompt', '-p',
        type=str,
        help='Initial prompt message (if not provided, enter interactive mode)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model name to use (default: None - use official Claude Code models, overrides model in configuration)'
    )
    parser.add_argument(
        '--log_level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='WARNING',
        help='Set logging level (default: WARNING to reduce noise)'
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

    # ===== Retrieve related parameters: create Reference Workspace for retrieval tools =====
    parser.add_argument(
        '--retrieve_commit_hash',
        type=str,
        help='Git commit hash for reference workspace (used by LeanRetrieve tools)'
    )
    parser.add_argument(
        '--retrieve_repo_url',
        type=str,
        help='Git repository URL for reference workspace'
    )
    parser.add_argument(
        '--retrieve_default_target',
        type=str,
        help='Default target directory for reference workspace (e.g., Mathlib)'
    )

    parser.add_argument(
        '--extra-arg',
        action='append',
        default=[],
        dest='extra_args',
        help='Extra arguments passed to claude command (can be repeated)'
    )

    return parser


def cli_main() -> None:
    """
    Claude Code CLI - Main entry point function
    Command line entry point - used for ape-claude command

    All parameters are obtained from command-line arguments.
    """
    # Parse command line arguments
    parser = create_argument_parser()
    args, remaining_args = parser.parse_known_args()

    # Parse remaining arguments as configuration dictionary
    config_overrides = parse_cli_args(remaining_args)

    # Extract parameters from args
    workspace = args.workspace
    prompt = args.prompt
    model = args.model
    log_level = args.log_level
    verify_commit_hash = args.verify_commit_hash
    verify_repo_url = args.verify_repo_url
    verify_default_target = args.verify_default_target
    retrieve_commit_hash = args.retrieve_commit_hash
    retrieve_repo_url = args.retrieve_repo_url
    retrieve_default_target = args.retrieve_default_target
    extra_args = args.extra_args

    # Initialize configuration dictionary
    config_dict = config_overrides or {}

    # Command line parameter overrides configuration
    # Only set model_name if model is provided (not None)
    # When model is None, use official Claude Code models (no relay)
    if model is not None:
        llm_config = config_dict.setdefault('llm_config', {})
        llm_config['model_name'] = model

    if log_level:
        config_dict['log_level'] = log_level

    # ===== New workspace processing strategy: completely separate verify and retrieve =====
    #
    # Design principles (consistent with ApeAgent):
    # 1. verify parameters → task.data.verify_* → Target Workspace (used for verification)
    # 2. retrieve parameters → task.data.retrieve_* → Reference Workspace (used for retrieval)
    # 3. --workspace → task.data.local_workspace_path → local Target Workspace
    # 4. All parameters are passed through task data, not internal config fields

    # Extract task_config configuration overrides
    task_config_overrides = config_dict.pop('task_config', {})

    # Create configuration instance (without workspace parameter, workspace passed through task.data)
    from .task import CLITaskConfig, CLITaskData, CLITask
    from pathlib import Path
    import uuid

    cli_task_config = CLITaskConfig.model_validate(task_config_overrides)
    config_dict['task_config'] = cli_task_config
    config = ClaudeCodeCLIConfig.model_validate(config_dict)

    # ===== Directly create TaskData (consistent with Batch mode and ApeAgent) =====
    # If workspace is not provided, use current working directory
    workspace_path = Path(workspace) if workspace else Path.cwd()

    task_data = CLITaskData(
        task_id=f"claude-cli-{uuid.uuid4().hex[:8]}",
        verify_commit_hash=verify_commit_hash,
        verify_repo_url=verify_repo_url,
        verify_default_target=verify_default_target,
        local_workspace_path=workspace_path,
        retrieve_commit_hash=retrieve_commit_hash,
        retrieve_repo_url=retrieve_repo_url,
        retrieve_default_target=retrieve_default_target
    )

    # Create CLI task (consistent with Batch mode)
    cli_task = CLITask(task_data, config)

    # Set signal handler
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        # Run CLI session (pass cli_task rather than config)
        exit_code = asyncio.run(_run_cli_session(
            config=config,
            cli_task=cli_task,
            prompt=prompt,
            extra_args=extra_args or []
        ))
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nSession interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception:
        import traceback
        print(f"Error: Execution failed\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


async def _run_cli_session(
    config: ClaudeCodeCLIConfig,
    cli_task: 'CLITask',
    prompt: Optional[str],
    extra_args: list[str]
) -> int:
    """
    Run CLI session

    Args:
        config: Pydantic configuration object (only contains system configuration)
        cli_task: Created CLI task instance (contains task.data)
        prompt: Initial prompt message
        extra_args: Extra arguments

    Returns:
        Exit code of claude command

    Design principles:
    - Consistent with Batch mode: task already created, directly use
    - Consistent with ApeAgent CLI: create task in main()
    """
    try:

        # Set CLI specific parameters to task's temporary attribute
        cli_task._cli_prompt = prompt
        cli_task._cli_extra_args = extra_args or []

        # Create scaffold and run CLI session
        scaffold = ClaudeCodeScaffold()
        await scaffold.solve(
            task=cli_task,
            termination_callback=lambda x: None,  # CLI does not need automatic termination
            orchestrator_id="cli",
            attempt_path=None
        )

        return 0  # Success exit

    except Exception:
        import traceback
        print(f"Failed to start CLI session:\n{traceback.format_exc()}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    cli_main()
