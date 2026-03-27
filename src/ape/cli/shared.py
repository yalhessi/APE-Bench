"""Shared parser and builder helpers for interactive agent CLIs."""

from __future__ import annotations

import argparse
import importlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from ape.cli.registry import AgentCliSpec, get_agent_cli_spec
from ape.cli.task_input import create_ape_agent_task_input_ui, prompt_for_task_data
from ape.cli.task_session import INTERNAL_CLI_TASK_TYPES
from ape.scaffolds.skills import normalize_skills_config_paths
from ape.tasks.base import create_task_from_data, list_task_types
from ape.utils import deep_merge, load_yaml, parse_cli_args


@dataclass(frozen=True)
class PreparedAgentRun:
    """Prepared CLI configuration and task objects."""

    config: Any
    task: Any
    args: argparse.Namespace
    remaining_args: list[str]
    uses_registered_task: bool


def _ensure_task_registry_initialized() -> None:
    """Import the tasks package so built-in task types are registered."""
    import ape.tasks  # noqa: F401


def _import_task_modules(task_modules: Sequence[str]) -> None:
    """Import user-specified task modules before task lookup."""
    for module_path in task_modules:
        importlib.import_module(module_path)


def _list_public_task_types() -> list[str]:
    """Return registered task types excluding internal CLI-only wrappers."""
    return [task_type for task_type in list_task_types() if task_type not in INTERNAL_CLI_TASK_TYPES]


def get_registered_task_types(task_modules: Sequence[str] = ()) -> list[str]:
    """Return all registered task types visible to the CLI."""
    _ensure_task_registry_initialized()
    _import_task_modules(task_modules)
    return _list_public_task_types()


def print_registered_task_types(task_modules: Sequence[str] = ()) -> None:
    """Print registered task types for interactive CLI discovery."""
    task_types = get_registered_task_types(task_modules)
    print("Registered task types:")
    for task_type in task_types:
        print(f"  - {task_type}")


def _add_model_and_logging_arguments(parser: argparse.ArgumentParser, spec: AgentCliSpec) -> None:
    """Attach model and logging flags shared by chat and registered-task modes."""
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        help="Initial prompt message (default: start interactive dialog)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=spec.model_help,
    )
    parser.add_argument(
        "--log-level",
        "--log_level",
        dest="log_level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Set logging level (default: WARNING to reduce noise)",
    )


def configure_agent_parser(parser: argparse.ArgumentParser, spec: AgentCliSpec) -> argparse.ArgumentParser:
    """Attach free-form chat arguments to an agent parser."""
    parser.add_argument(
        "--workspace",
        "-w",
        type=str,
        help="Workspace path (default: current directory)",
    )
    _add_model_and_logging_arguments(parser, spec)
    parser.add_argument(
        "--verify_commit_hash",
        type=str,
        help="Git commit hash for target workspace (enables get_workspace for verification)",
    )
    parser.add_argument(
        "--verify_repo_url",
        type=str,
        help="Git repository URL for target workspace",
    )
    parser.add_argument(
        "--verify_default_target",
        type=str,
        help="Default target directory for target workspace (e.g., Mathlib)",
    )
    parser.add_argument(
        "--retrieve_commit_hash",
        type=str,
        default=spec.retrieve_commit_hash_default,
        help="Git commit hash for reference workspace (used by LeanRetrieve tools)",
    )
    parser.add_argument(
        "--retrieve_repo_url",
        type=str,
        default=spec.retrieve_repo_url_default,
        help="Git repository URL for reference workspace",
    )
    parser.add_argument(
        "--retrieve_default_target",
        type=str,
        default=spec.retrieve_default_target_default,
        help="Default target directory for reference workspace (e.g., Mathlib)",
    )

    if spec.add_agent_arguments is not None:
        spec.add_agent_arguments(parser)

    parser.set_defaults(agent_spec=spec)
    return parser


def configure_registered_task_parser(
    parser: argparse.ArgumentParser,
    spec: AgentCliSpec,
    task_modules: Sequence[str] = (),
) -> argparse.ArgumentParser:
    """Attach registered-task arguments to an agent parser."""
    parser.add_argument(
        "--task-module",
        "--task_modules",
        dest="task_modules",
        action="append",
        default=[],
        help="Import an extra task module before task lookup (can be repeated)",
    )
    parser.add_argument(
        "registered_task",
        nargs="?",
        choices=get_registered_task_types(task_modules),
        help="Registered task type to run",
    )
    parser.add_argument(
        "--task-file",
        type=str,
        help="Path to a JSON or JSONL file containing one or more task records",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Task ID to select when --task-file or --task-data-json contains multiple tasks",
    )
    parser.add_argument(
        "--task-index",
        type=int,
        help="0-based task index to select when --task-file or --task-data-json contains multiple tasks",
    )
    parser.add_argument(
        "--task-data-json",
        type=str,
        help="Inline JSON object containing the task data for the selected registered task",
    )
    _add_model_and_logging_arguments(parser, spec)

    if spec.add_agent_arguments is not None:
        spec.add_agent_arguments(parser)

    parser.set_defaults(agent_spec=spec)
    return parser


def create_standalone_agent_parser(spec: AgentCliSpec, prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Create a parser for a single agent alias entrypoint."""
    parser = argparse.ArgumentParser(
        prog=prog or spec.command_name,
        description=spec.description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=spec.epilog,
    )
    return configure_agent_parser(parser, spec)


def create_registered_task_agent_parser(
    spec: AgentCliSpec,
    task_modules: Sequence[str] = (),
    prog: Optional[str] = None,
) -> argparse.ArgumentParser:
    """Create a parser for a single agent's registered-task mode."""
    parser = argparse.ArgumentParser(
        prog=prog or spec.command_name,
        description=f"{spec.description} (registered task mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_registered_task_epilog(spec),
    )
    return configure_registered_task_parser(parser, spec, task_modules=task_modules)


def _build_registered_task_epilog(spec: AgentCliSpec) -> str:
    """Build a short epilog for registered-task subcommands."""
    return f"""
Registered Task Examples:
  ape task {spec.command_name} lean_pr_review
  ape task {spec.command_name} --task-module examples.arithmetic.task arithmetic
  ape task {spec.command_name} --task-file inputs/proof_pr_review/mathlib_pr_review_10tasks.jsonl --task-index 0 lean_pr_review
  ape task {spec.command_name} --task-module examples.arithmetic.task arithmetic --task-data-json '{{"expression":"2 + 2","expected_result":4.0}}'
"""


def _validate_remaining_overrides(remaining_args: Sequence[str]) -> None:
    """Ensure leftover CLI tokens are valid key=value config overrides."""
    invalid_args = [arg for arg in remaining_args if "=" not in arg]
    if invalid_args:
        formatted = ", ".join(invalid_args)
        raise ValueError(
            f"Unrecognized arguments: {formatted}. "
            "Only key=value configuration overrides are allowed after the parsed CLI flags."
        )


def _prepare_config_dict(
    spec: AgentCliSpec,
    args: argparse.Namespace,
    remaining_args: Sequence[str],
) -> dict[str, Any]:
    """Build scaffold configuration dict with batch-style YAML and CLI precedence."""
    _validate_remaining_overrides(remaining_args)

    config_dict = load_yaml(args.config) if getattr(args, "config", None) else {}
    if getattr(args, "config", None):
        normalize_skills_config_paths(
            config_dict,
            base_dir=Path(args.config).expanduser().resolve().parent,
        )

    cli_overrides = parse_cli_args(list(remaining_args)) or {}
    normalize_skills_config_paths(cli_overrides, base_dir=Path.cwd())
    if cli_overrides:
        config_dict = deep_merge(config_dict, cli_overrides)

    if spec.apply_argument_overrides is not None:
        spec.apply_argument_overrides(config_dict, args)

    if spec.model_default is not None:
        llm_config = config_dict.setdefault("llm_config", {})
        if not llm_config.get("model_name"):
            llm_config["model_name"] = spec.model_default

    return config_dict


def _load_task_records_from_file(task_file: Path) -> list[dict[str, Any]]:
    """Load task records from JSON or JSONL."""
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found: {task_file}")

    if task_file.suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        with task_file.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                record = json.loads(stripped)
                if not isinstance(record, dict):
                    raise TypeError(
                        f"Line {line_number} in {task_file} must be a JSON object, got {type(record).__name__}"
                    )
                records.append(record)
        return records

    data = json.loads(task_file.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        return list(data)
    raise TypeError(f"{task_file} must contain a JSON object or a list of JSON objects")


def _select_task_record(
    records: Sequence[dict[str, Any]],
    *,
    source_label: str,
    task_id: Optional[str],
    task_index: Optional[int],
) -> dict[str, Any]:
    """Select a single task record from loaded data."""
    if not records:
        raise ValueError(f"No task records found in {source_label}")

    if task_id is not None and task_index is not None:
        raise ValueError("Use only one of --task-id or --task-index")

    if task_id is not None:
        for record in records:
            if record.get("task_id") == task_id:
                return dict(record)
        available_ids = [str(record.get("task_id")) for record in records if record.get("task_id")]
        preview = ", ".join(available_ids[:10]) if available_ids else "none"
        raise ValueError(
            f"Task ID '{task_id}' was not found in {source_label}. Available task_ids: {preview}"
        )

    if task_index is not None:
        if task_index < 0 or task_index >= len(records):
            raise IndexError(
                f"--task-index {task_index} is out of range for {source_label} (size={len(records)})"
            )
        return dict(records[task_index])

    if len(records) == 1:
        return dict(records[0])

    raise ValueError(
        f"{source_label} contains {len(records)} task records. Use --task-id or --task-index to choose one."
    )


def _normalize_task_data(
    raw_task_data: dict[str, Any],
    *,
    registered_task: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Normalize selected task data before task construction."""
    task_data = dict(raw_task_data)

    existing_task_type = task_data.get("task_type")
    if existing_task_type and existing_task_type != registered_task:
        raise ValueError(
            f"Selected task data has task_type={existing_task_type!r}, which does not match the requested task {registered_task!r}"
        )
    task_data["task_type"] = registered_task

    if not task_data.get("task_id"):
        if args.task_id:
            task_data["task_id"] = args.task_id
        elif args.task_index is not None:
            task_data["task_id"] = f"task_index_{args.task_index}"
        else:
            task_data["task_id"] = f"cli-task-{uuid.uuid4().hex[:8]}"

    return task_data


def _load_selected_task_data(
    registered_task: str,
    args: argparse.Namespace,
    *,
    task_input_ui: Any = None,
) -> dict[str, Any]:
    """Load the selected registered task from interactive input, inline JSON, or a task file."""
    if args.task_file and args.task_data_json:
        raise ValueError("Use only one of --task-file or --task-data-json")

    if not args.task_file and not args.task_data_json:
        if args.task_index is not None:
            raise ValueError("--task-index can only be used with --task-file or --task-data-json")
        return _normalize_task_data(
            prompt_for_task_data(registered_task, ui=task_input_ui),
            registered_task=registered_task,
            args=args,
        )

    if args.task_file:
        task_file = Path(args.task_file)
        records = _load_task_records_from_file(task_file)
        raw_task_data = _select_task_record(
            records,
            source_label=str(task_file),
            task_id=args.task_id,
            task_index=args.task_index,
        )
    else:
        payload = json.loads(args.task_data_json)
        if isinstance(payload, dict):
            raw_task_data = dict(payload)
        elif isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
            raw_task_data = _select_task_record(
                payload,
                source_label="--task-data-json",
                task_id=args.task_id,
                task_index=args.task_index,
            )
        else:
            raise TypeError("--task-data-json must contain a JSON object or a list of JSON objects")

    return _normalize_task_data(raw_task_data, registered_task=registered_task, args=args)


def prepare_agent_run(spec: AgentCliSpec, args: argparse.Namespace, remaining_args: Sequence[str]) -> PreparedAgentRun:
    """Build scaffold config and task objects for a free-form chat invocation."""
    config_dict = _prepare_config_dict(spec, args, remaining_args)

    task_config_overrides = config_dict.pop("task_config", {})
    cli_task_config = spec.task_config_class.model_validate(task_config_overrides)
    config_dict["task_config"] = cli_task_config
    config = spec.config_class.model_validate(config_dict)

    workspace_path = Path(args.workspace) if args.workspace else Path.cwd()
    task_data = spec.task_data_class(
        task_id=f"{spec.task_id_prefix}{uuid.uuid4().hex[:8]}",
        verify_commit_hash=args.verify_commit_hash,
        verify_repo_url=args.verify_repo_url,
        verify_default_target=args.verify_default_target,
        local_workspace_path=workspace_path,
        retrieve_commit_hash=args.retrieve_commit_hash,
        retrieve_repo_url=args.retrieve_repo_url,
        retrieve_default_target=args.retrieve_default_target,
    )
    task = spec.task_class(task_data, config)

    return PreparedAgentRun(
        config=config,
        task=task,
        args=args,
        remaining_args=list(remaining_args),
        uses_registered_task=False,
    )


def prepare_registered_task_run(
    spec: AgentCliSpec,
    args: argparse.Namespace,
    remaining_args: Sequence[str],
    *,
    task_input_ui: Any = None,
    before_interactive_task_input: Optional[Callable[[Any], None]] = None,
) -> PreparedAgentRun:
    """Build scaffold config and task objects for a registered-task invocation."""
    registered_task = args.registered_task
    if not registered_task:
        raise ValueError("No registered task type was selected")

    visible_task_types = get_registered_task_types(args.task_modules or [])
    if registered_task not in visible_task_types:
        available = ", ".join(visible_task_types)
        raise ValueError(f"Unknown registered task '{registered_task}'. Available: {available}")

    config_dict = _prepare_config_dict(spec, args, remaining_args)

    task_config_overrides = config_dict.pop("task_config", {})
    config = spec.config_class.model_validate(config_dict)
    uses_interactive_task_input = not args.task_file and not args.task_data_json
    if uses_interactive_task_input and before_interactive_task_input is not None:
        before_interactive_task_input(config)
    task_data = _load_selected_task_data(
        registered_task,
        args,
        task_input_ui=task_input_ui,
    )
    task = create_task_from_data(task_data, config, task_config_overrides)

    return PreparedAgentRun(
        config=config,
        task=task,
        args=args,
        remaining_args=list(remaining_args),
        uses_registered_task=True,
    )


def execute_agent_cli(spec: AgentCliSpec, args: argparse.Namespace, remaining_args: Sequence[str]) -> int:
    """Build and launch a free-form interactive agent CLI session."""
    prepared = prepare_agent_run(spec, args, remaining_args)
    return spec.launch(prepared.config, prepared.task, prepared.args)


def execute_registered_task_cli(spec: AgentCliSpec, args: argparse.Namespace, remaining_args: Sequence[str]) -> int:
    """Build and launch an interactive session for a registered task."""
    if not args.registered_task:
        print_registered_task_types(args.task_modules or [])
        return 0

    task_input_ui = None
    before_interactive_task_input = None

    if spec.command_name == "ape-agent" and not args.task_file and not args.task_data_json:
        task_input_ui = create_ape_agent_task_input_ui()

        def before_interactive_task_input(config) -> None:
            if not getattr(config, "show_welcome", True):
                return
            task_input_ui.display.show_welcome(f"Task Session ({args.registered_task})")
            args._ape_agent_welcome_shown = True

    prepared = prepare_registered_task_run(
        spec,
        args,
        remaining_args,
        task_input_ui=task_input_ui,
        before_interactive_task_input=before_interactive_task_input,
    )
    return spec.launch(prepared.config, prepared.task, prepared.args)


def run_agent_alias(command_name: str, argv: Optional[Sequence[str]] = None, prog: Optional[str] = None) -> int:
    """Run a standalone compatibility alias for an interactive agent CLI."""
    spec = get_agent_cli_spec(command_name)
    parser = create_standalone_agent_parser(spec, prog=prog or spec.alias_name)
    args, remaining_args = parser.parse_known_args(argv)
    return execute_agent_cli(spec, args, remaining_args)
