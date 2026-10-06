"""A new field on a review task's data is a `knob()`, and an old one never becomes one.

On 2026-10-06 the review task-data classes held the 63 field names below, beyond the framework
base. Each is part of the `global_index` of every task already run, and the hygiene reps, the
design reps and every partial run resume on those identities. So:

- a field not in this list must be a `knob()`, or adding it forks every task of its type, which is
  how `forbid_abstention` and `target_verdicts` each moved every review identity when they were
  added;
- a field in this list must not become a `knob()`, which would move the identity of every task
  where it is None.

The rule and its reason are in `.claude/rules/mathlib-review.md` ("What moves a hash").
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import ape.tasks.lean_tasks.formal_math.review as review
from ape.tasks.base import IDENTITY_WHEN_SET, BaseTaskData

FIELDS_BEFORE_KNOBS = frozenset({
    "arm_id", "arm_pool_path", "candidate_change_ids", "candidate_claim", "candidate_code",
    "candidate_family", "candidate_id", "candidate_source_sha256", "census", "change_ids",
    "change_ids_by_opportunity", "changed_files", "context_profile", "context_tools",
    "declarations", "diff", "entity_ids_by_change", "episode_id", "evidence_ids_by_opportunity",
    "execution_index_path", "forbid_abstention", "gold_action", "gold_claim", "gold_concerns",
    "invocation_id", "journal_path", "judge_version", "maintainer_comment", "obligation_id",
    "obligation_source_sha256", "opportunity_ids", "overlap_change_ids", "pairing_tier",
    "paths_by_change", "pr_description", "pr_number", "pr_title", "primary_subject",
    "primary_subjects_by_change", "proposals", "proposed_edit", "reference_workspaces",
    "rendered_prompt_sha256", "rendered_system_prompt", "rendered_user_prompt",
    "requested_change", "resolution_criteria", "retrieval_cutoff", "reviewed_path",
    "routing_mode", "sibling_claims", "snapshot_base_sha", "snapshot_head_sha", "spec_id",
    "stage", "submission_verification_policy", "suggested_fix", "target_code",
    "target_verdicts", "target_workspace", "trace_path",
    "verification_required_opportunity_ids", "work_unit_id",
})


def _review_data_classes():
    for info in pkgutil.iter_modules(review.__path__):
        module = importlib.import_module(f"{review.__name__}.{info.name}")
        for obj in vars(module).values():
            if (inspect.isclass(obj) and issubclass(obj, BaseTaskData)
                    and obj.__module__ == module.__name__):
                yield obj


def _is_knob(info) -> bool:
    return isinstance(info.json_schema_extra, dict) and bool(info.json_schema_extra.get(IDENTITY_WHEN_SET))


def test_the_review_data_classes_are_found():
    """A guard over an empty set passes; this one must see the classes it guards."""
    names = {cls.__name__ for cls in _review_data_classes()}
    assert {"SoloReviewData", "ReviewArmData", "ReviewLeadData", "StructuredReviewData"} <= names


def test_a_new_review_task_data_field_is_a_knob():
    base = set(BaseTaskData.model_fields)
    offending = sorted(
        f"{cls.__name__}.{name}"
        for cls in _review_data_classes()
        for name, info in cls.model_fields.items()
        if name not in base and name not in FIELDS_BEFORE_KNOBS and not _is_knob(info))
    assert not offending, (
        "a new field on review task data moves the global_index of every task of its type, so "
        "every cache and resume misses; declare it with `knob()` from ape.tasks.base:\n  "
        + "\n  ".join(offending))


def test_no_field_that_was_already_hashed_becomes_a_knob():
    converted = sorted(
        f"{cls.__name__}.{name}"
        for cls in _review_data_classes()
        for name, info in cls.model_fields.items()
        if name in FIELDS_BEFORE_KNOBS and _is_knob(info))
    assert not converted, (
        "these fields were hashed into every task's identity; making them knobs moves the "
        "identity of every task where they are None:\n  " + "\n  ".join(converted))
