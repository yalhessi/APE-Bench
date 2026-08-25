"""Helpers for shared-input task variants and sidecar variant manifests."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field

from ape.utils import deep_merge


class TaskVariantDefinition(BaseModel):
    """Describe how to expand one canonical task record into a concrete variant."""

    model_config = ConfigDict(extra="forbid")

    variant_id: str = Field(..., description="Stable identifier for the variant within a manifest")
    runtime_task_type: str = Field(..., description="Concrete task type instantiated at runtime")
    accepted_source_task_types: list[str] = Field(
        default_factory=list,
        description="Allowed source task types for this variant; empty means any source task type is accepted",
    )
    task_id_suffix: str = Field(
        default="",
        description="Suffix appended to the source task_id when materializing this variant",
    )
    metadata_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata merged into the expanded task record",
    )
    task_config_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-record task configuration overrides merged before task construction",
    )

    def accepts_source_task_type(self, task_type: str) -> bool:
        """Return whether this variant can expand a record with the given task type."""
        accepted = [value.strip() for value in self.accepted_source_task_types if str(value).strip()]
        return not accepted or task_type in accepted


class TaskVariantManifest(BaseModel):
    """Sidecar manifest pointing to one canonical task file plus one or more variants."""

    model_config = ConfigDict(extra="forbid")

    manifest_type: Literal["task_variant_manifest"] = "task_variant_manifest"
    version: Literal[1] = 1
    base_task_file: str = Field(..., description="Relative or absolute path to the canonical task file")
    variants: list[TaskVariantDefinition] = Field(
        default_factory=list,
        description="Concrete runtime variants expanded from the canonical task file",
    )


def build_default_pr_review_variants(
    *,
    skill_bundle: str = "mathlib-pr-review",
) -> tuple[TaskVariantDefinition, TaskVariantDefinition, TaskVariantDefinition]:
    """Return the standard PR review variants."""
    source_task_type = "lean_pr_review"
    return (
        TaskVariantDefinition(
            variant_id="baseline",
            runtime_task_type=source_task_type,
            accepted_source_task_types=[source_task_type],
            task_id_suffix="__baseline",
            metadata_updates={
                "paired_variant": "baseline",
                "skill_bundle": skill_bundle,
            },
        ),
        TaskVariantDefinition(
            variant_id="with_skills",
            runtime_task_type="skilled_pr_review",
            accepted_source_task_types=[source_task_type],
            task_id_suffix="__with_skills",
            metadata_updates={
                "paired_variant": "with_skills",
                "skill_bundle": skill_bundle,
            },
        ),
        TaskVariantDefinition(
            variant_id="with_skill_policy",
            runtime_task_type="skilled_policy_pr_review",
            accepted_source_task_types=[source_task_type],
            task_id_suffix="__with_skill_policy",
            metadata_updates={
                "paired_variant": "with_skill_policy",
                "skill_bundle": skill_bundle,
            },
        ),
    )


def build_default_pr_split_variants(
    *,
    skill_bundle: str = "mathlib-pr-split",
) -> tuple[TaskVariantDefinition, TaskVariantDefinition, TaskVariantDefinition]:
    """Return the standard PR split variants."""
    source_task_type = "lean_pr_split"
    return (
        TaskVariantDefinition(
            variant_id="baseline",
            runtime_task_type=source_task_type,
            accepted_source_task_types=[source_task_type],
            task_id_suffix="__baseline",
            metadata_updates={
                "paired_variant": "baseline",
                "skill_bundle": skill_bundle,
            },
        ),
        TaskVariantDefinition(
            variant_id="with_skills",
            runtime_task_type="skilled_pr_split",
            accepted_source_task_types=[source_task_type],
            task_id_suffix="__with_skills",
            metadata_updates={
                "paired_variant": "with_skills",
                "skill_bundle": skill_bundle,
            },
        ),
        TaskVariantDefinition(
            variant_id="with_skill_policy",
            runtime_task_type="skilled_policy_pr_split",
            accepted_source_task_types=[source_task_type],
            task_id_suffix="__with_skill_policy",
            metadata_updates={
                "paired_variant": "with_skill_policy",
                "skill_bundle": skill_bundle,
            },
        ),
    )


def get_registered_task_variant_definition(
    requested_task_type: str,
    *,
    source_task_type: str,
) -> TaskVariantDefinition | None:
    """Return a built-in compatibility variant for registered-task CLI selection."""
    normalized_requested = str(requested_task_type or "").strip()
    normalized_source = str(source_task_type or "").strip()
    if not normalized_requested or not normalized_source:
        return None

    if normalized_requested == "skilled_pr_review" and normalized_source == "lean_pr_review":
        return build_default_pr_review_variants()[1]
    if normalized_requested == "skilled_policy_pr_review" and normalized_source == "lean_pr_review":
        return build_default_pr_review_variants()[2]
    if normalized_requested == "skilled_pr_split" and normalized_source == "lean_pr_split":
        return build_default_pr_split_variants()[1]
    if normalized_requested == "skilled_policy_pr_split" and normalized_source == "lean_pr_split":
        return build_default_pr_split_variants()[2]
    return None


def default_variant_manifest_output_path(base_task_file: Path) -> Path:
    """Return the default sidecar manifest path for a canonical task file."""
    return base_task_file.with_name(f"{base_task_file.stem}_variants.json")


def create_task_variant_manifest(
    *,
    base_task_file: Path,
    manifest_output: Path,
    variants: Sequence[TaskVariantDefinition],
) -> Path:
    """Write a task-variant manifest next to a canonical task file."""
    relative_base_task_file = os.path.relpath(base_task_file, manifest_output.parent)
    manifest = TaskVariantManifest(
        base_task_file=relative_base_task_file,
        variants=list(variants),
    )
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_output


def is_task_variant_manifest_payload(payload: Any) -> bool:
    """Return True when a parsed JSON payload is a task-variant manifest."""
    return isinstance(payload, dict) and payload.get("manifest_type") == "task_variant_manifest"


def apply_task_variant(
    record: dict[str, Any],
    *,
    variant: TaskVariantDefinition,
    source_file: str | None = None,
) -> dict[str, Any]:
    """Expand one canonical task record into a concrete runtime variant."""
    updated = copy.deepcopy(record)

    source_task_type = str(updated.get("task_type") or "").strip()
    if not source_task_type:
        raise ValueError("Task variant expansion requires the source record to define task_type")
    if not variant.accepts_source_task_type(source_task_type):
        supported = ", ".join(variant.accepted_source_task_types) or "any task type"
        raise ValueError(
            f"Variant `{variant.variant_id}` cannot expand source task_type `{source_task_type}`. "
            f"Supported source task types: {supported}."
        )

    source_task_id = str(updated.get("task_id") or "task")
    source_global_index = str(updated.get("global_index") or "").strip()

    metadata = dict(updated.get("metadata") or {})
    variant_metadata: dict[str, Any] = {
        "task_variant_id": variant.variant_id,
        "variant_base_task_id": source_task_id,
        "variant_base_task_type": source_task_type,
        "variant_runtime_task_type": variant.runtime_task_type,
    }
    if source_global_index:
        variant_metadata["variant_base_global_index"] = source_global_index
    if source_file:
        variant_metadata["variant_source_file"] = source_file

    metadata = deep_merge(metadata, variant_metadata)
    metadata = deep_merge(metadata, variant.metadata_updates)
    updated["metadata"] = metadata

    if variant.task_id_suffix:
        updated["task_id"] = f"{source_task_id}{variant.task_id_suffix}"
    updated["task_type"] = variant.runtime_task_type
    updated.pop("global_index", None)

    merged_task_config_overrides: dict[str, Any] = {}
    existing_task_config_overrides = updated.get("task_config_overrides")
    if isinstance(existing_task_config_overrides, dict):
        merged_task_config_overrides = deep_merge(merged_task_config_overrides, existing_task_config_overrides)
    merged_task_config_overrides = deep_merge(merged_task_config_overrides, variant.task_config_overrides)
    if merged_task_config_overrides:
        updated["task_config_overrides"] = merged_task_config_overrides

    return updated


def expand_task_variant_records(
    records: Sequence[dict[str, Any]],
    *,
    variants: Sequence[TaskVariantDefinition],
    source_file: str | None = None,
) -> list[dict[str, Any]]:
    """Expand canonical task records into one record per variant."""
    expanded_records: list[dict[str, Any]] = []
    for record in records:
        for variant in variants:
            expanded_records.append(apply_task_variant(record, variant=variant, source_file=source_file))
    return expanded_records


def load_task_records_from_path(file_path: Path) -> list[dict[str, Any]]:
    """Load task records from JSONL, plain JSON, or a task-variant manifest."""
    if not file_path.exists():
        raise FileNotFoundError(f"Task file not found: {file_path}")

    if file_path.suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        with file_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                record = json.loads(stripped)
                if not isinstance(record, dict):
                    raise TypeError(
                        f"Line {line_number} in {file_path} must be a JSON object, got {type(record).__name__}"
                    )
                records.append(record)
        return records

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if is_task_variant_manifest_payload(payload):
        manifest = TaskVariantManifest.model_validate(payload)
        base_task_file = Path(manifest.base_task_file)
        if not base_task_file.is_absolute():
            base_task_file = (file_path.parent / base_task_file).resolve()
        base_records = load_task_records_from_path(base_task_file)
        return expand_task_variant_records(
            base_records,
            variants=manifest.variants,
            source_file=str(base_task_file),
        )

    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return list(payload)
    raise TypeError(f"{file_path} must contain a JSON object, JSON object list, or task variant manifest")


def resolve_task_record_for_registered_task(
    raw_task_data: dict[str, Any],
    *,
    requested_task_type: str,
) -> dict[str, Any]:
    """Align a raw task record with the registered task selected on the CLI."""
    normalized_requested_task_type = str(requested_task_type or "").strip()
    if not normalized_requested_task_type:
        raise ValueError("requested_task_type must be non-empty")

    existing_task_type = str(raw_task_data.get("task_type") or "").strip()
    if not existing_task_type or existing_task_type == normalized_requested_task_type:
        updated = copy.deepcopy(raw_task_data)
        updated["task_type"] = normalized_requested_task_type
        return updated

    variant = get_registered_task_variant_definition(
        normalized_requested_task_type,
        source_task_type=existing_task_type,
    )
    if variant is None:
        raise ValueError(
            f"Selected task data has task_type={existing_task_type!r}, which does not match "
            f"the requested task {normalized_requested_task_type!r}"
        )
    return apply_task_variant(raw_task_data, variant=variant)
