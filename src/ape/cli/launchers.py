"""Shared launch helpers for interactive agent CLI entrypoints."""

from __future__ import annotations

import asyncio
import importlib
import numbers
import signal
import sys
from typing import Optional, Type

from rich.console import Console

from ape.cli.task_session import is_internal_cli_task, merge_task_prompt
from ape.llm_clients.models import TokenUsage
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


def _coerce_int(value: object) -> int:
    """Normalize integer-like values used in session reports."""
    if isinstance(value, numbers.Integral):
        return int(value)
    return 0


def _coerce_float(value: object) -> float:
    """Normalize numeric values used in session reports."""
    if isinstance(value, numbers.Real):
        return float(value)
    return 0.0


def _get_session_token_usage(scaffold: object) -> Optional[TokenUsage]:
    """Fetch token usage from a scaffold when available."""
    usage_getter = getattr(scaffold, "_get_token_usage", None)
    if not callable(usage_getter):
        return None

    try:
        token_usage = usage_getter()
    except Exception:
        return None

    if token_usage is None:
        return None

    return token_usage


def _build_session_report_lines(token_usage: Optional[TokenUsage]) -> Optional[list[str]]:
    """Build minimal session summary lines for CLI users."""
    if token_usage is None:
        return None

    total_tokens = _coerce_int(getattr(token_usage, "total_tokens", None))
    total_cost = _coerce_float(getattr(token_usage, "total_cost", None))
    cached_total_cost = _coerce_float(getattr(token_usage, "cached_total_cost", None))

    return [
        f"Tokens: {total_tokens:,}",
        f"Cost: ${total_cost:.4f}",
        f"Cached Cost: ${cached_total_cost:.4f}",
    ]


def _build_managed_skill_report_lines(scaffold: object) -> Optional[list[str]]:
    """Summarize managed-skill availability and observed skill-tool usage."""
    managed_skills = getattr(scaffold, "managed_skills", None)
    skills = tuple(getattr(managed_skills, "skills", ()) or ())
    if not skills:
        return None

    session = None
    conversation_manager = getattr(scaffold, "conversation_manager", None)
    if conversation_manager is not None:
        session = getattr(conversation_manager, "conversation_session", None)
    if session is None:
        session = getattr(scaffold, "conversation_session", None)

    read_skill_calls = 0
    list_skills_calls = 0
    read_skill_paths: list[str] = []
    seen_paths: set[str] = set()
    if session is not None:
        for node in getattr(session, "nodes", []) or []:
            if getattr(node, "type", None) != "assistant":
                continue
            message = getattr(node, "message", None)
            for block in getattr(message, "content", []) or []:
                if getattr(block, "type", None) != "tool_use":
                    continue
                tool_name = getattr(block, "name", "") or ""
                if tool_name == "read_skill":
                    read_skill_calls += 1
                    block_input = getattr(block, "input", None) or {}
                    relative_path = "SKILL.md"
                    if isinstance(block_input, dict):
                        raw_relative_path = block_input.get("relative_path")
                        if isinstance(raw_relative_path, str) and raw_relative_path.strip():
                            relative_path = raw_relative_path.strip()
                    if relative_path not in seen_paths:
                        seen_paths.add(relative_path)
                        read_skill_paths.append(relative_path)
                elif tool_name == "list_skills":
                    list_skills_calls += 1

    total_skill_tool_calls = read_skill_calls + list_skills_calls
    skill_names = ", ".join(skill.name for skill in skills)

    report_lines = [
        f"Managed Skills: {skill_names}",
        f"Skill Tool Calls: {total_skill_tool_calls} (read_skill: {read_skill_calls}, list_skills: {list_skills_calls})",
    ]
    if read_skill_paths:
        report_lines.append(f"Skill References: {', '.join(read_skill_paths)}")

    return report_lines


def _print_external_session_report(token_usage: Optional[TokenUsage]) -> None:
    """Print a compact session summary for external scaffold sessions."""
    report_lines = _build_session_report_lines(token_usage)
    if not report_lines:
        return

    print("\nSession Report:", file=sys.stderr)
    for line in report_lines:
        print(f"  {line}", file=sys.stderr)


async def _finalize_scaffold_session(
    scaffold: object,
    existing_termination_result: Optional[object] = None,
    already_terminated: bool = False,
) -> Optional[TokenUsage]:
    """Terminate and clean up an interactive scaffold, then return token usage."""
    termination_result = existing_termination_result

    if not already_terminated and termination_result is None and getattr(scaffold, "task", None) is not None:
        terminate = getattr(scaffold, "terminate", None)
        if callable(terminate):
            try:
                termination_result = await terminate()
            except Exception:
                termination_result = None

    token_usage = getattr(termination_result, "token_usage", None)
    if token_usage is None:
        token_usage = _get_session_token_usage(scaffold)

    cleanup = getattr(scaffold, "_cleanup", None)
    if callable(cleanup):
        try:
            await cleanup()
        except Exception:
            pass

    return token_usage


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
    try:
        await scaffold.run_interactive_session(
            task=cli_task,
            initial_prompt=initial_prompt,
            oneshot_mode=oneshot_mode,
        )
    finally:
        managed_skill_report_lines = _build_managed_skill_report_lines(scaffold)
        token_usage = await _finalize_scaffold_session(scaffold)
        report_lines = _build_session_report_lines(token_usage) or []
        if managed_skill_report_lines:
            report_lines.extend(managed_skill_report_lines)
        if report_lines:
            display.show_tree_section(
                "Session Report",
                report_lines,
                accent_color=colors.accent_green,
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
    termination_completed = False
    termination_result = None

    async def termination_callback(_result) -> None:
        nonlocal termination_requested, termination_completed, termination_result
        if termination_requested:
            return
        termination_requested = True
        termination_result = await scaffold.terminate()
        termination_completed = True

    try:
        await scaffold.solve(
            task=cli_task,
            termination_callback=termination_callback,
            orchestrator_id="cli",
            attempt_path=None,
        )
    finally:
        token_usage = await _finalize_scaffold_session(
            scaffold,
            existing_termination_result=termination_result,
            already_terminated=termination_completed,
        )

    _print_external_session_report(token_usage)
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
