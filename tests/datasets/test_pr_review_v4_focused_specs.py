"""Focused-agent specs and the gold-free rule that decides where each one runs.

Scheduling is where a focused arm could quietly become a leak: activating an agent because
gold says an issue of that kind occurred there would hand the system the answer. Sites come
from the modification inventory, which is built from change graphs alone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.datasets.pr_review_v4.focused_specs import (
    DECLARATION_KINDS,
    FocusedAgentSpec,
    default_specs,
    schedule_focused,
    schedule_report,
)
from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.schema import ModificationRecord, ReviewWorkUnit

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
INVENTORY = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v3-medium/derived/"
    "modification_inventory.jsonl"
)


@pytest.fixture(scope="module")
def scheduled():
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    modifications = load_jsonl(INVENTORY, ModificationRecord)
    return schedule_focused(default_specs(), modifications, units)


def _spec(spec_id):
    return next(item for item in default_specs() if item.spec_id == spec_id)


def test_the_reserved_method_ids_are_not_reused():
    """`investigations.SMOKE_EXPECTATIONS` records these as `planned_method_gap`; a method
    with either ID and no scheduled InvestigationTask flips the smoke gate to fail."""

    ids = {item.spec_id for item in default_specs()}
    assert not ids & {"proof_compression.v1", "structural_rewrite.v1"}


def test_specs_carryprompt_hashes_not_prompt_text():
    """`contracts.assert_gold_free` sweeps a serialized plan for words the focused prompts
    are full of — "would a maintainer say", "maintainers routinely ask"."""

    for spec in default_specs():
        serialized = str(spec.identity())
        assert len(spec.prompt_sha256) == 64
        assert "maintainer" not in serialized.lower()


def test_golf_and_idiom_run_on_modified_proofs_only():
    """v2's measured 14% was golf on proofs the PR *changed*. A newly added declaration
    reports every component as `added`, so scheduling both lifecycles would put all four
    specs on every added theorem."""

    for spec_id in ("proof_golf", "proof_idiom"):
        spec = _spec(spec_id)
        assert spec.lifecycles == frozenset({"modified"})
        assert spec.component == "proof"


def test_duplication_and_generality_run_on_added_declarations_only():
    """They ask whether something *new* should exist in this form."""

    for spec_id in ("duplication", "generality"):
        spec = _spec(spec_id)
        assert spec.lifecycles == frozenset({"added"})
        assert spec.subject_kinds == DECLARATION_KINDS


def test_golf_and_idiom_are_distinguishable_despite_sharing_an_issue_kind():
    """Both declare `proof_simplification`; only `spec_id` separates their warrants."""

    golf, idiom = _spec("proof_golf"), _spec("proof_idiom")
    assert golf.issue_kind == idiom.issue_kind == "proof_simplification"
    assert golf.concern_family == idiom.concern_family
    assert golf.prompt_sha256 != idiom.prompt_sha256
    assert golf.source_sha256 != idiom.source_sha256


def test_a_work_unit_with_no_applicable_site_is_not_scheduled(scheduled):
    """The point of enumerating: 225 work units, far fewer invocations."""

    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    scheduled_units = {item.work_unit_id for item in scheduled}
    assert len(scheduled_units) < len(units)


def test_the_invocation_id_is_the_composite_key(scheduled):
    """`prompt_sha256_by_work_unit` maps one hash per work unit, and ingestion permits one
    successful response per unit — so four specs on one unit need distinct identities."""

    assert all("#" in item.invocation_id for item in scheduled)
    assert len({item.invocation_id for item in scheduled}) == len(scheduled)
    collisions = [item for item in scheduled
                  if item.invocation_id != f"{item.work_unit_id}#{item.spec_id}"]
    assert not collisions


def test_scheduling_is_deterministic(scheduled):
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    modifications = load_jsonl(INVENTORY, ModificationRecord)
    again = schedule_focused(default_specs(), modifications, units)
    assert [item.invocation_id for item in again] == [
        item.invocation_id for item in scheduled
    ]
    assert [item.source_sha256 for item in again] == [
        item.source_sha256 for item in scheduled
    ]


def test_scheduling_reads_nothing_from_gold():
    """Structural, not prose: the module may *discuss* gold, it may not *read* it.

    Checked by what it imports and what paths it names, so the docstring can explain why
    scheduling must stay gold-free without the test failing on the explanation.
    """

    import ast
    import inspect

    from src.datasets.pr_review_v4 import focused_specs

    tree = ast.parse(inspect.getsource(focused_specs))
    imported = {
        alias.name for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) for alias in node.names
    }
    gold_types = {"JudgmentNode", "InterventionView", "JudgmentObligation", "SemanticMatch"}
    assert not imported & gold_types, f"scheduler imports gold types: {imported & gold_types}"

    paths = [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and node.value.endswith(".jsonl")
    ]
    assert paths, "expected the scheduler to name its inputs"
    assert not [item for item in paths if "gold" in item], f"reads a gold artifact: {paths}"


def test_the_report_names_control_invocations_rather_than_hiding_them(scheduled):
    """The arm is silent on most controls by *enumeration*, not judgment, so its control
    rate is not comparable with the holistic arm's without saying so."""

    report = schedule_report(scheduled, control_pr_numbers=[33304, 33315, 33438])
    assert report["control_invocations"] == {33304: 0, 33315: 0, 33438: 2}


def test_the_measured_medium_schedule(scheduled):
    """Pinned so a rule change that silently doubles the bill is visible in the diff."""

    report = schedule_report(scheduled)
    assert report["invocations"] == 258
    assert report["invocations_by_spec"] == {
        "duplication": 101, "generality": 101, "proof_golf": 28, "proof_idiom": 28
    }
    # One PR is 43% of the arm and can never publish more than the per-PR limit of 20.
    assert report["invocations_by_pr"][33149] == 112
