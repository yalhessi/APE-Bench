"""Top-level interactive CLI for APE agent scaffolds."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from ape.cli.registry import list_agent_cli_specs
from ape.cli.shared import (
    configure_agent_parser,
    configure_registered_task_parser,
    execute_agent_cli,
    execute_registered_task_cli,
)


def _collect_task_modules(argv: Sequence[str]) -> list[str]:
    """Collect repeated --task-module values before building the full parser."""
    task_modules: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in {"--task-module", "--task_modules"}:
            if index + 1 < len(argv):
                task_modules.append(argv[index + 1])
            index += 2
            continue

        for prefix in ("--task-module=", "--task_modules="):
            if token.startswith(prefix):
                task_modules.append(token[len(prefix):])
                break

        index += 1

    return task_modules


def create_argument_parser(task_modules: Optional[Sequence[str]] = None) -> argparse.ArgumentParser:
    """Create the top-level `ape` CLI parser."""
    parser = argparse.ArgumentParser(
        prog="ape",
        description="Unified interactive CLI for APE-Bench agents",
    )
    subparsers = parser.add_subparsers(dest="command")

    chat_parser = subparsers.add_parser(
        "chat",
        help="Start a free-form interactive agent session",
        description="Start an interactive or one-shot session with an APE-Bench agent scaffold.",
    )
    chat_subparsers = chat_parser.add_subparsers(dest="agent")

    task_parser = subparsers.add_parser(
        "task",
        help="Run a registered task with an agent scaffold",
        description="Run a registered task with an APE-Bench agent scaffold.",
    )
    task_subparsers = task_parser.add_subparsers(dest="agent")

    for spec in list_agent_cli_specs():
        chat_agent_parser = chat_subparsers.add_parser(
            spec.command_name,
            help=spec.help_text,
            description=spec.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=spec.epilog,
        )
        configure_agent_parser(chat_agent_parser, spec)

        task_agent_parser = task_subparsers.add_parser(
            spec.command_name,
            help=f"Run a registered task with {spec.command_name}",
            description=f"{spec.description} (registered task mode)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        configure_registered_task_parser(task_agent_parser, spec, task_modules=task_modules or [])

    return parser


def cli_main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the top-level interactive CLI."""
    argv_list = list(argv) if argv is not None else sys.argv[1:]
    parser = create_argument_parser(task_modules=_collect_task_modules(argv_list))
    args, remaining_args = parser.parse_known_args(argv_list)

    agent_spec = getattr(args, "agent_spec", None)
    if agent_spec is None:
        parser.print_help()
        return 1

    if args.command == "task":
        return execute_registered_task_cli(agent_spec, args, remaining_args)

    return execute_agent_cli(agent_spec, args, remaining_args)


if __name__ == "__main__":
    raise SystemExit(cli_main())
