"""One declaration per arm, and everything else derives from it.

Four facts about an arm -- can a compile settle its claims, which retrieval tools it gets,
which concerns it may declare, may it submit a coordinated patch -- used to be four
dictionaries keyed by arm id. Two lived in `src/datasets/pr_review_v5/arms.py` and two in
`src/ape/tasks/.../pr_review_v5/arm.py`, on opposite sides of the package boundary, with
nothing checking that an arm appeared in the right subset of them.

That is not a hypothetical failure mode. `migration_consistency` sat in `PATCH_SET_ARMS`
while never being registered as an arm at all, and the retrieval grant was per-arm in
`arms.py` for weeks while `schema.py` still documented it as uniform for every arm.
"""

from __future__ import annotations

import pytest

from src.datasets.pr_review_v5 import arm_registry
from src.datasets.pr_review_v5.arms import (
    CHECKABLE_ARMS, default_arms, resolve_context_tools, v5_specs,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v5.arm import (
    EXPECTED_CONCERN_BY_ARM, LeanPRReviewV5ArmTask,
)


def test_every_registered_arm_has_a_scheduling_spec():
    """A declaration with no spec is a capability granted to nothing, readable as coverage
    that is not there."""

    spec_ids = {spec.spec_id for spec in v5_specs()}
    assert set(arm_registry.arm_ids()) == spec_ids


def test_every_spec_agrees_with_its_declaration_on_concern_and_issue_kind():
    """The concern family and issue kind decide which verifier can warrant the arm, so a
    disagreement here means findings dropped for lacking a warrant their concern can never
    produce."""

    for spec in v5_specs():
        definition = arm_registry.BY_ID[spec.spec_id]
        assert spec.concern_family == definition.concern_family, spec.spec_id
        assert spec.issue_kind == definition.issue_kind, spec.spec_id


def test_checkable_arms_derives_from_the_registry():
    assert CHECKABLE_ARMS == arm_registry.checkable_arms()


def test_patch_set_arms_derives_from_the_registry():
    assert LeanPRReviewV5ArmTask.PATCH_SET_ARMS == arm_registry.patch_set_arms()


def test_expected_concerns_derives_from_the_registry():
    derived = {k: set(v) for k, v in arm_registry.expected_concerns().items()}
    assert EXPECTED_CONCERN_BY_ARM == derived


def test_an_arm_may_always_declare_its_own_concern_family():
    """Otherwise the arm's own findings are rejected at its own gate."""

    for definition in arm_registry.ARM_DEFINITIONS:
        assert definition.concern_family in definition.expected_concerns, definition.arm_id


def test_every_arm_keeps_lean_verify_edit():
    """The one tool no arm may lose: 87 of its 100 calls on smoke4 carried a real edit."""

    for definition in arm_registry.ARM_DEFINITIONS:
        assert "lean_verify_edit" in definition.granted_tools(), definition.arm_id


def test_a_patch_set_arm_is_one_whose_scope_is_a_group():
    """Only an arm reviewing a set of declarations has anything to coordinate. Granting it
    broadly turns a bounded capability into a licence to rewrite whatever the arm was shown."""

    assert arm_registry.patch_set_arms() == {"family_design"}


def test_family_design_has_no_identifier_lookup():
    """The measured intervention: it spent 50 of 63 retrieval calls on `declaration_search`,
    which cannot answer a question about a group's shape, and returned nothing from eleven
    invocations."""

    assert "declaration_search" not in arm_registry.BY_ID["family_design"].context_tools


def test_the_convention_arms_keep_the_review_corpus():
    """Naming, docs and style ask questions the code corpus answers wrongly -- `coe_`
    outnumbers the requested form 4,707 to 50."""

    for arm_id in ("naming", "docs", "style"):
        assert "precedent_search" in arm_registry.BY_ID[arm_id].context_tools, arm_id


def test_the_generalist_is_not_in_the_registry_and_keeps_every_tool():
    """It has no concern filter, which is what makes it the control, and narrowing it would
    move both sides of the comparison at once."""

    from src.datasets.pr_review_v5.schema import CONTEXT_TOOLS

    assert "generalist" not in arm_registry.BY_ID
    generalist = next(a for a in default_arms("v4-renderer/1") if a.arm_id == "generalist")
    assert sorted(resolve_context_tools(generalist)) == sorted(CONTEXT_TOOLS)


@pytest.mark.parametrize("definition", arm_registry.ARM_DEFINITIONS,
                         ids=lambda d: d.arm_id)
def test_each_declaration_says_what_the_arm_is_for(definition):
    """A registry row with no rationale is a name, not a contract."""

    assert definition.rationale.strip()
    assert definition.expected_concerns
