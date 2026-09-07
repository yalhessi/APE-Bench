"""One declaration per arm, and everything else derives from it.

Four facts about an arm -- can a compile settle its claims, which retrieval tools it gets,
which concerns it may declare, may it submit a coordinated patch -- used to be four
dictionaries keyed by arm id. Two lived in `src/mathlib_review/agenda/arms.py` and two in
`src/ape/tasks/.../pr_review_v5/arm.py`, on opposite sides of the package boundary, with
nothing checking that an arm appeared in the right subset of them.

That is not a hypothetical failure mode. `migration_consistency` sat in `PATCH_SET_ARMS`
while never being registered as an arm at all, and the retrieval grant was per-arm in
`arms.py` for weeks while `schema.py` still documented it as uniform for every arm.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.agenda import registry as arm_registry
from src.mathlib_review.agenda.arms import (
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

    from src.mathlib_review.schema.review import CONTEXT_TOOLS

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
    from src.mathlib_review.agenda.arms import v5_specs

    assert ([spec.spec_id for spec in v5_specs()]
            == [item.arm_id for item in arm_registry.ARM_DEFINITIONS])


def test_an_arms_question_is_written_once():
    """Both copies were called `rationale` and one was documented as being "for the reader",
    which is how they were allowed to differ. The fuller text -- `docs` carries a measurement
    in it -- is the one that survives, and it is the one the agenda ships."""

    from src.mathlib_review.agenda.arms import v5_specs

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
    from src.mathlib_review.agenda.arms import v5_specs

    actual = {spec.spec_id: spec.source_sha256[:12] for spec in v5_specs()}
    assert actual == EXPECTED_SPEC_IDENTITY


def test_the_arms_that_may_look_beyond_declarations_still_can():
    """`docs` reaches module docs; `style` reaches module docs and placement. Every other arm
    sees declarations only. This is the field that vanished."""

    from src.mathlib_review.agenda.arms import v5_specs

    kinds = {spec.spec_id: spec.subject_kinds for spec in v5_specs()}
    assert "module_doc" in kinds["docs"]
    assert {"module_doc", "namespace_or_section", "command", "import"} <= kinds["style"]
    assert "module_doc" not in kinds["naming"]


def test_nothing_but_the_registry_names_an_arm_when_building_specs():
    """Everything `v5_specs` produces is read off the registry entry, so an arm's id, concern,
    issue kind, subject kinds and rationale appear in exactly one place."""

    import inspect

    from src.mathlib_review.agenda import arms

    source = inspect.getsource(arms.v5_specs)
    assert "for definition in ARM_DEFINITIONS" in source
    for definition in arm_registry.ARM_DEFINITIONS:
        assert f'"{definition.arm_id}"' not in source, (
            f"v5_specs names {definition.arm_id}; it should only iterate the registry")


def test_adding_an_arm_takes_two_edits_and_the_second_one_says_so():
    """Measured by adding an arm through the registry alone and seeing what refused.

    Two edits, and the second is irreducible: an arm is a declaration plus the one question it
    asks, and a prompt is real content rather than boilerplate a registry could generate. What
    was not irreducible is being told about it -- this surfaced as a bare
    `KeyError: 'import_hygiene'` from a dict lookup two frames down, which is exactly the
    "forgot a lesson, told nothing useful" failure this consolidation started from.
    """

    from dataclasses import replace

    from src.mathlib_review.agenda.arms import _new_spec

    undeclared = replace(arm_registry.ARM_DEFINITIONS[0], arm_id="import_hygiene")
    with pytest.raises(KeyError) as excinfo:
        _new_spec(undeclared)
    message = str(excinfo.value)
    assert "import_hygiene" in message
    assert "FOCUSED_PROMPTS" in message
    assert "focused_prompts.py" in message


# --- what the sealed identities cover ------------------------------------------------------
#
# `tools_sha256` hashes the tool list the *prompt* declares, which is not the list the arm
# runs with -- workspace tools come from `task_config.enabled_tools`, retrieval tools from the
# registry, and for `naming`/`docs`/`style` the prompt list holds four against a runtime six
# plus grants. That reads like a provenance hole and is not one. These pin why, so the next
# reader does not re-derive it and then "fix" it by moving ten sealed identities.


def test_changing_the_workspace_tools_moves_the_scaffold_hash():
    """`load_run` pops `task_config` into `scaffold.task_config_overrides`, which is inside
    the scaffold dump that `scaffold_config_sha256` hashes."""

    from pathlib import Path

    from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes
    from src.mathlib_review.review.runner import load_run

    _dataset, scaffold, overrides = load_run(Path("configs/pr_review_v5_specialist4.yaml"))
    assert overrides["enabled_tools"]

    def digest(sc):
        return sha256_bytes(canonical_json_bytes(sc.model_dump(mode="json")))

    before = digest(scaffold)
    scaffold.task_config_overrides = {"enabled_tools": ["file_read"]}
    assert digest(scaffold) != before


def test_changing_an_arms_retrieval_grant_moves_the_agenda():
    """`ReviewArm.context_tools` carries the grant and `ReviewArm`s are in the agenda, so the
    grant is inside `agenda_sha256`. This is the capability the `family_design` measurement
    showed matters most -- 50 of 63 retrieval calls spent on the wrong tool -- so it being
    sealed is the thing worth checking."""

    from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes
    from src.mathlib_review.agenda.arms import default_arms
    from src.mathlib_review.schema.review import ReviewAgenda

    arm = next(a for a in default_arms("candidate-prompt/12") if a.arm_id == "family_design")
    payload = arm.model_dump(mode="json")
    assert payload["context_tools"]
    altered = {**payload, "context_tools": ["declaration_search"]}
    assert (sha256_bytes(canonical_json_bytes(payload))
            != sha256_bytes(canonical_json_bytes(altered)))
    assert "arms" in ReviewAgenda.model_fields


def test_a_new_arm_needs_nothing_beyond_those_two_edits(monkeypatch):
    """The end-to-end form of the guarantee, and the answer to "we end up touching way too
    many things".

    Adding `family_design` once meant editing thirteen source files across six packages, four
    of them dictionaries keyed by arm id that had to agree by hand. A registry entry plus a
    prompt is now the whole of it: the spec, the `ReviewArm`, the tool grant, the bench roster
    and the concern vocabulary all fall out.
    """

    from dataclasses import replace

    from ape.tasks.lean_tasks.formal_math.pr_shared import focused_prompts
    from src.mathlib_review.agenda import arms
    from src.mathlib_review.analysis import bench_cli

    prompts = dict(focused_prompts.FOCUSED_PROMPTS)
    prompts["import_hygiene"] = (
        ["file_read", "content_search"],
        "You are a Mathlib maintainer running ONE focused check: imports.",
        "## PR #{pr_number} — {title}\n\n{description}\n\n{diff}\n",
    )
    monkeypatch.setattr(focused_prompts, "FOCUSED_PROMPTS", prompts)

    declared = arm_registry._arm(
        "import_hygiene", "scope", "scope_violation",
        "Does this file import more than it uses, or reach across a layer boundary?",
        context_tools=("declaration_search",))
    roster = arm_registry.ARM_DEFINITIONS + (declared,)
    monkeypatch.setattr(arm_registry, "ARM_DEFINITIONS", roster)
    monkeypatch.setattr(arms, "ARM_DEFINITIONS", roster)
    monkeypatch.setattr(bench_cli, "ARM_DEFINITIONS", roster)

    specs = {spec.spec_id: spec for spec in arms.v5_specs()}
    assert "import_hygiene" in specs
    assert specs["import_hygiene"].concern_family == "scope"

    built = {arm.arm_id: arm for arm in arms.default_arms("candidate-prompt/12")}
    assert built["import_hygiene"].context_tools == [
        "declaration_search", "lean_verify_edit"]

    assert "import_hygiene" in bench_cli.roster()
    assert arm_registry.expected_concerns()["import_hygiene"] == frozenset({"scope"})
    # Not checkable unless it says so: a compile cannot settle an import-hygiene claim.
    assert "import_hygiene" not in arm_registry.checkable_arms()
