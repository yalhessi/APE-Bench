"""Shared launch helpers for interactive agent CLI entrypoints."""

from __future__ import annotations

import asyncio
import importlib
import signal
import sys
from typing import Optional, Type

from rich.console import Console

from ape.cli.task_session import is_internal_cli_task, merge_task_prompt
from ape.scaffolds.base import BaseScaffold


def register_signal_handlers(handler) -> None:
    """Register signal handlers for interactive CLI sessions."""
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def rich_signal_handler(_signum, _frame) -> None:
    """Handle interactive signals using rich console output."""
    console = Console()
    console.print("Shutting down gracefully...", style="gray")
    sys.exit(0)


def stderr_signal_handler(_signum, _frame) -> None:
    """Handle interactive signals using stderr output."""
    print("\nShutting down gracefully...", file=sys.stderr)
    sys.exit(0)


async def run_ape_agent_cli_session(
    config,
    cli_task,
    user_prompt: Optional[str],
    oneshot_mode: bool,
    welcome_already_shown: bool = False,
) -> None:
    """Run the APE-Agent interactive CLI session."""
    from ape.scaffolds.ape_agent.cli.ui.colors import colors
    from ape.scaffolds.ape_agent.cli.ui.display import CLIDisplay
    from ape.scaffolds.ape_agent.scaffold import ApeAgentScaffold

    console = Console()
    display = CLIDisplay(console)
    task_prompt = None
    if not is_internal_cli_task(cli_task):
        task_prompt = await cli_task.create_user_prompt()
    initial_prompt = merge_task_prompt(task_prompt, user_prompt)
    verify_commit_hash = getattr(cli_task.data, "verify_commit_hash", None)
    local_workspace_path = getattr(cli_task.data, "local_workspace_path", None)
    target_workspace = getattr(cli_task.data, "target_workspace", None)

    if is_internal_cli_task(cli_task):
        subtitle = "Interactive Workspace Session"
    else:
        subtitle = f"Task Session ({cli_task.task_type})"

    if config.show_welcome and not welcome_already_shown:
        display.show_welcome(subtitle)
    if config.show_help_on_start:
        display.show_quick_help()

    workspace_label: str
    if verify_commit_hash:
        workspace_label = f"Git ({verify_commit_hash[:8]}...)"
    elif local_workspace_path:
        workspace_label = str(local_workspace_path)
    elif target_workspace is not None and getattr(target_workspace, "commit_hash", None):
        workspace_label = f"{target_workspace.name} ({target_workspace.commit_hash[:8]}...)"
    else:
        from pathlib import Path

        workspace_label = str(Path.cwd())

    display.show_tree_section(
        "Session",
        [
            f"Model: {config.llm_config.model_name}",
            f"Workspace: {workspace_label}",
        ],
        accent_color=colors.accent_cyan,
        margin_top=not (config.show_welcome and not welcome_already_shown),
    )

    if initial_prompt:
        display.show_message_preview(
            "User Prompt",
            initial_prompt,
            accent_color=colors.accent_blue,
        )

    cli_task._cli_force_tool_use = not is_internal_cli_task(cli_task)
    scaffold = ApeAgentScaffold()
    scaffold.progress_callback = display.show_status
    await scaffold.run_interactive_session(
        task=cli_task,
        initial_prompt=initial_prompt,
        oneshot_mode=oneshot_mode,
    )


def launch_ape_agent(config, cli_task, args) -> int:
    """Launch the APE-Agent interactive CLI."""
    register_signal_handlers(rich_signal_handler)
    try:
        asyncio.run(
            run_ape_agent_cli_session(
                config=config,
                cli_task=cli_task,
                user_prompt=args.prompt,
                oneshot_mode=args.oneshot_mode,
                welcome_already_shown=getattr(args, "_ape_agent_welcome_shown", False),
            )
        )
        return 0
    except KeyboardInterrupt:
        console = Console()
        console.print("Session interrupted by user", style="dim")
        return 0
    except Exception:
        console = Console()
        console.print("Error: Execution failed", style="red")
        import traceback

        console.print("Traceback:", style="dim")
        console.print(traceback.format_exc())
        return 1


async def run_external_scaffold_cli_session(
    scaffold_cls: Type[BaseScaffold],
    cli_task,
    prompt: Optional[str],
    extra_args: list[str],
) -> int:
    """Launch an external CLI-backed scaffold session."""
    cli_task._cli_prompt = prompt
    cli_task._cli_extra_args = extra_args or []

    scaffold = scaffold_cls()
    scaffold.progress_callback = lambda message: print(f"[setup] {message}", file=sys.stderr)
    termination_requested = False

    async def termination_callback(_result) -> None:
        nonlocal termination_requested
        if termination_requested:
            return
        termination_requested = True
        await scaffold.terminate()

    await scaffold.solve(
        task=cli_task,
        termination_callback=termination_callback,
        orchestrator_id="cli",
        attempt_path=None,
    )
    return 0


def _load_scaffold_class(module_path: str, class_name: str) -> Type[BaseScaffold]:
    """Load a scaffold class lazily to avoid importing optional backends eagerly."""
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def build_external_launcher(scaffold_module: str, scaffold_class_name: str):
    """Create a launcher for CLI-backed external scaffold wrappers."""

    def _launch(_config, cli_task, args) -> int:
        register_signal_handlers(stderr_signal_handler)
        try:
            scaffold_cls = _load_scaffold_class(scaffold_module, scaffold_class_name)
            return asyncio.run(
                run_external_scaffold_cli_session(
                    scaffold_cls=scaffold_cls,
                    cli_task=cli_task,
                    prompt=args.prompt,
                    extra_args=getattr(args, "extra_args", []) or [],
                )
            )
        except KeyboardInterrupt:
            print("\nSession interrupted by user", file=sys.stderr)
            return 130
        except Exception:
            import traceback

            print(f"Failed to start CLI session:\n{traceback.format_exc()}", file=sys.stderr)
            return 1

    return _launch
