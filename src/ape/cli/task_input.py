"""Interactive task data collection for registered task types."""

from __future__ import annotations

import json
import types
from pathlib import Path
from typing import Any, Literal, Optional, Union, get_args, get_origin

from pydantic import BaseModel

from ape.cli.task_prefill import build_pr_review_task_data
from ape.tasks.base import get_task_class
from ape.tasks.models import WorkspaceInfo


SKIPPED_TASK_FIELDS = {
    "task_type",
    "task_id",
    "metadata",
    "global_index",
    "document_databases",
}

SKIPPED_WORKSPACE_FIELDS = {
    "path",
    "blocked_path_patterns",
    "read_only_path_patterns",
    "no_read_path_patterns",
}

MULTILINE_SENTINEL = "<<EOF"
MULTILINE_END_MARKER = "EOF"


class TaskInputUI:
    """Small presentation interface for interactive task prompts."""

    def show_collection_intro(self, task_type: str, info_lines: list[str]) -> None:
        raise NotImplementedError

    def show_group(self, field_path: str, model_name: str, description: str) -> None:
        raise NotImplementedError

    def prompt(self, prompt_text: str) -> str:
        raise NotImplementedError

    def show_error(self, message: str) -> None:
        raise NotImplementedError

    def show_multiline_intro(self, field_path: str) -> None:
        raise NotImplementedError


class PlainTaskInputUI(TaskInputUI):
    """Default text-based task input prompts."""

    def show_collection_intro(self, task_type: str, info_lines: list[str]) -> None:
        print(f"Collecting input for task type: {task_type}")
        for line in info_lines:
            print(line)

    def show_group(self, field_path: str, model_name: str, description: str) -> None:
        print(f"\n{field_path} ({model_name})")
        if description:
            print(f"  {description}")

    def prompt(self, prompt_text: str) -> str:
        return input(prompt_text)

    def show_error(self, message: str) -> None:
        print(message)

    def show_multiline_intro(self, field_path: str) -> None:
        print(f"Enter multi-line content for {field_path}. Finish with a line containing {MULTILINE_END_MARKER}.")


class ApeAgentRichTaskInputUI(TaskInputUI):
    """APE-Agent themed prompts for interactive task setup."""

    def __init__(self, console=None) -> None:
        from rich.console import Console

        from ape.scaffolds.ape_agent.cli.ui.colors import colors
        from ape.scaffolds.ape_agent.cli.ui.display import CLIDisplay

        self.console = console or Console()
        self.colors = colors
        self.display = CLIDisplay(self.console)

    def show_collection_intro(self, task_type: str, info_lines: list[str]) -> None:
        self.display.show_tree_section(
            "Task Setup",
            [f"Task type: {task_type}", *info_lines],
            accent_color=self.colors.accent_blue,
        )

    def show_group(self, field_path: str, model_name: str, description: str) -> None:
        lines = [description] if description else ["Fill in the nested task fields below."]
        self.display.show_tree_section(
            f"{field_path} ({model_name})",
            lines,
            accent_color=self.colors.accent_cyan,
            margin_bottom=False,
        )

    def prompt(self, prompt_text: str) -> str:
        from rich.text import Text

        prompt = Text()
        prompt.append("? ", style=self.colors.accent_blue)
        prompt.append(prompt_text)
        self.console.print(prompt, end="")
        return self.console.input("")

    def show_error(self, message: str) -> None:
        self.display.show_error(message)

    def show_multiline_intro(self, field_path: str) -> None:
        self.display.show_tree_section(
            "Multiline Input",
            [f"Enter content for {field_path}. Finish with a line containing {MULTILINE_END_MARKER}."],
            accent_color=self.colors.accent_yellow,
            margin_bottom=False,
        )


def create_ape_agent_task_input_ui(console=None) -> ApeAgentRichTaskInputUI:
    """Create the APE-Agent themed task input UI."""
    return ApeAgentRichTaskInputUI(console=console)


def prompt_for_task_data(task_type: str, ui: Optional[TaskInputUI] = None) -> dict[str, Any]:
    """Prompt for a task's data fields interactively."""
    prompt_ui = ui or PlainTaskInputUI()

    special_case_data = _prompt_special_task_data(task_type, prompt_ui)
    if special_case_data is not None:
        return special_case_data

    task_class = get_task_class(task_type)
    data_class = task_class.data_class
    if data_class is None:
        raise ValueError(f"Task class {task_class.__name__} does not define data_class")

    prompt_ui.show_collection_intro(
        task_type,
        [
            "Press Enter to accept a default or skip an optional field.",
            f"For multi-line string fields, enter {MULTILINE_SENTINEL} on the first line.",
        ],
    )

    return {
        "task_type": task_type,
        **_prompt_model_fields(data_class, ui=prompt_ui),
    }


def _prompt_special_task_data(task_type: str, ui: TaskInputUI) -> Optional[dict[str, Any]]:
    """Handle task-specific interactive flows."""
    if task_type != "lean_pr_review":
        return None

    ui.show_collection_intro(
        task_type,
        [
            "The remaining PR review fields will be fetched automatically from GitHub.",
            "You only need the PR URL and the commit SHA from the PR branch.",
        ],
    )

    pr_url = _prompt_required_text(
        ui,
        "pr_url",
        "GitHub pull request URL",
    )
    commit = _prompt_required_text(
        ui,
        "commit",
        "Commit SHA from the pull request branch",
    )
    return build_pr_review_task_data(pr_url=pr_url, commit=commit)


def _prompt_required_text(ui: TaskInputUI, field_name: str, description: str) -> str:
    """Prompt until the user provides a non-empty text value."""
    while True:
        raw = ui.prompt(f"{field_name} (required) - {description}: ").strip()
        if raw:
            return raw
        ui.show_error("This field is required.")


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    """Split Optional[T] into (T, True)."""
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1 and len(args) != len(get_args(annotation)):
            return args[0], True
    return annotation, False


def _field_default(field) -> Any:
    """Get a field default, resolving default_factory when present."""
    if getattr(field, "default_factory", None) is not None:
        return field.default_factory()
    return field.default


def _prompt_model_fields(
    model_cls: type[BaseModel],
    *,
    ui: TaskInputUI,
    prefix: str = "",
) -> dict[str, Any]:
    """Prompt for all fields in a Pydantic model."""
    values: dict[str, Any] = {}

    for field_name, field in model_cls.model_fields.items():
        if _should_skip_field(model_cls, field_name):
            continue

        annotation, is_optional = _unwrap_optional(field.annotation)
        required = field.is_required() and not is_optional
        default_value = None if field.is_required() else _field_default(field)
        field_path = f"{prefix}.{field_name}" if prefix else field_name
        description = field.description or ""
        values[field_name] = _prompt_value(
            ui=ui,
            annotation=annotation,
            field_path=field_path,
            description=description,
            required=required,
            default_value=default_value,
            is_optional=is_optional,
        )

    return values


def _should_skip_field(model_cls: type[BaseModel], field_name: str) -> bool:
    """Return whether a field should be hidden from interactive prompting."""
    if field_name in SKIPPED_TASK_FIELDS:
        return True

    return issubclass(model_cls, WorkspaceInfo) and field_name in SKIPPED_WORKSPACE_FIELDS


def _prompt_value(
    *,
    ui: TaskInputUI,
    annotation: Any,
    field_path: str,
    description: str,
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> Any:
    """Prompt for a single value based on type annotation."""
    origin = get_origin(annotation)

    if origin is Literal:
        return _prompt_literal(
            ui,
            field_path,
            description,
            get_args(annotation),
            required,
            default_value,
            is_optional,
        )

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _prompt_model(
            ui,
            annotation,
            field_path,
            description,
            required,
            default_value,
            is_optional,
        )

    if origin is list:
        item_annotation = get_args(annotation)[0] if get_args(annotation) else Any
        return _prompt_list(
            ui,
            field_path,
            description,
            item_annotation,
            required,
            default_value,
            is_optional,
        )

    if origin is dict:
        return _prompt_json(ui, field_path, description, required, default_value, is_optional)

    if annotation in {str, int, float, bool, Path}:
        return _prompt_scalar(ui, annotation, field_path, description, required, default_value, is_optional)

    return _prompt_json(ui, field_path, description, required, default_value, is_optional)


def _prompt_scalar(
    ui: TaskInputUI,
    annotation: Any,
    field_path: str,
    description: str,
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> Any:
    """Prompt for a scalar value."""
    while True:
        prompt = _format_prompt(field_path, annotation.__name__, description, required, default_value, is_optional)
        raw = ui.prompt(prompt)

        if raw == "" and not required:
            return default_value
        if raw == "" and required:
            ui.show_error("This field is required.")
            continue

        if annotation is str:
            if raw == MULTILINE_SENTINEL:
                return _read_multiline_value(ui, field_path)
            return raw

        try:
            if annotation is int:
                return int(raw)
            if annotation is float:
                return float(raw)
            if annotation is bool:
                return _parse_bool(raw)
            if annotation is Path:
                return Path(raw)
        except ValueError as exc:
            ui.show_error(f"Invalid value for {field_path}: {exc}")
            continue

        return raw


def _prompt_literal(
    ui: TaskInputUI,
    field_path: str,
    description: str,
    literal_values: tuple[Any, ...],
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> Any:
    """Prompt for a Literal field."""
    choices = ", ".join(repr(value) for value in literal_values)
    while True:
        prompt = _format_prompt(
            field_path,
            f"one of {choices}",
            description,
            required,
            default_value,
            is_optional,
        )
        raw = ui.prompt(prompt)
        if raw == "" and not required:
            return default_value
        if raw == "" and required:
            ui.show_error("This field is required.")
            continue

        for candidate in literal_values:
            if raw == str(candidate):
                return candidate

        ui.show_error(f"Invalid choice. Expected one of: {choices}")


def _prompt_model(
    ui: TaskInputUI,
    model_cls: type[BaseModel],
    field_path: str,
    description: str,
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> Any:
    """Prompt for a nested Pydantic model."""
    if is_optional and default_value is None:
        include_prompt = f"{field_path} ({model_cls.__name__})"
        if description:
            include_prompt += f" - {description}"
        include_prompt += " [y/N]: "
        include_nested = ui.prompt(include_prompt).strip().lower()
        if include_nested not in {"y", "yes"}:
            return None

    ui.show_group(field_path, model_cls.__name__, description)
    return _prompt_model_fields(model_cls, ui=ui, prefix=field_path)


def _prompt_list(
    ui: TaskInputUI,
    field_path: str,
    description: str,
    item_annotation: Any,
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> Any:
    """Prompt for a list field."""
    existing_items = default_value if isinstance(default_value, list) else []
    default_count = len(existing_items)

    while True:
        prompt = _format_prompt(
            field_path,
            "list length",
            description,
            required,
            default_count,
            is_optional,
        )
        raw = ui.prompt(prompt)

        if raw == "" and not required:
            count = default_count
        elif raw == "" and required:
            ui.show_error("This field is required.")
            continue
        else:
            try:
                count = int(raw)
            except ValueError:
                ui.show_error("Please enter an integer list length.")
                continue

        if count < 0:
            ui.show_error("List length cannot be negative.")
            continue

        break

    if count == 0:
        if is_optional and default_value is None:
            return None
        return []

    items = []
    for index in range(count):
        item_default = existing_items[index] if index < len(existing_items) else None
        item_value = _prompt_value(
            ui=ui,
            annotation=item_annotation,
            field_path=f"{field_path}[{index}]",
            description="",
            required=True,
            default_value=item_default,
            is_optional=False,
        )
        items.append(item_value)

    return items


def _prompt_json(
    ui: TaskInputUI,
    field_path: str,
    description: str,
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> Any:
    """Prompt for a JSON-encoded complex value."""
    default_repr = _json_repr(default_value)
    while True:
        prompt = _format_prompt(field_path, "JSON", description, required, default_repr, is_optional)
        raw = ui.prompt(prompt)
        if raw == "" and not required:
            return default_value
        if raw == "" and required:
            ui.show_error("This field is required.")
            continue

        try:
            return json.loads(raw)
        except Exception as exc:
            ui.show_error(f"Invalid JSON for {field_path}: {exc}")


def _read_multiline_value(ui: TaskInputUI, field_path: str) -> str:
    """Read a multi-line string until EOF marker."""
    ui.show_multiline_intro(field_path)
    lines: list[str] = []
    while True:
        line = ui.prompt("")
        if line == MULTILINE_END_MARKER:
            break
        lines.append(line)
    return "\n".join(lines)


def _parse_bool(raw: str) -> bool:
    """Parse a boolean value from user input."""
    normalized = raw.strip().lower()
    if normalized in {"true", "t", "yes", "y", "1"}:
        return True
    if normalized in {"false", "f", "no", "n", "0"}:
        return False
    raise ValueError("expected one of true/false, yes/no, or 1/0")


def _format_prompt(
    field_path: str,
    type_label: str,
    description: str,
    required: bool,
    default_value: Any,
    is_optional: bool,
) -> str:
    """Format a prompt string with metadata."""
    details = [type_label]
    if required:
        details.append("required")
    elif is_optional:
        details.append("optional")

    prompt = f"{field_path} ({', '.join(details)})"
    if description:
        prompt += f" - {description}"
    if default_value not in (None, "", [], {}):
        prompt += f" [default: {default_value}]"
    prompt += ": "
    return prompt


def _json_repr(value: Any) -> Any:
    """Format a default complex value for display."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value
