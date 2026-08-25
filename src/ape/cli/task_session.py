"""Helpers for distinguishing free-form CLI sessions from registered task sessions."""

from __future__ import annotations

from typing import Optional


INTERNAL_CLI_TASK_TYPES = {
    "cli_interactive",
    "claude_code_cli",
    "codex_cli",
}


def is_internal_cli_task(task) -> bool:
    """Return whether a task is one of the interactive CLI wrapper tasks."""
    return getattr(task, "task_type", None) in INTERNAL_CLI_TASK_TYPES


def merge_task_prompt(task_prompt: Optional[str], user_prompt: Optional[str]) -> Optional[str]:
    """Merge a task-generated prompt with optional user-supplied guidance."""
    clean_task_prompt = task_prompt.strip() if isinstance(task_prompt, str) else ""
    clean_user_prompt = user_prompt.strip() if isinstance(user_prompt, str) else ""

    if clean_task_prompt and clean_user_prompt:
        return (
            f"{clean_task_prompt}\n\n"
            f"{'=' * 80}\n\n"
            f"Additional user instructions:\n{clean_user_prompt}"
        )
    if clean_task_prompt:
        return clean_task_prompt
    if clean_user_prompt:
        return clean_user_prompt
    return None
