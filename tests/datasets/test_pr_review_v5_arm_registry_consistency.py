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


# --- one declaration per arm -----------------------------------------------------------------
#
# `v5_specs()` used to re-declare all ten arms next to a registry that already declared all
# ten: id, concern family, issue kind, subject kinds, and a rationale each. Adding an arm meant
# editing both, and the two rationales had drifted apart in every single one of the ten.


def test_the_spec_set_is_exactly_the_registry():
    from src.datasets.pr_review_v5.arms import v5_specs

    assert ([spec.spec_id for spec in v5_specs()]
            == [item.arm_id for item in arm_registry.ARM_DEFINITIONS])


def test_an_arms_question_is_written_once():
    """Both copies were called `rationale` and one was documented as being "for the reader",
    which is how they were allowed to differ. The fuller text -- `docs` carries a measurement
    in it -- is the one that survives, and it is the one the agenda ships."""

    from src.datasets.pr_review_v5.arms import v5_specs

    by_id = {item.arm_id: item for item in arm_registry.ARM_DEFINITIONS}
    for spec in v5_specs():
        assert spec.rationale == by_id[spec.spec_id].rationale, spec.spec_id


#: What each spec hashes to. Pinned because folding the two declarations together silently
#: dropped `docs`'s `module_doc` and all four of `style`'s extra kinds -- the exact capability
#: two gold obligations need (PR 33305's over-long module-doc line, PR 33362's `namespace
#: Complex` placement) -- and the whole suite stayed green. A spec's identity is what the
#: agenda seals, so it is worth stating outright.
EXPECTED_SPEC_IDENTITY = {
    "api_reuse": "cab1c1dd3561", "correctness": "75bca1cae954", "docs": "0272b478d6e9",
    "duplication": "dcef56db2ee5", "family_design": "860fd12098a9",
    "generality": "ef5c1b06333a", "naming": "8dfd2c87af4d", "proof_golf": "854c179f8da7",
    "proof_idiom": "d0d4b417257d", "style": "d82d80097e5a",
}


def test_spec_identities_are_unchanged():
    from src.datasets.pr_review_v5.arms import v5_specs

    actual = {spec.spec_id: spec.source_sha256[:12] for spec in v5_specs()}
    assert actual == EXPECTED_SPEC_IDENTITY


def test_the_arms_that_may_look_beyond_declarations_still_can():
    """`docs` reaches module docs; `style` reaches module docs and placement. Every other arm
    sees declarations only. This is the field that vanished."""

    from src.datasets.pr_review_v5.arms import v5_specs

    kinds = {spec.spec_id: spec.subject_kinds for spec in v5_specs()}
    assert "module_doc" in kinds["docs"]
    assert {"module_doc", "namespace_or_section", "command", "import"} <= kinds["style"]
    assert "module_doc" not in kinds["naming"]


def test_adding_an_arm_is_one_edit():
    """The measure of whether this stayed fixed: everything `v5_specs` produces is read off
    the registry entry, so a new `_arm(...)` line is a whole new arm."""

    import inspect

    from src.datasets.pr_review_v5 import arms

    source = inspect.getsource(arms.v5_specs)
    assert "for definition in ARM_DEFINITIONS" in source
    # No arm may be named in the function that projects them.
    for definition in arm_registry.ARM_DEFINITIONS:
        assert f'"{definition.arm_id}"' not in source, (
            f"v5_specs names {definition.arm_id}; it should only iterate the registry")
